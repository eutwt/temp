#!/bin/bash

# Print header
echo "Available colors with tput setaf:"
echo "================================"

# Reset formatting
reset=$(tput sgr0)

# Try colors from 0 to 255
for i in {0..255}; do
    # Try to set the color and capture any errors
    if color=$(tput setaf $i 2>/dev/null); then
        # Print color number and sample text
        printf "Color %3d: ${color}This is color %d${reset}\n" $i $i
    fi
done

# Reset terminal colors
echo "${reset}"
