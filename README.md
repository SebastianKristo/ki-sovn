<p align="center"><img src="icon.png" width="128" alt="KI Søvn"></p>

# KI Søvn

Custom integration for Home Assistant som avgjør automatisk om en person sover, og
speiler resultatet inn i en bryter (f.eks. Homey `switch.homey_logic_<navn>_sovn_vaken`).

Én oppføring per person. Alle sensorer er valgfrie utenom hjemme/borte – motoren bruker det som finnes.

## Installasjon (HACS)
1. HACS → Integrations → ⋮ → Custom repositories → `https://github.com/SebastianKristo/ki-sovn` (Integration)
2. Installer **KI Søvn**, restart HA
3. Innstillinger → Enheter og tjenester → Legg til integrasjon → **KI Søvn**

## Signaler
| Observasjon | Kilde | Kommentar |
|---|---|---|
| hjemme | hjemme/borte-bryter | borte = tvungen våken |
| sovevindu | klokkeslett | konfigurerbart per person |
| i rommet | presence-sensor | holdes `on` i N min etter siste deteksjon (tåler «Klar»-glipp) |
| dør lukket | dørsensor | lukket i N min; lavere vekt hvis «døra kan åpnes om natta» |
| vindu åpent | vindussensor | trekker ned |
| puls lav / høy | pulssensor | brukes bare når verdien er fersk |
| i senga | sengesensor | valgfri |

Sannsynligheten regnes bayesiansk. Over terskel i *N* min → sover, under terskel i *N* min → våken.

## Vekkeregler (overstyrer)
- Forlater hjemmet → våken
- Borte fra rommet i *N* min (standard 30) → våken – do-turer er kortere
- Dør åpnes i morgenvinduet → våken umiddelbart, **eller** hvis «døra kan åpnes om natta»: våken når personen har vært borte fra rommet i *N* min etterpå
- Etter en tvungen vekking må sannsynligheten under terskel før «sover» kan settes igjen

## Entiteter
- `binary_sensor.<navn>_sover` – med attributter: sannsynlighet, årsak, alle observasjoner
- `sensor.<navn>_sovn_sannsynlighet` – prosent

## Forslag til oppsett i dette huset
| | Sebastian | Rune | Cybele |
|---|---|---|---|
| sovevindu | 22:00–10:00 | 22:00–10:00 | 19:00–08:00 |
| dør om natta OK | – | nei | ja |
| terskel | 0.8 | 0.8 | 0.75 |
| puls sover/våken | 54 / 65 | – | – |

## Ikon
Ikonet ligger i `brand/ki_sovn/` (`icon.png` 256×256, `icon@2x.png` 512×512, kilde `icon.svg`).

Home Assistant og HACS henter ikoner fra <https://github.com/home-assistant/brands>, ikke fra selve integrasjonen.
For at ikonet skal vises i integrasjonsmenyen og i HACS må det sendes inn dit én gang:

1. Fork `home-assistant/brands`
2. Legg `icon.png` og `icon@2x.png` i `custom_integrations/ki_sovn/`
3. Åpne en PR – etter merge vises ikonet automatisk (cache kan ta noen timer)

Inntil da viser HA et standard-ikon; README-bildet over vises uansett i HACS.
