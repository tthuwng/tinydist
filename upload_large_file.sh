#!/bin/bash

# Usage: ./upload_large_file.sh /path/to/your/large_file

FILE_PATH="$1"
CHUNK_SIZE="5M" # chunk size: 5MB
CATEGORY="model" # default to model
AUTH_TOKEN="${AUTH_TOKEN}"
UPLOAD_URL="http://localhost:5002/upload_chunk"
FILE_NAME=$(basename "$FILE_PATH")
OUTPUT_DIR="/tmp/chunks"
mkdir -p "$OUTPUT_DIR"
SPLIT_PREFIX="${OUTPUT_DIR}/${FILE_NAME}_chunk_"

split -b "$CHUNK_SIZE" -d "$FILE_PATH" "$SPLIT_PREFIX"
TOTAL_CHUNKS=$(find "$OUTPUT_DIR" -name "${FILE_NAME}_chunk_*" | wc -l)

COUNTER=0
for CHUNK in "${OUTPUT_DIR}"/"${FILE_NAME}_chunk_"*; do
    echo "Uploading chunk $((COUNTER + 1)) of $TOTAL_CHUNKS"
    curl -X POST -H "Authorization: $AUTH_TOKEN" \
        -F "file=@${CHUNK}" \
        -F "filename=${FILE_NAME}" \
        -F "chunkIndex=${COUNTER}" \
        -F "totalChunks=${TOTAL_CHUNKS}" \
        -F "category=${CAT}" \
        -F "fileChecksum=${FILE_CHECKSUM}" \
        "$UPLOAD_URL"
    ((COUNTER++))
done

echo "All chunks uploaded. Cleaning up..."
rm -r "$OUTPUT_DIR"
