# IP68 & trillingsbestendige opbouw

Hoe je de aansturing van een **breadboard-prototype** naar een **waterdicht
(IP68)** en **schok-/trillingsbestendig** geheel brengt, geschikt voor permanent
gebruik op een boot. Dit document beschrijft de mechanische en afdichtings-kant;
de elektrische bedrading staat in [`torqeedo-1103cl-aansturing.md`](torqeedo-1103cl-aansturing.md)
en de voedingsopbouw (buck, zekeringen, hoofdschakelaar) in de
[`README`](../README.md).

> ⚠️ Het breadboard uit de banktest is **niet** geschikt voor gebruik op het
> water: trillingen schudden de steekverbindingen los en het is niet
> waterdicht. Alles hieronder gaat ervan uit dat je opnieuw en definitief
> opbouwt.

---

## 1. Wat betekent IP68 hier — en heb je het echt nodig?

| Code | Stof | Water |
|---|---|---|
| IP67 | Stofdicht | Onderdompeling tot **1 m / 30 min** |
| IP68 | Stofdicht | Langdurige onderdompeling, **dieper dan 1 m**, duur/diepte door fabrikant gespecificeerd |

Voor elektronica die **boven de waterlijn** in een kastje zit, is **IP67 in de
praktijk al ruim voldoende** (spatwater, regen, een golf). **IP68** is pas echt
nodig als het geheel **onder water** kan komen te staan of blijvend nat staat
(bilge, of montage laag in de romp). Kies bewust: IP68 is duurder en moeilijker
te onderhouden. De rest van dit document mikt op IP68, met IP67 als het
minimum-alternatief waar dat volstaat.

---

## 2. Twee strategieën

Er zijn twee manieren om IP68 + trillingsbestendig te halen. Ze sluiten elkaar
niet uit — je kunt een afgedichte behuizing combineren met lokaal ingieten.

| | A. Afgedichte behuizing | B. Volledig ingegoten (potting) |
|---|---|---|
| **Waterdicht** | Goed (afhankelijk van afdichting/wartels) | Uitstekend — hars sluit alles in |
| **Trillingsbestendig** | Redelijk (mits alles vastgezet) | Uitstekend — niets kan bewegen |
| **Warmteafvoer** | Goed (lucht rond componenten) | Slecht — hars houdt warmte vast |
| **Onderhoud/servicebaar** | Ja, kastje open | Nee — onherstelbaar ingegoten |
| **Aanpasbaar** | Ja | Nee |

**Aanbeveling:** begin met **A** (afgedichte behuizing met alles mechanisch
vastgezet). Dat geeft IP67–IP68 én blijft servicebaar. Overweeg **B (potting)**
alleen voor het kleine, definitieve print-deel als trillingen daar een
hardnekkig probleem blijven — en **giet de buck-converter nooit volledig in**
(warmte).

---

## 3. Behuizing

- **Rating:** IP68 (of IP67) afdichtdoos. Let op de fabrikantsopgave van
  diepte/duur bij IP68.
- **Materiaal:** ABS/polycarbonaat (goedkoop, corrosievrij) of aluminium
  (robuuster, betere warmteafvoer, maar let op galvanische corrosie in zilte
  omgeving — isoleer van andere metalen).
- **Formaat:** ruim kiezen — minimaal ~15×10×6 cm (Arduino Uno is 68×53 mm),
  plus ruimte voor MAX485, buck-converter, zekeringhouders en bedrading.
- **Deksel:** doorlopende siliconen/EPDM-afdichtring, roestvrije (RVS A4/316)
  schroeven. Draai kruislings en gelijkmatig aan zodat de ring egaal knijpt.
- **Montage van het kastje zelf:** op **trillingsdempers** (rubberen
  silentblocks) tegen de romp, niet star vastgeschroefd — dat scheelt de
  elektronica veel schok.

---

## 4. Elektronica trillingsbestendig monteren (weg van breadboard)

Dit is de kern van "tegen abrupte bewegingen". Trillingen en schokken breken
steekverbindingen, laten soldeer scheuren bij zware componenten en trekken
connectoren los.

- **Soldeer alles vast** op een perfboard/prototypeshield of een custom PCB —
  **geen breadboard, geen losse Dupont-draadjes** in de eindopstelling.
