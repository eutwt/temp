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
        for root, dirs, files in os.walk(directory, followlinks=False):
            for name in files:
                try:
                    file_path = Path(root) / name
                    if not file_path.is_symlink():
                        total_size += file_path.stat().st_size
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        pass
    return total_size

def analyze_directories(start_path: str = '.') -> List[Tuple[str, int]]:
    """
    Analyze all directories recursively and return list of (path, size) tuples.
    """
    directory_sizes = []
    start_path = Path(start_path).resolve()
    
    # Walk through directories using os.walk
    for root, dirs, _ in os.walk(start_path, followlinks=False):
        # Remove hidden directories from dirs list in-place
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for dir_name in dirs:
            try:
                dir_path = Path(root) / dir_name
                if not dir_path.is_symlink():
                    size = get_directory_size(dir_path)
                    directory_sizes.append((str(dir_path), size))
            except (PermissionError, OSError):
                continue
    
    # Add the start directory itself
    if not start_path.parts[-1].startswith('.') and not start_path.is_symlink():
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
    
    try:
        # Get and display directory sizes
        directory_sizes = analyze_directories(args.path)
        base_path = Path(args.path).resolve()
        
        for path, size in directory_sizes:
            if size < min_bytes:
                continue
                
            # Calculate directory depth relative to start path
            try:
                rel_path = Path(path).relative_to(base_path.parent)
                depth = len(rel_path.parts) - 1
            except ValueError:
                # Handle case where path is not relative to base_path
                depth = 0
            
            indent = "  " * depth
            print(f"{indent}{get_human_readable_size(size):<10} {path}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()