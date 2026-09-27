# tools — hoe deze print gemaakt is

`torqeedo_pcb.kicad_pcb` is niet met de hand in pcbnew gelegd; hij is
**gegenereerd** uit het schema door de scripts hiernaast. Ze staan hier zodat
een wijziging (zoals de PS1-footprint) niet met handwerk hoeft, en zodat
navolgbaar is hoe het bord tot stand kwam.

> ### Lees dit eerst
>
> **Het ingecheckte `torqeedo_pcb.kicad_pcb` is de waarheid, niet deze scripts.**
> Zodra je in de KiCad-GUI iets versleept, is het bord vooruit op de scripts.
> `regenerate.sh --install` gooit dat handwerk weg. Vanaf het moment dat je
> pcbnew opent: bewerk het bord, niet de scripts.

## Draaien

```sh
./tools/regenerate.sh             # bouwen + controleren in een tijdelijke map
./tools/regenerate.sh --install   # én over torqeedo_pcb.kicad_pcb heen zetten
```

Zonder `--install` raakt hij niets aan. Hij stopt met exit 1 als de router niet
alles rond krijgt of als DRC niet schoon is, dus een slecht bord kan er niet
stilletijds in glippen.

Nodig: KiCad 9 (`kicad-cli`) en de pcbnew-Python-binding, die in
`/usr/lib/python3/dist-packages` zit — niet in de venv die hier standaard actief
is. Daarom zet het script `PYTHONPATH` zelf. Verder `numpy` en `scipy`.

## Bekende eigenaardigheid: de uitkomst varieert per run

Bij een **vast** bordbestand is de router volledig deterministisch — drie runs
gaven exact 207 banen en 34 via's. Maar `place.py` geeft elke footprint een
nieuwe willekeurige UUID, en pcbnew levert footprints terug in een volgorde die
daarmee meebeweegt. Daardoor vallen de GND-stitching-via's net anders, en
kantelt de routering mee.

Praktisch: de ene run geeft 203 banen / 32 via's en alles rond, de volgende 207
/ 34 met één net dat niet lukt. **Dat is geen fout in je schema — draai gewoon
opnieuw.** Het script weigert een onvolledig resultaat, dus je merkt het meteen.

Ooit echt oplossen? Sorteer `padinfo['/GND']` op coördinaat in plaats van op
footprint-volgorde; dan is de hele keten deterministisch.

## De stappen

| Script | Doet |
|---|---|
| `parse_net.py` | netlist van `kicad-cli` → `net.json` (componenten, netten, symbool-UUID's) |
| `place.py` | plaatst alle 39 footprints op vaste coördinaten, kent netten toe, tekent de bordrand en de M3-gaten |
| `router.py` | de router: A\*-doolhofzoeker op een 0,15 mm-raster, 2 lagen, per net eigen clearance, plus het rechttrekken van trapjes |
| `route.py` | stuurt de router aan: eerst GND-via's, dan de netten in volgorde van kritiek naar grof, daarna koper en massavlakken |
| `finish.py` | silkscreen: aansluitbenamingen, titel, het kader voor de buck, en referenties die op een pad vielen |
| `audit.py` | rapport: baanlengte per net, via's, vulgraad van de vlakken, afstand A0 ↔ buck, kristal |
| `dump_fp.py` | hulpje: padposities van een footprint opvragen |
| `gauge.py` | genereert `ps1-buck-gauge.svg`, het 1:1 meetvel |

`place.py` bevat bovenin de plaatsingstabel (`PLACE`): per onderdeel x, y en
rotatie. Dát is de plek om de indeling te veranderen.

## Waar de plaatsing vandaan komt

De coördinaten volgen §11 van
[`../../../docs/pcb-geintegreerd.md`](../../../docs/pcb-geintegreerd.md):
kristal pal tegen pin 9/10, ontkoppeling tegen de voedingspinnen, de A0-tak ver
van de buck, RS485-terminatie bij de connector, 12 V apart in een hoek.
`audit.py` rekent na of dat ook echt gehaald is.
