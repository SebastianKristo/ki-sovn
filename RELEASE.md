# KI Søvn & Vekking 2.2.0

## Åpent vindu trakk søvnen ned hele natten

I den bayesianske utregningen har `vindu_apent` vektene `(0.15, 0.30)`. Et åpent vindu
regnes altså som mer enn dobbelt så sannsynlig når man er våken som når man sover, og
halverer oddsen hver eneste gang det står åpent.

Det er en rimelig antakelse for et vindu som åpnes fordi noen er oppe. Det er en dårlig
antakelse for en som sover med vinduet åpent året rundt — da ligger den samme straffen
på hele natten, og sannsynligheten kommer kanskje aldri over terskelen.

Ny bryter per person: **Vindu teller**. Slå den av, så holdes vindusobservasjonen utenfor
regnestykket. Den vises fortsatt i observasjonslista og som merke på kortet, så du ser
at vinduet står åpent — den teller bare ikke imot.

Standard er på, så ingenting endrer seg før du velger.
