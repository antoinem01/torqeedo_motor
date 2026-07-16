# Torqeedo motor

Arduino-sketch die een Torqeedo-motor aanstuurt via RS485, met een potmeter voor snelheidsregeling en twee veiligheidsschakelaars (noodstop en dodemansknop).

## Hardware

- Board: Arduino Uno
- Pinnen:
  - `2` — RS485 RX
  - `3` — RS485 TX
  - `4` — RS485 DE (driver enable)
  - `A0` — potmeter (snelheidsregeling)
  - `5` — noodstop (normaal gesloten knop tussen pin en GND)
  - `6` — dodemansknop (normaal open knop tussen pin en GND)

## Werking

- Leest de potmeter en stuurt de motor via een RS485-protocol met CRC8-checksum.
- Snelheid wordt geleidelijk opgebouwd/afgebouwd (zachte start/stop, max 10 eenheden per 100 ms).
- Bij noodstop of loslaten van de dodemansknop stopt de motor direct.
- Een watchdog timer (2 s) herstart de Arduino als de loop vastloopt.
- Het aantal fouten/stops wordt bijgehouden in EEPROM.

## Libraries

Alleen standaard Arduino-libraries nodig, geen externe dependencies:

- `SoftwareSerial`
- `EEPROM`
- `avr/wdt`

## Uploaden

Open `Torqeedo_motor.ino` in de Arduino IDE (of gebruik `arduino-cli`), selecteer board **Arduino Uno**, en upload.
