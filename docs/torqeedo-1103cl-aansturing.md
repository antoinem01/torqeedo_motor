# Torqeedo 1103CL — Arduino aansturing via RS485

## Doel

Potmeter → Arduino → RS485 → Torqeedo 1103CL (Long shaft, 24V)

---

## Hardware

| Onderdeel | Details |
|---|---|
| Motor | Torqeedo 1103CL (24V nominaal, tot ~29V vol) |
| Controller | Arduino (Uno/Nano) |
| RS485 interface | TTL-to-RS485 bordje (bijv. MAX485) |
| Bediening | Potmeter op A0 |
| Noodstop | Normaal gesloten drukknop op pin 5 |
| Dode man schakelaar | Normaal open drukknop op pin 6 |
| Voeding motor | 24V LiFePO4 accu (later: 48V accu via Victron Orion DC-DC) |
| Voeding Arduino | 5V via USB of eigen voeding |

---

## Aansluiting

### Potmeter → Arduino

De potmeter heeft 3 pinnen:

```
   +-----+
   |     |
   1  2  3
```

| Pin | Naam | Arduino |
|---|---|---|
| 1 | Linker buitenste | GND |
| 2 | Middelste (wiper) | A0 |
| 3 | Rechter buitenste | 5V |

Pin 1 en 3 mogen omgedraaid — dat bepaalt alleen welke kant vooruit is.

**Bediening (midden = stop):** de potmeterstand wordt gemapt op `-1000…+1000`.
Helemaal naar één kant = vol achteruit, midden = stil, helemaal naar de andere
kant = vol vooruit. Rond het midden zit een dode zone (~5%) zodat de motor bij
neutraal niet kruipt. Een draaipotmeter heeft geen mechanische midden-klik, dus
voor achteruit is een midden-detent potmeter of joystick/gashendel prettiger —
dan voel je waar stop zit.

### Arduino → RS485-bordje

Het TTL-to-RS485 bordje heeft aan de TTL-kant 4 pinnen (VCC, GND, RX, TX).
VCC = de positieve voedingspin (5V).

| TTL-bordje | Arduino |
|---|---|
| VCC | 5V |
| GND | GND |
| RX | Pin 3 (TX) |
| TX | Pin 2 (RX) |

Let op: RX van het bordje gaat naar TX van de Arduino en omgekeerd.

**Voeding delen zonder breadboard:** sluit een kort draadje van VCC op het RS485-bordje naar pin 3 van de potmeter, en van GND naar pin 1 van de potmeter.

De RS485-kant van het bordje heeft A en B aansluitingen voor naar de motor.

### Noodstop → Arduino
- Normaal gesloten knop tussen pin 5 en GND
- Ingedrukt = circuit open = motor stopt

### Dode man schakelaar → Arduino
- Normaal open knop tussen pin 6 en GND
- Vasthouden = circuit gesloten = motor draait
- Loslaten = circuit open = motor stopt direct

### RS485-bordje → Gele motorconnector (X60)
| RS485-bordje | Connector |
|---|---|
| A (+) | A (+) |
| B (-) | B (-) |
| GND | GND |

### Motorconnector pinout
- **A (+)** — RS485 Data+
- **B (-)** — RS485 Data-
- **GND** — Massa (2 pinnen)
- **VCC** — Motorvoeding van accu
- **NC** — Not connected

Bron: https://ardupilot.org/rover/_images/torqeedo-motor-cable-small-annotated.jpg

---

## Protocol (TQBus RS485)

- **Baud rate:** 19200
- **Header:** 0xAC
- **Footer:** 0xAD
- **Escape byte:** 0xAE (gevolgd door originele byte XOR 0x80)
- **CRC:** Dallas/Maxim CRC-8 (polynoom 0x8C)
- **Update interval:** 100ms (10Hz)

### Motoradres en commando
| Constante | Waarde |
|---|---|
| Adres MOTOR | 0x30 |
| Message ID DRIVE | 0x82 |

