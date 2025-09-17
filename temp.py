#!/usr/bin/env python3
"""
Efficiently copy a directory tree while excluding certain subdirectories.
Uses rsync for efficient copying with progress reporting.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


def copy_directory_with_exclusions(
    source_dir: str,
    dest_dir: str,
    exclude_dirs: List[str],
    use_rsync: bool = True,
    verbose: bool = True
) -> bool:
    """
    Copy a directory recursively while excluding certain subdirectories.
    
    Args:
        source_dir: Source directory path
        dest_dir: Destination directory path
        exclude_dirs: List of subdirectory names to exclude
        use_rsync: Use rsync if available (more efficient)
        verbose: Show progress information
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Convert to absolute paths
    source_dir = os.path.abspath(source_dir)
    dest_dir = os.path.abspath(dest_dir)
    
    # Validate source directory
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return False
    
    if not os.path.isdir(source_dir):
        print(f"Error: '{source_dir}' is not a directory.")
        return False
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Check if rsync is available
    if use_rsync and shutil.which('rsync'):
        return _copy_with_rsync(source_dir, dest_dir, exclude_dirs, verbose)
    else:
        if use_rsync:
            print("rsync not found, falling back to cp command...")
        return _copy_with_cp(source_dir, dest_dir, exclude_dirs, verbose)


def _copy_with_rsync(
    source_dir: str,
    dest_dir: str,
    exclude_dirs: List[str],
    verbose: bool
) -> bool:
    """Copy using rsync command for efficiency and progress reporting."""
    # Build rsync command
    cmd = ['rsync', '-av']  # -a for archive mode, -v for verbose
    
    if verbose:
        cmd.append('--progress')  # Show progress for each file
        cmd.append('--info=progress2')  # Show overall progress
    
    # Add exclusions
    for exclude in exclude_dirs:
        cmd.extend(['--exclude', exclude])
    
    # Add source and destination
    # Important: Add trailing slash to source to copy contents, not the directory itself
    cmd.extend([f"{source_dir}/", dest_dir])
    
    print(f"Copying from '{source_dir}' to '{dest_dir}'...")
    if exclude_dirs:
        print(f"Excluding: {', '.join(exclude_dirs)}")
    print("-" * 50)
    
    try:
        # Run rsync
        result = subprocess.run(cmd, check=True, text=True)
        print("\nCopy completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError during rsync: {e}")
        return False
    except KeyboardInterrupt:
        print("\nCopy interrupted by user.")
        return False


def _copy_with_cp(
    source_dir: str,
    dest_dir: str,
    exclude_dirs: List[str],
    verbose: bool
) -> bool:
    """Fallback method using cp command with find for exclusions."""
    print(f"Copying from '{source_dir}' to '{dest_dir}'...")
    if exclude_dirs:
        print(f"Excluding: {', '.join(exclude_dirs)}")
    print("-" * 50)
    
    # First, get total size for progress estimation
    if verbose:
        total_size = _get_directory_size(source_dir, exclude_dirs)
        print(f"Total size to copy: {_format_bytes(total_size)}")
        copied_size = 0
    
    # Build find command to list files excluding certain directories
    find_cmd = ['find', source_dir]
    
    # Add exclusions to find command
    if exclude_dirs:
        find_cmd.append('(')
        for i, exclude in enumerate(exclude_dirs):
            if i > 0:
                find_cmd.append('-o')
            find_cmd.extend(['-name', exclude, '-prune'])
        find_cmd.append(')')
        find_cmd.append('-o')
    
    find_cmd.extend(['-type', 'f', '-print'])
    
    try:
        # Get list of files to copy
        result = subprocess.run(find_cmd, capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        files = [f for f in files if f]  # Remove empty strings
        
        total_files = len(files)
        print(f"Found {total_files} files to copy\n")
        
        # Copy each file
        for i, file_path in enumerate(files):
            # Calculate relative path
            rel_path = os.path.relpath(file_path, source_dir)
            dest_path = os.path.join(dest_dir, rel_path)
            
            # Create destination directory
            dest_file_dir = os.path.dirname(dest_path)
            os.makedirs(dest_file_dir, exist_ok=True)
            
            # Copy file
            subprocess.run(['cp', '-p', file_path, dest_path], check=True)
            
            if verbose:
                # Show progress
                file_size = os.path.getsize(file_path)
                copied_size += file_size
                progress = (i + 1) / total_files * 100
                size_progress = copied_size / total_size * 100 if total_size > 0 else 0
                
                print(f"\rProgress: {i+1}/{total_files} files ({progress:.1f}%) | "
                      f"{_format_bytes(copied_size)}/{_format_bytes(total_size)} ({size_progress:.1f}%)", 
                      end='', flush=True)
        
        print("\n\nCopy completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\nError during copy: {e}")
        return False
    except KeyboardInterrupt:
        print("\nCopy interrupted by user.")
        return False


def _get_directory_size(path: str, exclude_dirs: List[str]) -> int:
    """Calculate total size of directory excluding certain subdirectories."""
    total_size = 0
    
    for dirpath, dirnames, filenames in os.walk(path):
        # Remove excluded directories from dirnames to prevent walking into them
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, IOError):
                pass
    
    return total_size


def _format_bytes(size: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


# Example usage
if __name__ == "__main__":
    # Example configuration
    source_directory = "/path/to/source"
    destination_directory = "/path/to/destination"
    
    # List of subdirectories to exclude
    exclude_list = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "build",
        "dist",
        "*.egg-info"
    ]
    
    # Perform the copy
    success = copy_directory_with_exclusions(
        source_dir=source_directory,
        dest_dir=destination_directory,
        exclude_dirs=exclude_list,
        use_rsync=True,  # Prefer rsync if available
        verbose=True      # Show progress
    )
    
    sys.exit(0 if success else 1)