- **Zware componenten extra fixeren:** elco's, connectoren, de buck-converter en
  het MAX485-bordje vastzetten met een klodder **RTV-silicone of hot-glue** zodat
  ze niet op hun pootjes staan te trillen (dat vermoeit de soldeerpunten).
- **Print zwevend monteren** op RVS-afstandsbusjes met rubberen ringetjes of
  nylon standoffs — demp de print van de behuizing.
- **Connectoren met vergrendeling** waar losneembaar moet zijn: JST-XH met
  vergrendeling, of schroefklemmen (Phoenix-type). Vermijd gladde headerpinnen.
- **Schroefdraad borgen:** een druppel **schroefborgmiddel (Loctite)** of
  borgmoeren op bevestigingen die door trilling los kunnen lopen.
- **Trekontlasting op elke kabel** die de print of het kastje verlaat, zodat een
  ruk of trilling nooit op de soldeerpunt of de wartel komt.
- **Conformal coating** (acryl of urethaan) op de gesoldeerde print beschermt
  tegen vocht en condens — een goedkope, effectieve extra laag, ook zonder
  volledige potting.

---

## 5. Kabeldoorvoeren & connectoren

De afdichting is zo goed als zijn zwakste doorvoer. Standaard PG-wartels zijn
vaak maar IP54–IP68 afhankelijk van uitvoering — kies bewust.

- **Kabelwartels:** IP68-gecertificeerde wartels (M-serie, bijv. M12/M16/M20)
  met correcte klembereik voor de kabeldiameter. Te dun t.o.v. de wartel = geen
  afdichting. Gebruik een **blindstop** in ongebruikte gaten.
- **Externe connectoren (loskoppelbaar):** IP68 **M12-connectoren** of marine
  bulkhead-connectoren voor motorkabel, voeding en bediening. Handiger dan de
  kabel door een wartel als je onderdelen wilt kunnen loskoppelen.
- **Aantal doorvoeren** (minimaliseer — elke doorvoer is een risico):

  | Doorvoer | Voor |
  |---|---|
  | 1× | Motorkabel (RS485 A/B + GND, en evt. motorvoeding-retour) |
  | 1× | Voedingskabel van accu |
  | 1× | Bedieningskabel (potmeter/gashendel) |
  | 1× | Noodstop + dode man |

- **Afdichting rond de kabel** binnenin extra borgen met een kabelbinder/klem
  net binnen de wartel, zodat trek niet aan de afdichting trekt.

---

## 6. Condens & drukvereffening

Een volledig dichte behuizing "ademt" bij temperatuurwisselingen: opwarmen en
afkoelen bouwt onder-/overdruk op die de afdichting belast en vocht naar binnen
kan trekken. Condens binnenin is een sluipende oorzaak van corrosie.

- **Drukvereffeningsventiel (Gore-type breather):** laat lucht/druk door maar
  houdt water tegen (IP68). Sterk aanbevolen voor een dichte behuizing buiten.
- **Droogmiddel (silicagel)** zakje in het kastje als extra buffer tegen
  restvocht bij het sluiten.
- Sluit het kastje bij voorkeur in een **droge, koele omgeving** zodat je geen
  vochtige lucht opsluit.

---

## 7. Bediening & schakelaars

De bediening en veiligheidsschakelaars moeten dezelfde IP-klasse halen als de
rest — zij zitten buiten het kastje en krijgen direct water.

- **Bediening:** IP67/IP68 potmeter, of een **marine gashendel** (professioneel,
  goede haptiek, midden-detent voor voel-baar "stop"). Alternatief zonder
  mechanisch contact: **AS5600 hall-sensor** achter een afgedicht magneetknopje —
  onverwoestbaar en makkelijk waterdicht te maken.
- **Noodstop:** afgedichte (IP67+) paddenstoel-noodstop, normaal gesloten.
- **Dode man:** afgedichte drukknop of hendel, normaal open. Denk aan een
  marine-uitvoering die tegen zout en UV kan.
- **Kabels naar deze onderdelen** via IP68-wartels of M12-connectoren, met
  trekontlasting.

---

## 8. Kabels, routing & corrosie

- **Marine-grade kabel:** vertind koper (tinned copper) tegen corrosie, flexibel,
  met olie-/UV-bestendige mantel.
- **Routing vastzetten:** P-clips of kabelklemmen om de ~20–30 cm zodat kabels
  niet vrij hangen te zwiepen (trilling = draadbreuk bij de connector). Laat een
  kleine **serviceslinger** (lus) bij connectoren zodat er geen trek op staat.
