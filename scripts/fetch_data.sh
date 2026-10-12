#!/usr/bin/env sh
# Download the Hillstrom (MineThatData, 2008) e-mail experiment into data/.
# About 4 MB. Published by Kevin Hillstrom for an open analytics challenge; no
# licence is stated, so the file is not redistributed in this repository.
#
# The publisher serves it over plain HTTP only, so the download is checked
# against the SHA-256 of the copy analysed in evidence/hillstrom/. It goes to a
# temporary file first: an interrupted or altered download never ends up at
# data/hillstrom.csv, where later runs would treat it as present.
set -eu

DEST="data/hillstrom.csv"
URL="http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
SHA256="0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece"

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d' ' -f1
    else
        shasum -a 256 "$1" | cut -d' ' -f1  # macOS
    fi
}

if [ -f "$DEST" ]; then
    if [ "$(sha256_of "$DEST")" = "$SHA256" ]; then
        echo "dataset present and verified: $DEST"
        exit 0
    fi
    echo "$DEST exists but its SHA-256 does not match; delete it and run make data again" >&2
    exit 1
fi

tmp="$DEST.part"
trap 'rm -f "$tmp"' EXIT
echo "downloading $URL"
curl -fsSL -o "$tmp" "$URL"
actual="$(sha256_of "$tmp")"
if [ "$actual" != "$SHA256" ]; then
    echo "SHA-256 mismatch: expected $SHA256, got $actual" >&2
    exit 1
fi
mv "$tmp" "$DEST"
echo "saved and verified $DEST"
