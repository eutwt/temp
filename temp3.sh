#!/bin/bash

# Function to convert sizes to human readable format
human_readable() {
    local size=$1
    local units=('B' 'K' 'M' 'G' 'T' 'P')
    local unit_index=0
    
    while (( size > 1024 )); do
        size=$(( size / 1024 ))
        unit_index=$(( unit_index + 1 ))
    done
    
    echo "$size${units[$unit_index]}"
}

# Create a temporary file to store results
temp_file=$(mktemp)

# Find all directories and calculate their sizes
find "${1:-.}" -type d -print0 | while IFS= read -r -d '' dir; do
    # Skip hidden directories
    [[ $(basename "$dir") == .* ]] && continue
    
    # Calculate total size of directory
    size=$(du -sb "$dir" 2>/dev/null | cut -f1)
    
    # Skip if size calculation failed
    [[ -z "$size" ]] && continue
    
    # Store size and path in temporary file
    echo -e "$size\t$dir" >> "$temp_file"
done

# Sort results by size (largest first) and display
echo "Directory Size Analysis (Largest to Smallest):"
echo "----------------------------------------"
sort -rn "$temp_file" | while IFS=$'\t' read -r size path; do
    # Convert to human readable format
    readable_size=$(human_readable "$size")
    # Calculate directory depth
    depth=$(echo "$path" | tr -cd '/' | wc -c)
    # Create indent based on depth
    indent=$(printf '%*s' "$((depth*2))" '')
    
    echo "${indent}${readable_size}  ${path}"
done

# Clean up temporary file
rm "$temp_file"