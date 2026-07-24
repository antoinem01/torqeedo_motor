# Bench-test checklist — Torqeedo motoraansturing

Doorloop deze lijst **op de werkbank**, vóór elk gebruik op het water. Test in de
volgorde hieronder: eerst alles zonder motorvoeding, daarna pas met de accu erop
en **altijd zonder belasting** (schroef eraf of boot vastgezet).

> ⚠️ Deze sketch is nog **niet gevalideerd tegen de echte motor**. Wees extra
> voorzichtig: houd je hand bij de noodstop en de hoofdschakelaar.

---

## 0. Vooraf

- [ ] Schroef verwijderd, of boot stevig vastgezet zodat er geen stuwkracht kan ontstaan
- [ ] Hoofdschakelaar / uittrekstekker UIT, accu losgekoppeld
- [ ] Laatste `Torqeedo_motor/Torqeedo_motor.ino` geüpload (board **Arduino Uno**, upload zonder fouten)
- [ ] Brandblusser / manier om snel de stroom eraf te halen binnen handbereik

## 1. Bedrading controleren (visueel, stroomloos)

- [ ] `2` → MAX485 `DI`, `3` → `RO`, `4` → `DE`+`RE` (samen)
- [ ] MAX485 `VCC` → 5V, `GND` → GND
- [ ] Potmeter: wiper → `A0`, buitenpennen → 5V en GND
- [ ] Noodstop (normaal gesloten) tussen pin `5` en GND
- [ ] Dode man (normaal open) tussen pin `6` en GND
- [ ] RS485 `A`/`B` naar de motorconnector (polariteit later verifiëren)
- [ ] **Gemeenschappelijke massa**: accu-, Arduino- en MAX485-GND aan elkaar
- [ ] Twee aparte zekeringen: zwaar (~40A) motorcircuit, klein (~1A) logica

## 2. Eerste keer aan — alleen logica, GEEN motorvoeding

Voed alleen de Arduino (USB of buck), motoraccu nog LOS.

- [ ] Serial Monitor open op **9600 baud**
- [ ] Bij opstarten verschijnt `Stored errors: <n>` en daarna `Start`
- [ ] Loop print continu `Pot: … Target: … Current: …`
- [ ] Potmeter op **midden** → `Target` ≈ 0 (binnen de dode zone)
- [ ] Potmeter naar één kant → `Target` loopt naar **+1000** (vooruit)
- [ ] Potmeter naar de andere kant → `Target` loopt naar **−1000** (achteruit)
- [ ] `Current` volgt `Target` **geleidelijk** (soft-start, max ~10 per stap)
- [ ] Dode zone werkt: kleine afwijking rond het midden → `Target` blijft 0

## 3. Veiligheidsschakelaars (nog steeds zonder motorvoeding)

- [ ] Noodstop indrukken → `STOP: emergency stop` verschijnt **één keer**, `Current` → 0
- [ ] Noodstop ingedrukt houden → géén herhaalde STOP-regels (edge-logging werkt)
- [ ] Noodstop loslaten → loop draait weer normaal
- [ ] Dode man **loslaten** → `STOP: dead man switch`, `Current` → 0
- [ ] Dode man vasthouden → loop draait normaal
- [ ] Bij een STOP loopt `Stored errors` bij herstart met precies +1 per gebeurtenis

## 4. Watchdog

- [ ] (Optioneel) simuleer een hang: tijdelijk een `while(1);` inbouwen →
      Arduino herstart binnen ~2 s (je ziet opnieuw `Start`). **Fix daarna terugdraaien!**

## 5. Met motorvoeding — zonder belasting

Sluit nu pas de motoraccu aan. Schroef eraf / boot vast. Hand bij de noodstop.

- [ ] Buck-converter meet **5V** aan de Arduino (vóór aansluiten gecontroleerd)
- [ ] Motoraccu-spanning plausibel (~24–29V)
- [ ] Potmeter op midden bij inschakelen → motor blijft **stil**
- [ ] Langzaam vooruit → motor draait vooruit, toerental volgt de potmeter
- [ ] Reageert de motor niet? Zet dan `A`/`B` op de RS485-bus om
- [ ] Langzaam achteruit → motor draait de **andere** kant op
- [ ] Door het midden bewegen (vooruit↔achteruit) → gaat vloeiend via nul
- [ ] **Noodstop onder belastingloos toerental** → motor stopt direct
- [ ] **Dode man loslaten onder toerental** → motor stopt direct
- [ ] Hoofdschakelaar / uittrekstekker → hele systeem valt dood (onafhankelijk van software)

## 6. Afronden

- [ ] Geen oververhitting bij MAX485, buck-converter of bedrading (voel/ruik)
- [ ] `Stored errors`-teller genoteerd (nulpunt voor volgende sessie)
- [ ] Pas ná een volledig geslaagde banktest: overweeg een test met schroef in het
      water, aangemeerd en met iemand aan de noodstop

---

## Faalgedrag — wat te doen

| Symptoom | Waarschijnlijke oorzaak |
|---|---|
| Motor reageert niet | `A`/`B` omgedraaid, geen gemeenschappelijke massa, DE niet geschakeld |
| Motor kruipt bij neutraal | Potmeter niet op midden, of dode zone te klein |
| Draait verkeerde kant op | Potmeter-buitenpennen omdraaien, of `A`/`B` |
| Continue STOP-regels | Schakelaarlogica omgekeerd (NC/NO) — controleer bedrading pin 5/6 |
| Willekeurige herstarts | Watchdog trigger (loop te traag) of voedingsdip op de 5V |
