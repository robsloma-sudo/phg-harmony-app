#!/usr/bin/env bash
# Re-render every panel menu into ../out/panel/<menu>/current (used before each review round).
set -e
cd "$(dirname "$0")/../tools"
node run.mjs --transcript-file ../examples/sample-bar.voice.txt --venue-type cocktail_lounge --city Denver --state CO --zip 80211 \
  --standards ../examples/classic-specs.json ${SAMPLE_BAR_EXTRA:-} --out ../out/panel/sample-bar/current > /dev/null
node run.mjs --transcript-file ../examples/casa-luna.voice.txt --venue-type latin_cantina --city Denver --state CO --zip 80205 \
  --demographics ../examples/denver-80205.census.json --comparables ../examples/denver-cantina.refs.json \
  --standards ../examples/classic-specs.json ${CASA_LUNA_EXTRA:-} --out ../out/panel/casa-luna/current > /dev/null
node run.mjs --transcript-file ../examples/high-altitude.voice.txt --venue-type brewery --city "Fort Collins" --state CO --zip 80524 \
  --demographics ../examples/fort-collins-80524.census.json --standards ../examples/classic-specs.json ${HIGH_ALTITUDE_EXTRA:-} \
  --out ../out/panel/high-altitude/current > /dev/null
for m in sample-bar casa-luna high-altitude; do
  echo "$m: $(sed -n 2p ../out/panel/$m/current/SUMMARY.md | cut -c1-120) | $(ls ../out/panel/$m/current/option-A/page-*.png | wc -l) page(s)"
done
