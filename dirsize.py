#!/usr/bin/env python3

import os
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def get_directory_size(directory: Path) -> int:
    """Calculate total size of a directory and its subdirectories."""
    total_size = 0
    try:
        for path in directory.rglob('*'):
            if path.is_file() and not path.is_symlink():
                total_size += path.stat().st_size
    except (PermissionError, OSError):
        pass  # Skip directories we can't access
    return total_size

def analyze_directories(start_path: str = '.') -> List[Tuple[str, int]]:
    """
    Analyze all directories recursively and return list of (path, size) tuples.
    """
    directory_sizes = []
    start_path = Path(start_path).resolve()
    
    # Get all directories recursively
    for directory in [x for x in start_path.rglob('*') if x.is_dir()]:
        try:
            # Skip hidden directories
            if any(part.startswith('.') for part in directory.parts):
                continue
                
            size = get_directory_size(directory)
            directory_sizes.append((str(directory), size))
        except (PermissionError, OSError):
            continue
            
    # Add the start directory itself
    if not start_path.parts[-1].startswith('.'):
        size = get_directory_size(start_path)
        directory_sizes.append((str(start_path), size))
    
    # Sort by size (largest first)
    return sorted(directory_sizes, key=lambda x: x[1], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Analyze directory sizes recursively')
    parser.add_argument('path', nargs='?', default='.',
                      help='Path to analyze (default: current directory)')
    parser.add_argument('-m', '--min-size', type=float, default=0,
                      help='Minimum size in MB to display (default: 0)')
    args = parser.parse_args()

    print("\nDirectory Size Analysis (Largest to Smallest):")
    print("-" * 50)

    # Convert minimum size to bytes
    min_bytes = int(args.min_size * 1024 * 1024)
    
    # Get and display directory sizes
    directory_sizes = analyze_directories(args.path)
    base_path = Path(args.path).resolve()
    
    for path, size in directory_sizes:
        if size < min_bytes:
            continue
            
        # Calculate directory depth relative to start path
        rel_path = Path(path).relative_to(base_path.parent)
        depth = len(rel_path.parts) - 1
        indent = "  " * depth
        
        # Display size and path
        print(f"{indent}{get_human_readable_size(size):<10} {path}")

if __name__ == "__main__":
    main()