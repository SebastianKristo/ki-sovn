<p align="center"><img src="icon.png" width="128" alt="KI Søvn & Vekking"></p>

# KI Søvn & Vekking

Én custom integration (domene `ki_sovn`) med to typer oppføringer:

- **Person – søvndeteksjon**: avgjør bayesiansk om en person sover ut fra hjemme/borte, sovevindu, tilstedeværelse, dør, vindu,
  puls og seng, og speiler resultatet i en bryter (Homey `switch.homey_logic_<navn>_sovn_vaken`).
- **Vekkealarm – gradvis lys**: fader lys opp til vekketid per ukedag, med betingelser, nattlampe og kobling til en person.

v2.0.0 erstatter både ki-sovn v1 og [ki-vekking](https://github.com/SebastianKristo/ki-vekking). Eksisterende person-oppføringer
fungerer uendret (samme unique_id og entitets-ID-er).

## Installasjon (HACS)
1. HACS → Integrations → ⋮ → Custom repositories → `https://github.com/SebastianKristo/ki-sovn` (Integration)
2. Installer **KI Søvn & Vekking**, restart HA
3. Innstillinger → Enheter og tjenester → Legg til integrasjon → **KI Søvn & Vekking** → velg type

## Migrering fra ki_vekking
1. Legg til «Vekkealarm» med samme navn (f.eks. `Soverom`), lys og betingelser → entitetene får samme prefiks (`soverom_vekking_*`).
2. Velg person (`binary_sensor.sebastian_sovn_sover`) hvis alarmen skal vekke/hoppe over.
3. Fjern ki_vekking-oppføringen og slett integrasjonen fra HACS.

## Person – entiteter (`<navn>_sovn_*`)
| Entitet | Funksjon |
|---|---|
| `binary_sensor.<navn>_sovn_sover` | on = sover. Attributter: `sannsynlighet`, `årsak`, `venter_på`, `siden`, `obs_*`, `prefix`, `bryter` |
| `sensor.<navn>_sovn_sannsynlighet` | prosent |
| `button.<navn>_sovn_sett_sover` / `_sett_vaken` | manuell overstyring (skriver til bryteren med en gang) |
| `number.<navn>_sovn_terskel`, `_forsinkelse_sovner`, `_forsinkelse_vakner`, `_hold_i_rommet`, `_borte_fra_rommet_vaken`, `_dor_lukket_i`, `_dorlas_bekreft`, `_puls_sover`, `_puls_vaken` | innstillinger, endres uten reload |
| `switch.<navn>_sovn_dorlas` | dørlåsen på/av (standard på) |
| `time.<navn>_sovn_sovevindu_start` / `_slutt` / `_morgen_fra` | tider |
| `switch.<navn>_sovn_automatisk`, `_dor_om_natta_ok` | styring av bryteren / do-turer |

### Dørlås – presence som mister personen
Tilstedeværelsessensorer slutter ofte å se en person som ligger stille. Dørlåsen bruker døra som
sannhetsvitne i stedet:

- Var noen registrert i rommet (nå, eller innen `dorlas_bekreft` minutter) idet **døra ble lukket**,
  er personen inne. Låsen settes.
- Mens låsen står, betyr presence som faller ut bare at sensoren mistet personen. «I rommet» holdes
  sann, får litt høyere vekt i beregningen, og regelen «borte fra rommet i N min» kan ikke vekke noen.
- Låsen slippes først når **døra faktisk åpnes** – da bestemmer presence igjen, og nedtellingen for
  «borte fra rommet» starter tidligst ved døråpningen.
- Åpnes døra en liten stund mens personen sover (do-tur) og lukkes igjen innen
  `borte_fra_rommet_vaken` minutter, settes låsen på nytt selv om presence ikke rakk å se hen komme
  tilbake i senga.
- Forsvinner personen fra huset, slippes låsen.

Attributtene på `binary_sensor.<navn>_sovn_sover` viser `dorlas_aktiv`, `dorlas_siden` og
`obs_i_rommet_kilde` (`sensor`, `dørlås` eller `hysterese`), så det er lett å se hva som holder
«i rommet» oppe. Slå av med `switch.<navn>_sovn_dorlas` hvis du heller vil stole blindt på sensoren.

Vekkeregler: forlater hjemmet → våken; borte fra rommet i N min → våken; dør åpnes i morgenvinduet → våken (eller etter N min borte
hvis «dør om natta OK»); vekkealarm med «Vekk person» → våken når lyset er oppe.

## Vekkealarm – entiteter (`<navn>_vekking_*`)
| Entitet | Funksjon |
|---|---|
| `switch.<navn>_vekking_aktiv` | hovedbryter |
| `switch.<navn>_vekking_<dag>_aktiv`, `time.<navn>_vekking_<dag>` | dag på/av og vekketid (mandag … sondag) |
| `number.<navn>_vekking_fade_opp`, `_av_etter` | minutter |
| `switch.<navn>_vekking_nattlampe` | ta med nattlampen |
| `switch.<navn>_vekking_vekk_person` | marker personen som våken når fade er ferdig (standard på) |
| `switch.<navn>_vekking_bare_hvis_sover` | hopp over alarmen hvis personen er våken (standard av) |
| `sensor.<navn>_vekking_neste_alarm` | HH:MM / Av. Attributter: `neste_dag`, `betingelser_ok`, `hopper_over`, `person_sover`, `lys`, `sist_kjort`, `sist_hoppet_over` |
| `binary_sensor.<navn>_vekking_kjorer` | sekvens kjører (`fase`: fader / lyser) |
| `button.<navn>_vekking_test` / `_stopp` | kjør nå (uavhengig av betingelser) / avbryt og slukk |

Sekvens: lys til startlysstyrke → fade til 100 % over *fade opp* min → (vekk person) → vent *av etter* min → slukk.

## Kort
[ki-cards](https://github.com/SebastianKristo/ki-cards) v2: `ki-sovn-card` og `ki-vekking-card` finner entitetene selv via
attributtet `integrasjon: ki_sovn`.

## Ikon
`brand/ki_sovn/` sendes til `home-assistant/brands` under `custom_integrations/ki_sovn/`.
