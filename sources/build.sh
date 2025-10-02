#!/bin/sh
set -e

echo "Build Headline"

gftools builder config-headline.yaml

echo "Build Text"

gftools builder config-text.yaml

echo "Complete"
