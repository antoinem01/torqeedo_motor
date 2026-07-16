// Torqeedo RS485 bus protocol (framing bytes 0xAC/0xAD/0xAE, CRC8) is based on
// ArduPilot's AP_Torqeedo driver: https://github.com/ArduPilot/ardupilot
// (libraries/AP_Torqeedo), licensed under the GNU GPLv3. See LICENSE.

#include <SoftwareSerial.h>
#include <avr/wdt.h>
#include <EEPROM.h>

#define RS485_TX      2
#define RS485_RX      3
#define RS485_DE      4
#define POT_PIN       A0
#define NOODSTOP_PIN  5   // normally closed button between pin and GND
#define DODE_MAN_PIN  6   // normally open button between pin and GND

#define EEPROM_FOUTEN 0   // EEPROM address for error counter

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
    0x30,                        // address: MOTOR
    0x82,                        // message ID: DRIVE
    0x01,                        // flags: enable
    vermogen,                    // motor power 0-100
    (uint8_t)(snelheid >> 8),    // speed high byte
    (uint8_t)(snelheid & 0xFF)   // speed low byte
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
  Serial.print("Stored errors: ");
  Serial.println(foutTeller);

  wdt_enable(WDTO_2S);  // restart Arduino if the loop hangs
  Serial.println("Start");
}

void loop() {
  wdt_reset();  // tell the watchdog everything is OK

  // Emergency stop (normally closed: LOW = OK, HIGH = pressed = stop)
  if (digitalRead(NOODSTOP_PIN) == HIGH) {
    motorStop("emergency stop");
    delay(100);
    return;
  }

  // Dead man switch (normally open: LOW = released = stop)
  if (digitalRead(DODE_MAN_PIN) == LOW) {
    motorStop("dead man switch");
    delay(100);
    return;
  }

  // Read potentiometer and convert
  int pot = analogRead(POT_PIN);
  int16_t doelSnelheid = map(pot, 0, 1023, 0, 1000);

  // Soft start/stop: max 10 units per step (100ms = max 100 units/sec)
  if (doelSnelheid > huidigSnelheid + 10)      huidigSnelheid += 10;
  else if (doelSnelheid < huidigSnelheid - 10) huidigSnelheid -= 10;
  else                                          huidigSnelheid = doelSnelheid;

  Serial.print("Pot: ");      Serial.print(pot);
  Serial.print("  Target: "); Serial.print(doelSnelheid);
  Serial.print("  Current: "); Serial.println(huidigSnelheid);

  stuurSnelheid(huidigSnelheid);
  delay(100);
}