### DRIVE bericht payload (6 bytes)
| Byte | Inhoud |
|---|---|
| 0 | Adres: 0x30 (MOTOR) |
| 1 | Message ID: 0x82 (DRIVE) |
| 2 | Flags: 0x01 (enable, bit 0) |
| 3 | Motorvermogen: 0–100 |
| 4 | Snelheid hoog byte (signed, -1000 tot +1000) |
| 5 | Snelheid laag byte |

Gevolgd door CRC-byte, alles tussen 0xAC en 0xAD.

---

## Bediening — opties voor potmeter

| Optie | Voordeel | Nadeel | Codewijziging |
|---|---|---|---|
| IP67 potmeter | Zelfde aansluiting, waterdicht | Mechanisch contact slijt | Geen |
| Hall sensor (AS5600) | Geen mechanisch contact, onverwoestbaar | Iets meer software | Minimaal |
| IP67 joystick | Voor/achteruit in één beweging | Iets duurder | Kleine aanpassing |
| Marine gashendel | Professioneel, goede haptiek | Duurder | Kleine aanpassing |

**Aanbeveling nu:** IP67 potmeter — zelfde aansluiting als huidige potmeter, gewoon buiten het kastje monteren.

**Aanbeveling later:** marine gashendel voor een nette eindoplossing.

Zoektermen:
- IP67 potmeter: "IP67 potentiometer" of "waterproof potentiometer" (€5-15)
- Hall sensor: "AS5600 rotary encoder"
- Marine gashendel: "marine throttle control single lever"

---

## Robuustheid

| Maatregel | Implementatie |
|---|---|
| Noodstop | Normaal gesloten knop op pin 5 — indrukken stopt motor direct |
| Dode man schakelaar | Normaal open knop op pin 6 — loslaten stopt motor direct |
| Watchdog timer | Arduino herstart zichzelf als de code vastloopt (timeout 2 seconden) |
| Zachte start/stop | Snelheid verandert max 10 eenheden per 100ms (100 eenheden/sec) |
| Foutlogging | Aantal stops wordt opgeslagen in EEPROM, zichtbaar na herstart via Serial Monitor |
| Hardware (nog te doen) | Weg van breadboard (solderen/perfboard), getwiste RS485-paar, zekeringen (~40A motor / ~1A logica), buck-converter i.p.v. USB, hoofdschakelaar, waterproof behuizing |

---

## Arduino sketch

De volledige sketch staat in [`Torqeedo_motor/Torqeedo_motor.ino`](../Torqeedo_motor/Torqeedo_motor.ino).

---

## Testen

1. Sluit de potmeter aan op de Arduino (5V, GND, wiper naar A0)
2. Sluit het RS485-bordje aan op de Arduino (pin 2, 3, 4, 5V, GND)
3. Verbind RS485-bordje met de motorconnector (A+, B-, GND)
4. Zet de motorvoeding aan (24V accu)
5. Draai de potmeter — de motor zou moeten reageren

### Uitgevoerde banktest (2026-07-25) — geslaagd ✅

Getest tegen een echte Travel 1103 CL, onbelast (schroef in de lucht):

- Motorvoeding: regelbare DC-voeding (BaseTech BT-305) op **29V, 5A-limiet**.
  Logica (Arduino + RS485-bordje) apart gevoed via USB — met **gemeenschappelijke
  massa** tussen USB-GND en de min van de DC-voeding.
