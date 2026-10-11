#!/usr/bin/env sh
# Download the Hillstrom (MineThatData, 2008) e-mail experiment into data/.
# About 4 MB. Published by Kevin Hillstrom for an open analytics challenge; no
# licence is stated, so the file is not redistributed in this repository.
set -eu

DEST="data/hillstrom.csv"
URL="http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"

if [ -f "$DEST" ]; then
    echo "dataset present: $DEST"
    exit 0
fi
echo "downloading $URL"
curl -fsSL -o "$DEST" "$URL"
echo "saved $DEST"
