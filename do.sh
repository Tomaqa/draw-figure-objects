#!/bin/bash

FUNCTION_NAME=python-fu-Mysteria-gen

VERSION=1.10

RESOLUTION=864


gimp-console -b "(${FUNCTION_NAME} RUN-NONINTERACTIVE ${RESOLUTION})" -b '(gimp-quit 0)' || exit

exit 0

cd /media/Data/Obrázky/Hry/Mysteria/v$VERZE/export

for i in `eval echo {0001..$POCET_KARET}`
  do
    `echo "pdfunite" $i{\_lic,\_rub,}.pdf`
  done

rm *_lic.pdf *_rub.pdf
unset POCET_KARET
unset VERZE
cd -
rm pocet
