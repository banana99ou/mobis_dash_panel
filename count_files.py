#!/usr/bin/env python3
"""
[DEBUG util] Count files of a specific type in a directory structure
Generic file counter that can count any file extension in any path
"""

import os
import argparse
from pathlib import Path
from collections import defaultdict

def count_files(base_path, file_type, verbose=False):
    """Count files of specified type by directory structure"""
    # Ensure file_type starts with a dot
    if not file_type.startswith('.'):
        file_type = '.' + file_type
    
    counts = defaultdict(int)
    total = 0
    
    if not os.path.exists(base_path):
        print(f"Error: Path '{base_path}' does not exist")
        return counts, total
    
    print(f"Scanning {file_type} files in: {base_path}")
    if verbose:
        print("=" * 60)
    
    for root, dirs, files in os.walk(base_path):
        matching_files = [f for f in files if f.endswith(file_type)]
        if matching_files:
            rel_path = os.path.relpath(root, base_path)
            counts[rel_path] = len(matching_files)
            total += len(matching_files)
            
            # Show first few files in each directory
            if verbose:
                if len(matching_files) <= 5:
                    print(f"{rel_path}: {len(matching_files)} files")
                    for f in matching_files:
                        print(f"  - {f}")
                else:
                    print(f"{rel_path}: {len(matching_files)} files")
                    for f in matching_files[:3]:
                        print(f"  - {f}")
                    print(f"  ... and {len(matching_files) - 3} more")
    
    print("=" * 60)
    print(f"Total {file_type} files: {total}")
    print(f"Directories with {file_type} files: {len(counts)}")
    
    return counts, total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Count files of a specific type in a directory structure'
    )
    parser.add_argument(
        '--path', '-p',
        type=str,
        required=False,
        help='Base path to search for files',
        default='data/motion_sickness/'
    )
    parser.add_argument(
        '--type', '-t',
        type=str,
        required=False,
        help='File type/extension to count (e.g., "m", ".m", "py", ".py")',
        default='.m'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        required=False,
        help='Show detailed output for each file',
        default=False
    )
    
    args = parser.parse_args()
    count_files(args.path, args.type, args.verbose)


