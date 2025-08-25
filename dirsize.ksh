#!/bin/ksh

# Find biggest directories with max depth
MAX_DEPTH=2

echo "Finding biggest directories (max depth: $MAX_DEPTH)..."
echo "Size (MB)    Directory"
echo "=========    ========="

# Find directories up to MAX_DEPTH and get their sizes
find . -type d -maxdepth $MAX_DEPTH 2>/dev/null | \
    while read dir; do
        size=$(du -xsm "$dir" 2>/dev/null | cut -f1)
        echo "$size $dir"
    done | \
    sort -rn | \
    head -10 | \
    while read size dir; do
        printf "%8d MB  %s\n" "$size" "$dir"
    done
