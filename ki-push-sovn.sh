#!/bin/bash
# Bruk: bash ~/ki-push-sovn.sh 2.2.0
set -e
V=$1
[ -z "$V" ] && { echo "Bruk: ki-push-sovn.sh 2.2.0"; exit 1; }
REPO=~/Documents/HomeAssistant/ki-sovn
U=${V//./_}                      # 2.2.0 -> 2_2_0

cd ~/Downloads
ZIP=""
for kandidat in "ki-sovn-$V.zip" "ki-sovn-$U.zip"; do
  [ -f "$kandidat" ] && ZIP="$kandidat" && break
done
[ -z "$ZIP" ] && { echo "Fant ingen ki-sovn-$V.zip eller ki-sovn-$U.zip i ~/Downloads"; exit 1; }

rm -rf "ki-sovn-$V" && unzip -oq "$ZIP" -d "ki-sovn-$V"

KILDE="ki-sovn-$V"
[ -d "$KILDE/ki-sovn" ] && KILDE="$KILDE/ki-sovn"
[ -d "$KILDE/custom_components" ] || { echo "Fant ingen custom_components i pakka"; exit 1; }

[ -d "$REPO/.git" ] || git clone -q https://github.com/SebastianKristo/ki-sovn.git "$REPO"
cp -r "$KILDE/." "$REPO/"
cd "$REPO"
perl -pi -e "s/\"version\": \"[^\"]*\"/\"version\": \"$V\"/" custom_components/ki_sovn/manifest.json
git add .
git commit -m "KI Søvn & Vekking v$V" || true
git push origin main
git tag -f "v$V" && git push -f origin "v$V"

NOTAT=""
[ -f RELEASE.md ] && NOTAT="--notes-file RELEASE.md"
if gh release view "v$V" >/dev/null 2>&1; then
  gh release edit "v$V" $NOTAT
  echo "Ferdig. Release v$V oppdatert."
else
  gh release create "v$V" --title "v$V" $NOTAT
  echo "Ferdig. Release v$V opprettet."
fi
