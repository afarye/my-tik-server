#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <path-to-image-tar>"
  exit 2
fi

IMG_TAR="$1"

echo "Loading image from: $IMG_TAR"
docker load -i "$IMG_TAR"
echo "Image loaded. You can run it with:" 
echo "  docker run -p 8000:8000 tik-server:latest"
