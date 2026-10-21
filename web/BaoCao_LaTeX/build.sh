#!/bin/bash
# Biên dịch báo cáo trên máy: bash build.sh  -> ra main.pdf
cd "$(dirname "$0")"
xelatex -interaction=nonstopmode main.tex > /dev/null
biber main > /dev/null
xelatex -interaction=nonstopmode main.tex > /dev/null
xelatex -interaction=nonstopmode main.tex > build.log
if grep -q '^!' build.log; then
  echo "CO LOI:"; grep -A3 '^!' build.log
else
  echo "Xong, 0 loi -> main.pdf ($(pdfinfo main.pdf | grep Pages))"
fi
rm -f *.aux *.bbl *.bcf *.blg *.run.xml *.toc *.out
