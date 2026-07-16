#include <SoftwareSerial.h>
#include <avr/wdt.h>
#include <EEPROM.h>

#define RS485_TX      2
#define RS485_RX      3
#define RS485_DE      4
#define POT_PIN       A0
#define NOODSTOP_PIN  5   // normaal gesloten knop tussen pin en GND
#define DODE_MAN_PIN  6   // normaal open knop tussen pin en GND

#define EEPROM_FOUTEN 0   // EEPROM adres voor foutenteller

SoftwareSerial rs485(RS485_RX, RS485_TX);

int16_t huidigSnelheid = 0;
uint8_t foutTeller = 0;

uint8_t crc8(uint8_t *data, uint8_t len) {
  uint8_t crc = 0;
  for (uint8_t i = 0; i < len; i++) {
    uint8_t b = data[i];
    for (uint8_t j = 0; j < 8; j++) {
      uint8_t mix = (crc ^ b) & 0x01;
      crc >>= 1;
      if (mix) crc ^= 0x8C;
      b >>= 1;
    }
  }
  return crc;
}

void schrijfByte(uint8_t b) {
  if (b == 0xAC || b == 0xAD || b == 0xAE) {
    rs485.write(0xAE);
    rs485.write(b ^ 0x80);
  } else {
    rs485.write(b);
  }
}

void stuurSnelheid(int16_t snelheid) {
  uint8_t vermogen = map(abs(snelheid), 0, 1000, 0, 100);
  uint8_t payload[6] = {
    0x30,                        // adres: MOTOR
    0x82,                        // message ID: DRIVE
    0x01,                        // flags: enable
    vermogen,                    // motorvermogen 0-100
    (uint8_t)(snelheid >> 8),    // snelheid hoog byte
    (uint8_t)(snelheid & 0xFF)   // snelheid laag byte
  };
  uint8_t crc = crc8(payload, 6);
  digitalWrite(RS485_DE, HIGH);
  rs485.write(0xAC);
  for (int i = 0; i < 6; i++) schrijfByte(payload[i]);
  schrijfByte(crc);
  rs485.write(0xAD);
  digitalWrite(RS485_DE, LOW);
}

void motorStop(const char* reden) {
  huidigSnelheid = 0;
  stuurSnelheid(0);
  Serial.print("STOP: ");
  Serial.println(reden);
  foutTeller++;
  EEPROM.write(EEPROM_FOUTEN, foutTeller);
}

void setup() {
  Serial.begin(9600);

  pinMode(RS485_DE, OUTPUT);
  digitalWrite(RS485_DE, LOW);
  pinMode(NOODSTOP_PIN, INPUT_PULLUP);
  pinMode(DODE_MAN_PIN, INPUT_PULLUP);

  rs485.begin(19200);

  foutTeller = EEPROM.read(EEPROM_FOUTEN);
  Serial.print("Opgeslagen fouten: ");
  Serial.println(foutTeller);

  wdt_enable(WDTO_2S);  // herstart Arduino als loop vastloopt
  Serial.println("Start");
}

void loop() {
  wdt_reset();  // vertel watchdog dat alles OK is

  // Noodstop (normaal gesloten: LOW = OK, HIGH = ingedrukt = stop)
  if (digitalRead(NOODSTOP_PIN) == HIGH) {
    motorStop("noodstop");
    delay(100);
    return;
  }

  // Dode man schakelaar (normaal open: LOW = losgelaten = stop)
  if (digitalRead(DODE_MAN_PIN) == LOW) {
    motorStop("dode man");
    delay(100);
    return;
  }

  // Potmeter lezen en omzetten
  int pot = analogRead(POT_PIN);
  int16_t doelSnelheid = map(pot, 0, 1023, 0, 1000);

  // Zachte start/stop: max 10 eenheden per stap (100ms = max 100 eenheden/sec)
  if (doelSnelheid > huidigSnelheid + 10)      huidigSnelheid += 10;
  else if (doelSnelheid < huidigSnelheid - 10) huidigSnelheid -= 10;
  else                                          huidigSnelheid = doelSnelheid;

  Serial.print("Pot: ");      Serial.print(pot);
  Serial.print("  Doel: ");   Serial.print(doelSnelheid);
  Serial.print("  Huidig: "); Serial.println(huidigSnelheid);

  stuurSnelheid(huidigSnelheid);
  delay(100);
}