- **Bevestigingsmateriaal:** RVS **A4/316** in zilte omgeving. Vermijd
  verschillende metalen tegen elkaar (galvanische corrosie).
- **Zekeringhouders & klemmen** in een waterdichte uitvoering of binnen het
  afgedichte kastje houden.

---

## 9. Warmte

Waterdicht maken en warmte afvoeren zijn tegengesteld. Het grootste warmtepunt
is de **buck-converter** (29,6 V → 5 V).

- Kies een buck met **ruime marge** op de stroom zodat hij koel blijft.
- **Giet de buck niet volledig in** hars (strategie B) — dan kan de warmte
  nergens heen.
- Bij een aluminium behuizing: monteer warme componenten **thermisch tegen de
  wand** (met thermisch pad) zodat de behuizing als koellichaam werkt.
- Houd de motor-vermogenselektronica (~40 A circuit) zo mogelijk **buiten** het
  logica-kastje — dat scheelt warmte en ruis.

---

## 10. Testprotocol

Test in deze volgorde, vóór montage op de boot:

1. **Droge functietest** — doorloop eerst de
   [bench-test checklist](bench-test-checklist.md) met de definitieve, gesoldeerde
   opbouw (nog niet dichtgemaakt). Alles moet werken zoals op het breadboard.
2. **Trillingstest** — schud/klop het kastje stevig, tik erop, terwijl de
   Serial Monitor of de motor loopt. Er mag **geen** onderbreking, reset of
   `STOP: comms lost` optreden. Zo niet → een verbinding zit los.
3. **Waterdichtheidstest (leeg of met dummy):** dompel de gesloten, afgedichte
   behuizing onder (of besproei ruim, afhankelijk van je doel-IP) en controleer
   op binnendringend water. Doe dit **vóór** je de echte elektronica erin
   vertrouwt — of test met een papieren indicator/silicagel die verkleurt.
4. **Thermische test** — laat het geheel een tijd draaien en voel/meet of niets
   oververhit (buck, MAX485, bedrading).
5. **Herhaal na trilling:** na de trillingstest nog eens de waterdichtheid
   controleren — trillingen kunnen een afdichting of wartel loswerken.

---

## 11. Onderdelen & zoektermen

| Onderdeel | Zoekterm |
|---|---|
| IP68 behuizing | "IP68 enclosure ABS", "waterproof enclosure" (Kiwi Electronics, Conrad, Reichelt) |
| IP68 kabelwartels | "IP68 cable gland M12/M16" |
| M12 connectoren | "M12 connector waterproof A-coded panel mount" |
| Drukvereffeningsventiel | "Gore protective vent", "pressure equalization valve M12" |
| Trillingsdempers | "rubber vibration mount / silentblock M4" |
| Conformal coating | "conformal coating acrylic PCB" (spuitbus) |
| Potting compound | "polyurethane potting compound" (flexibel, i.p.v. hard epoxy voor trillingen) |
| RVS bevestiging | "RVS A4 / 316 bouten moeren" |
| IP67 potmeter | "IP67 potentiometer waterproof" |
| Marine gashendel | "marine throttle control single lever" |
| Afgedichte noodstop | "IP67 emergency stop mushroom NC" |
| Vertind kabel | "marine tinned copper wire" |

---

## 12. Checklist

- [ ] Alles gesoldeerd op perfboard/PCB — **geen breadboard/Dupont** meer
- [ ] Zware componenten vastgezet met RTV/hot-glue
- [ ] Print op trillingsdempers/standoffs, kastje op silentblocks
- [ ] Conformal coating op de print
- [ ] Alle interne connectoren met vergrendeling; schroeven geborgd (Loctite)
- [ ] Trekontlasting op elke kabel
- [ ] IP68-wartels/M12-connectoren, ongebruikte gaten met blindstop
- [ ] Drukvereffeningsventiel + silicagel geplaatst
- [ ] Bediening + noodstop + dode man in IP67/IP68-uitvoering
- [ ] Kabels vastgeklemd (P-clips), serviceslinger bij connectoren
- [ ] RVS A4/316 bevestiging, geen ongelijke metalen tegen elkaar
- [ ] Buck-converter koel en **niet** ingegoten
- [ ] Trillingstest doorstaan zonder onderbreking/`STOP: comms lost`
- [ ] Waterdichtheidstest doorstaan (ook ná trillingstest)
