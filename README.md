# Torqeedo motor

Arduino sketch that drives a Torqeedo motor over RS485, with a potentiometer for speed control and two safety switches (emergency stop and dead man switch).

## Hardware

- Board: Arduino Uno
- Pins:
  - `2` — RS485 RX
  - `3` — RS485 TX
  - `4` — RS485 DE (driver enable)
  - `A0` — potentiometer (speed control)
  - `5` — emergency stop (normally closed button between pin and GND)
  - `6` — dead man switch (normally open button between pin and GND)

## How it works

- Reads the potentiometer and drives the motor via an RS485 protocol with a CRC8 checksum.
- Speed is ramped up/down gradually (soft start/stop, max 10 units per 100 ms).
- The motor stops immediately on emergency stop or when the dead man switch is released.
- A watchdog timer (2 s) restarts the Arduino if the loop hangs.
- The number of errors/stops is tracked in EEPROM.

## Libraries

Only standard Arduino libraries are needed, no external dependencies:

- `SoftwareSerial`
- `EEPROM`
- `avr/wdt`

## Uploading

Open `Torqeedo_motor.ino` in the Arduino IDE (or use `arduino-cli`), select board **Arduino Uno**, and upload.