- Bij inschakelen trok de motorcontroller een **ruststroom van ~0,06A** (bewijs
  dat de motorelektronica opstartte en op commando's wachtte).
- Potmeter vooruit → schroef draaide vooruit; andere kant → schroef draaide
  **achteruit**. Aansturing en protocol werken dus.

**Nog niet getest:** gebruik onder belasting (in het water) en de definitieve
voedingsopbouw (buck-converter, zekeringen, hoofdschakelaar). Een DC-voeding van
5A is te zwak voor de motor onder belasting (~30A vol) — die is alleen geschikt
voor deze onbelaste banktest.

### Bekende valkuilen uit de banktest

| Symptoom | Oorzaak / oplossing |
|---|---|
| `Pot: 0`, `Target: -1000` blijft hangen | 5V-kant van de potmeter kwam niet aan (los draadje / dode railhelft). Meet 5V tussen de twee buitenpennen van de pot. |
| Alleen TXD-lampje knippert, RXD donker | Normaal zolang de motor niet aangesloten/antwoordend is: TXD = Arduino zendt, RXD licht pas op als de motor terugpraat. |
| Motor reageert niet | `A`/`B` omwisselen; gemeenschappelijke massa ontbreekt; DE niet geschakeld. |
| Breadboard-voeding valt steeds weg | Massief draad i.p.v. gevlochten, verse gaatjes, beide railhelften voeden. Breadboard is sowieso ongeschikt voor de eindopstelling (trillingen). |

---

## Behuizing

**Type:** IP67 of IP68 afdichtingsbox (spatwaterdicht tot onderwaterdicht)

**Formaat:** minimaal 15×10×6cm (Arduino Uno is 68×53mm)

**Materiaal:** ABS kunststof (goedkoop, voldoende) of aluminium (robuuster)

**Kabeldoorvoeren:** blindnippels of PG-kabelwartels voor draden naar buiten (motor, potmeter, knoppen, voeding)

### Waar te koop

| Winkel | Zoekterm |
|---|---|
| Gamma / Praxis | afdichtdoos buitengebruik (IP65/IP67, €5-10) |
| Conrad | "IP67 behuizing" of "afdichtdoos" |
| Kiwi Electronics | "waterproof enclosure" |
| Reichelt | "Gehäuse IP67" |
| Amazon | "IP67 junction box ABS" |

Voor een prototype volstaat een Gamma/Praxis afdichtdoos. Voor een nettere uitvoering: aluminium Hammond-behuizing via Conrad of Reichelt.

### Kabeldoorvoeren

Kabels komen waterdicht naar buiten via **PG-kabelwartels**:

1. Boor een gat in de zijkant van het kastje
2. Schroef de kabelwartel erin (met moer aan de binnenkant)
3. Voer de kabel erdoor
4. Draai de kap aan — die knijpt een rubberen ring om de kabel dicht

**Maten:** PG7 (dunne draadjes) of PG9 (iets dikker)

**Benodigde wartels:**

| Wartel | Voor |
|---|---|
| 1× | Motorcabel (RS485 A/B/GND) |
| 1× | Potmeterkabel |
| 1× | Noodstop + dode man knoppen |
| 1× | Voedingskabel |

**Waar te koop:** Conrad, Gamma, Praxis — €0,50-2,00 per stuk.

---

## Voedingsplan

- **Nu:** 24V LiFePO4 accu (originele Torqeedo batterij, ~29V vol)
- **Later:** 48V accu → Victron Orion DC-DC converter → 24V naar motor

### Voeding elektronica

Alles loopt op 5V uit de Arduino. De Arduino krijgt voeding van een **step-down converter** (buck converter) aangesloten op de 24V accu.

```
24V accu ──→ Step-down converter (24V → 5V) ──→ Arduino VIN of 5V pin
                                                        │
                                                        ├──→ TTL-RS485 bordje (via 5V pin)
                                                        └──→ Potmeter (via 5V pin)
```

Knoppen (noodstop, dode man) hebben geen eigen voeding nodig — die lopen via de Arduino.

**Instellen:** stel de step-down converter in op **5V uitgang** voordat je hem aansluit op de Arduino. Te hoog voltage beschadigt de Arduino.

**Aansluiting step-down → Arduino:**
- Uitgang + → Arduino VIN (als de converter regelbaar is en je zeker bent van 7-12V) of rechtstreeks naar 5V pin (als de converter exact op 5V staat)
- Uitgang − → Arduino GND

**Extra wartel nodig:** voedingskabel van accu naar kastje via PG-kabelwartel.

---

## Bronnen

- ArduPilot AP_Torqeedo library: https://github.com/ArduPilot/ardupilot/tree/master/libraries/AP_Torqeedo
- ArduPilot Torqeedo documentatie: https://ardupilot.org/rover/docs/common-torqeedo.html
- Connector pinout afbeelding: https://ardupilot.org/rover/_images/torqeedo-motor-cable-small-annotated.jpg
