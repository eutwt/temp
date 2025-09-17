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
        exclude_dirs: List of subdirectory names or paths to exclude
                     Can be:
                     - Simple names: "node_modules", ".git"
                     - Relative paths: "src/temp", "data/cache"
                     - Absolute paths: "/home/user/project/temp"
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
    
    # Process exclude list to handle both absolute and relative paths
    processed_excludes = _process_exclude_list(exclude_dirs, source_dir)
    
    # Check if rsync is available
    if use_rsync and shutil.which('rsync'):
        return _copy_with_rsync(source_dir, dest_dir, processed_excludes, verbose)
    else:
        if use_rsync:
            print("rsync not found, falling back to cp command...")
        return _copy_with_cp(source_dir, dest_dir, processed_excludes, verbose)


def _process_exclude_list(exclude_dirs: List[str], source_dir: str) -> List[str]:
    """
    Process exclude list to handle absolute paths, relative paths, and simple names.
    Returns a list suitable for rsync exclusion patterns.
    """
    processed = []
    source_dir = os.path.abspath(source_dir)
    
    for exclude in exclude_dirs:
        exclude = exclude.strip()
        if not exclude:
            continue
            
        # Check if it's an absolute path
        if os.path.isabs(exclude):
            # Convert absolute path to relative to source
            try:
                rel_path = os.path.relpath(exclude, source_dir)
                # Only include if it's actually inside the source directory
                if not rel_path.startswith('..'):
                    processed.append(rel_path)
                else:
                    print(f"Warning: Exclude path '{exclude}' is outside source directory, skipping")
            except ValueError:
                print(f"Warning: Cannot process exclude path '{exclude}', skipping")
        else:
            # It's already a relative path or simple name
            processed.append(exclude)
    
    return processed


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
            
            # Handle both simple names and paths
            if '/' in exclude:
                # It's a path - use full path matching
                full_exclude_path = os.path.join(source_dir, exclude)
                find_cmd.extend(['-path', full_exclude_path, '-prune'])
            else:
                # It's a simple name - match anywhere
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
    path = os.path.abspath(path)
    
    for dirpath, dirnames, filenames in os.walk(path):
        # Check if current directory should be excluded
        rel_dir = os.path.relpath(dirpath, path)
        
        # Remove excluded directories from dirnames to prevent walking into them
        new_dirnames = []
        for dirname in dirnames:
            # Check against all exclusion patterns
            should_exclude = False
            dir_rel_path = os.path.join(rel_dir, dirname) if rel_dir != '.' else dirname
            
            for exclude in exclude_dirs:
                if '/' in exclude:
                    # Path-based exclusion
                    if dir_rel_path == exclude or dir_rel_path.startswith(exclude + '/'):
                        should_exclude = True
                        break
                else:
                    # Name-based exclusion
                    if dirname == exclude:
                        should_exclude = True
                        break
            
            if not should_exclude:
                new_dirnames.append(dirname)
        
        dirnames[:] = new_dirnames
        
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
    
    # List of subdirectories to exclude - now supports multiple formats
    exclude_list = [
        # Simple folder names (excluded anywhere in tree)
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        
        # Relative paths (excluded at specific locations)
        "src/temp",
        "data/cache",
        "build/intermediate",
        
        # Absolute paths (will be converted to relative)
        "/path/to/source/specific/folder/to/exclude",
        "/path/to/source/another/specific/path"
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
