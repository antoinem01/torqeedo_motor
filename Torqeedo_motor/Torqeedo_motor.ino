// Copyright (C) 2026 antoinem01
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <https://www.gnu.org/licenses/>.
//
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

#define COMMS_TIMEOUT_MS 1000  // fail-safe stop if no valid motor reply for this
                               // long (only enforced once comms has been seen)

SoftwareSerial rs485(RS485_RX, RS485_TX);

int16_t huidigSnelheid = 0;
uint8_t foutTeller = 0;
bool gestopt = false;   // true while a safety switch keeps the motor stopped

unsigned long laatsteReplyMs = 0;  // millis() of the last valid motor reply
bool commsGezien = false;          // true once the motor has ever replied validly
bool commsVerloren = false;        // edge flag: comms-loss already logged this event

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

// Drain the RS485 receive buffer and reassemble any reply frame the motor sent
// (same framing as we transmit: 0xAC start, 0xAD end, 0xAE escape + XOR 0x80,
// trailing CRC8). Returns true if at least one complete, CRC-valid frame was
// decoded. We only need "did the motor answer?", not the payload contents, so
// a valid frame is enough to prove the bus and controller are alive. Parser
// state is static so a frame split across calls is still reassembled.
bool leesMotorReply() {
  static uint8_t buf[32];
  static uint8_t len = 0;
  static bool inFrame = false;
  static bool escape = false;
  bool geldig = false;

  while (rs485.available()) {
    uint8_t b = rs485.read();
    if (b == 0xAC) {            // start of frame (resync on any 0xAC)
      inFrame = true; escape = false; len = 0;
      continue;
    }
    if (!inFrame) continue;     // junk before a start byte
    if (b == 0xAD) {            // end of frame: last byte is the CRC
      inFrame = false;
      if (len >= 2 && crc8(buf, len - 1) == buf[len - 1]) geldig = true;
      continue;
    }
    if (b == 0xAE) { escape = true; continue; }  // next byte is XOR 0x80
    if (escape) { b ^= 0x80; escape = false; }
    if (len < sizeof(buf)) buf[len++] = b;
    else inFrame = false;       // overflow: drop this frame
  }
  return geldig;
}

// Keep the motor stopped. Logs the stop and bumps the EEPROM error counter only
// once, on the transition into the stopped state, to avoid wearing out the EEPROM
// while a switch is held (the loop runs every ~100 ms).
void motorStop(const char* reden) {
  huidigSnelheid = 0;
  stuurSnelheid(0);
  if (!gestopt) {
    Serial.print("STOP: ");
    Serial.println(reden);
    if (foutTeller < 255) foutTeller++;
    EEPROM.update(EEPROM_FOUTEN, foutTeller);
    gestopt = true;
  }
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

  laatsteReplyMs = millis();  // arm the comms clock; fail-safe stays dormant
                              // until the motor has actually replied once

  wdt_enable(WDTO_2S);  // restart Arduino if the loop hangs
  Serial.println("Start");
}

void loop() {
  wdt_reset();  // tell the watchdog everything is OK

  // Read any reply the motor sent since our last frame. A valid framed reply
  // proves the RS485 link and the motor controller are alive.
  if (leesMotorReply()) {
    laatsteReplyMs = millis();
    if (!commsGezien) {
      Serial.println("Motor comms OK");  // fail-safe is now armed
      commsGezien = true;
    }
    commsVerloren = false;
  }

  // Emergency stop (normally closed: LOW = OK, HIGH = pressed = stop)
  if (digitalRead(NOODSTOP_PIN) == HIGH) {
    motorStop("emergency stop");
    delay(100);
    return;
  }

  // Dead man switch (normally open button to GND, INPUT_PULLUP):
  // held = closed = LOW = run, released = open = HIGH = stop. A broken or
  // disconnected wire reads HIGH too, so it fails safe to stop.
  if (digitalRead(DODE_MAN_PIN) == HIGH) {
    motorStop("dead man switch");
    delay(100);
    return;
  }

  // Both safety switches OK again: allow the next stop to be logged.
  gestopt = false;

  // Comms-loss fail-safe: once the motor has ever replied, a prolonged silence
  // means a broken bus or a dead controller. Command stop and refuse to drive
  // until replies resume, so we never keep pushing a link we've lost. If the
  // motor never replies (commsGezien stays false) this stays dormant, so it
  // can't brick a setup where the motor sends no status back.
  if (commsGezien && (millis() - laatsteReplyMs) > COMMS_TIMEOUT_MS) {
    huidigSnelheid = 0;
    stuurSnelheid(0);
    if (!commsVerloren) {
      Serial.println("STOP: comms lost");
      if (foutTeller < 255) foutTeller++;
      EEPROM.update(EEPROM_FOUTEN, foutTeller);
      commsVerloren = true;
    }
    delay(100);
    return;
  }

  // Read potentiometer and convert. Centre = stop: fully left = full reverse,
  // middle = idle, fully right = full forward.
  int pot = analogRead(POT_PIN);
  int16_t doelSnelheid = map(pot, 0, 1023, -1000, 1000);

  // Dead zone around the centre so the motor doesn't creep at neutral (a pot
  // rarely sits exactly at the middle).
  if (abs(doelSnelheid) < 50) doelSnelheid = 0;

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
