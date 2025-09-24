#!/usr/bin/env python3
"""
Copy NAS Resampled Data to Local Ingest Folder

This script copies only the resampled folders from each week folder on the NAS 
to the local data/ingest folder, excluding zip files and video files to save 
space and focus on CSV data.

Usage:
  python3 copy_nas_data.py [--dry-run] [--verbose]
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import Set, List
import time

# File extensions to exclude
EXCLUDED_EXTENSIONS = {
    '.zip', '.avi', '.mp4', '.mov', '.mkv', '.wmv', '.flv', '.webm',
    '.ZIP', '.AVI', '.MP4', '.MOV', '.MKV', '.WMV', '.FLV', '.WEBM',
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif',  # Image files
    '.JPG', '.JPEG', '.PNG', '.BMP', '.TIFF', '.GIF'
}

# File patterns to exclude (partial matches)
EXCLUDED_PATTERNS = {
    '._',  # macOS metadata files
    '.DS_Store'  # macOS system files
}

def should_exclude_file(file_path: Path) -> bool:
    """Check if a file should be excluded from copying"""
    # Check file extension
    if file_path.suffix in EXCLUDED_EXTENSIONS:
        return True
    
    # Check file name patterns
    file_name = file_path.name
    for pattern in EXCLUDED_PATTERNS:
        if pattern in file_name:
            return True
    
    return False

def copy_resampled_folders(src: Path, dst: Path, dry_run: bool = False, verbose: bool = False) -> tuple[int, int, int]:
    """
    Copy only resampled folders from src to dst, excluding specified files
    Returns (files_copied, files_excluded, dirs_created)
    """
    files_copied = 0
    files_excluded = 0
    dirs_created = 0
    
    # Create destination directory if it doesn't exist
    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)
    else:
        if verbose:
            print(f"[DRY-RUN] Would create directory: {dst}")
    
    # Process all items in source directory
    try:
        for item in src.iterdir():
            src_path = item
            dst_path = dst / item.name
            
            if item.is_dir():
                # Check if this is a resampled directory
                if item.name == "resampled":
                    # Copy the entire resampled directory
                    sub_files, sub_excluded, sub_dirs = copy_directory_contents(
                        src_path, dst_path, dry_run, verbose
                    )
                    files_copied += sub_files
                    files_excluded += sub_excluded
                    dirs_created += sub_dirs + 1
                else:
                    # Recursively search for resampled directories in subdirectories
                    sub_files, sub_excluded, sub_dirs = copy_resampled_folders(
                        src_path, dst_path, dry_run, verbose
                    )
                    files_copied += sub_files
                    files_excluded += sub_excluded
                    dirs_created += sub_dirs
                
            elif item.is_file():
                if should_exclude_file(item):
                    files_excluded += 1
                    if verbose:
                        print(f"[EXCLUDE] {item.relative_to(src.parent)}")
                else:
                    files_copied += 1
                    if dry_run:
                        if verbose:
                            print(f"[DRY-RUN] Would copy: {item.relative_to(src.parent)} -> {dst_path.relative_to(dst.parent)}")
                    else:
                        try:
                            shutil.copy2(src_path, dst_path)
                            if verbose:
                                print(f"[COPY] {item.relative_to(src.parent)}")
                        except Exception as e:
                            print(f"[ERROR] Failed to copy {item}: {e}")
                            files_copied -= 1
                            files_excluded += 1
            else:
                # Handle symlinks or other file types
                if verbose:
                    print(f"[SKIP] {item.relative_to(src.parent)} (not a regular file/directory)")
    
    except PermissionError as e:
        print(f"[ERROR] Permission denied accessing {src}: {e}")
    except Exception as e:
        print(f"[ERROR] Error processing {src}: {e}")
    
    return files_copied, files_excluded, dirs_created

def copy_directory_contents(src: Path, dst: Path, dry_run: bool = False, verbose: bool = False) -> tuple[int, int, int]:
    """
    Copy all contents of a directory, excluding specified files
    Returns (files_copied, files_excluded, dirs_created)
    """
    files_copied = 0
    files_excluded = 0
    dirs_created = 0
    
    # Create destination directory if it doesn't exist
    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)
    else:
        if verbose:
            print(f"[DRY-RUN] Would create directory: {dst}")
    
    # Process all items in source directory
    try:
        items = list(src.iterdir())
        for item in items:
            src_path = item
            dst_path = dst / item.name
            
            if item.is_dir():
                # Skip frames directories to avoid copying thousands of images
                if item.name == "frames":
                    if verbose:
                        print(f"[SKIP] {item.relative_to(src.parent)} (frames directory - too many files)")
                    continue
                
                # Recursively copy subdirectories
                sub_files, sub_excluded, sub_dirs = copy_directory_contents(
                    src_path, dst_path, dry_run, verbose
                )
                files_copied += sub_files
                files_excluded += sub_excluded
                dirs_created += sub_dirs + 1
                
            elif item.is_file():
                if should_exclude_file(item):
                    files_excluded += 1
                    if verbose:
                        print(f"[EXCLUDE] {item.relative_to(src.parent)}")
                else:
                    files_copied += 1
                    if dry_run:
                        if verbose:
                            print(f"[DRY-RUN] Would copy: {item.relative_to(src.parent)} -> {dst_path.relative_to(dst.parent)}")
                    else:
                        try:
                            shutil.copy2(src_path, dst_path)
                            if verbose:
                                print(f"[COPY] {item.relative_to(src.parent)}")
                        except Exception as e:
                            print(f"[ERROR] Failed to copy {item}: {e}")
                            files_copied -= 1
                            files_excluded += 1
            else:
                # Handle symlinks or other file types
                if verbose:
                    print(f"[SKIP] {item.relative_to(src.parent)} (not a regular file/directory)")
    
    except PermissionError as e:
        print(f"[ERROR] Permission denied accessing {src}: {e}")
    except Exception as e:
        print(f"[ERROR] Error processing {src}: {e}")
    
    return files_copied, files_excluded, dirs_created

def copy_nas_data_to_ingest(nas_path: str, ingest_path: str, dry_run: bool = False, verbose: bool = False):
    """Copy only resampled folders from each week folder on NAS to local ingest directory"""
    
    nas_root = Path(nas_path)
    ingest_root = Path(ingest_path)
    
    if not nas_root.exists():
        print(f"❌ Error: NAS path does not exist: {nas_root}")
        return
    
    print("=" * 80)
    print("📁 NAS RESAMPLED DATA COPY TO INGEST")
    print("=" * 80)
    print(f"📂 Source: {nas_root}")
    print(f"📂 Destination: {ingest_root}")
    print(f"🔧 Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"📁 Copying: Only resampled folders from each week")
    print(f"🚫 Excluding: {', '.join(EXCLUDED_EXTENSIONS)} files")
    print()
    
    # Find all week folders
    week_folders = []
    for week_num in range(4):
        week_folder = f"week{week_num}"
        week_path = nas_root / week_folder
        if week_path.exists() and week_path.is_dir():
            week_folders.append(week_folder)
    
    if not week_folders:
        print("❌ No week folders found in NAS directory")
        return
    
    print(f"📊 Found {len(week_folders)} week folders: {', '.join(week_folders)}")
    print()
    
    total_files_copied = 0
    total_files_excluded = 0
    total_dirs_created = 0
    
    # Copy each week folder
    for week_folder in week_folders:
        print(f"📅 Processing: {week_folder}")
        print("-" * 50)
        
        src_week = nas_root / week_folder
        dst_week = ingest_root / week_folder
        
        start_time = time.time()
        files_copied, files_excluded, dirs_created = copy_resampled_folders(
            src_week, dst_week, dry_run, verbose
        )
        end_time = time.time()
        
        total_files_copied += files_copied
        total_files_excluded += files_excluded
        total_dirs_created += dirs_created
        
        print(f"   📄 Files copied: {files_copied}")
        print(f"   🚫 Files excluded: {files_excluded}")
        print(f"   📁 Directories created: {dirs_created}")
        print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
        print()
    
    # Summary
    print("=" * 80)
    print("📊 COPY SUMMARY")
    print("=" * 80)
    print(f"📄 Total files copied: {total_files_copied}")
    print(f"🚫 Total files excluded: {total_files_excluded}")
    print(f"📁 Total directories created: {total_dirs_created}")
    print(f"💾 Total files processed: {total_files_copied + total_files_excluded}")
    
    if dry_run:
        print("\n🔍 Dry-run mode: no changes made.")
        print("Run without --dry-run to execute the copy operation.")
    else:
        print("\n✅ Copy operation completed!")
    
    return total_files_copied, total_files_excluded, total_dirs_created

def main():
    parser = argparse.ArgumentParser(description="Copy only resampled folders from NAS to local ingest folder, excluding zip and video files.")
    parser.add_argument("--nas-path", "-n", 
                       default="/Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data",
                       help="Path to the NAS Experiment Data directory")
    parser.add_argument("--ingest-path", "-i",
                       default="./data/ingest",
                       help="Path to the local ingest directory")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be copied without actually copying")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed output for each file")
    args = parser.parse_args()
    
    # Convert to absolute paths
    nas_path = os.path.abspath(args.nas_path)
    ingest_path = os.path.abspath(args.ingest_path)
    
    try:
        copy_nas_data_to_ingest(nas_path, ingest_path, args.dry_run, args.verbose)
    except KeyboardInterrupt:
        print("\n⚠️  Copy operation interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Error during copy operation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
