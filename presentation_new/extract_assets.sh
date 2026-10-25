#!/bin/sh
# Re-extract the thirteen report figures from report/main.pdf into assets/.
# PNGs are gitignored (as they are for report/figures/), so run this once after a fresh clone,
# then: cd src && npm install && node build_deck.js
# Order below is the order the figures appear in the PDF (pdfimages emits an image and its mask
# alternately, so the figure for slot k is raw-(2k).png). The first slot is the Monash logo on the title page.
set -e
cd "$(dirname "$0")"
mkdir -p assets
pdfimages -png ../report/main.pdf assets/raw
i=2
for name in fig3_1_coverage fig3_2_series fig3_3_periodogram fig3_4_weekly fig3_5_annual \
            fig3_6_arima_stability fig4_1_accuracy fig4_2_predictions fig4_3_weather \
            fig4_4_arms fig4_5_tradeoff fig5_1_sensitivity fig5_2_architectures; do
  mv "assets/raw-$(printf '%03d' $i).png" "assets/$name.png"
  i=$((i + 2))
done
rm -f assets/raw-*.png
cp ../report/figures/monash-logo.png ../report/figures/monash-logo-stacked.png assets/
echo "assets ready"
