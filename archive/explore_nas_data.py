#!/usr/bin/env python3
"""
NAS Data Explorer
Scans the mounted NAS folder and prints out all experiment files
"""

import os
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

def explore_nas_data(nas_path: str = "/Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data"):
    """
    Explore the mounted NAS folder and print out all experiment files
    
    Args:
        nas_path: Path to the mounted NAS folder
    """
    print("=" * 80)
    print("🔍 NAS DATA EXPLORER")
    print("=" * 80)
    print(f"📁 Scanning: {nas_path}")
    print()
    
    # Check if path exists
    if not os.path.exists(nas_path):
        print(f"❌ Error: Path does not exist: {nas_path}")
        print("Please check if the NAS is properly mounted.")
        print()
        print("🔧 MOUNTING INSTRUCTIONS:")
        print("1. Open Finder")
        print("2. Press Cmd+K (Connect to Server)")
        print("3. Enter: smb://mysmbserver.ddns.net:9999")
        print("4. Navigate to: /mnt/raid0/main/code/Receive_Realsense/Experiment Data")
        print("5. Or try alternative paths:")
        print("   - /Volumes/NAS_01/")
        print("   - /Volumes/Experiment Data/")
        print("   - /Volumes/Receive_Realsense/")
        print()
        
        # Try to find alternative mount points
        print("🔍 Checking for alternative mount points...")
        possible_paths = [
            "/Volumes/NAS_01/",
            "/Volumes/Experiment Data/",
            "/Volumes/Receive_Realsense/",
            "/Volumes/main/",
            "/Volumes/raid0/"
        ]
        
        found_mounts = []
        for path in possible_paths:
            if os.path.exists(path):
                found_mounts.append(path)
                print(f"   ✅ Found: {path}")
        
        if found_mounts:
            print(f"\n💡 Try using one of these paths:")
            for path in found_mounts:
                print(f"   python3 explore_nas_data.py --path {path}")
        else:
            print("   ❌ No alternative mount points found")
        
        return
    
    # Initialize counters
    total_weeks = 0
    total_dates = 0
    total_recordings = 0
    total_csv_files = 0
    total_size_mb = 0
    
    # Scan week folders (week0, week1, week2, week3)
    week_folders = []
    for week_num in range(4):
        week_folder = f"week{week_num}"
        week_path = os.path.join(nas_path, week_folder)
        if os.path.exists(week_path):
            week_folders.append(week_folder)
            total_weeks += 1
    
    print(f"📊 Found {total_weeks} week folders: {', '.join(week_folders)}")
    print()
    
    # Detailed exploration
    for week_folder in week_folders:
        week_path = os.path.join(nas_path, week_folder)
        print(f"📅 WEEK: {week_folder.upper()}")
        print("-" * 50)
        
        # Find all date folders (YYYY-MM-DD format)
        date_folders = []
        try:
            for item in os.listdir(week_path):
                item_path = os.path.join(week_path, item)
                if os.path.isdir(item_path):
                    # Check if it looks like a date folder
                    if len(item) == 10 and item.count('-') == 2:
                        date_folders.append(item)
        except PermissionError:
            print(f"❌ Permission denied accessing {week_path}")
            continue
        
        date_folders.sort()
        total_dates += len(date_folders)
        
        print(f"   📅 Found {len(date_folders)} date folders:")
        for date_folder in date_folders:
            print(f"      - {date_folder}")
        
        print()
        
        # Explore each date folder
        for date_folder in date_folders:
            date_path = os.path.join(week_path, date_folder)
            print(f"   📅 DATE: {date_folder}")
            print("   " + "-" * 40)
            
            # Find recording folders
            recording_folders = []
            try:
                for item in os.listdir(date_path):
                    item_path = os.path.join(date_path, item)
                    if os.path.isdir(item_path) and item.startswith('recording_'):
                        recording_folders.append(item)
            except PermissionError:
                print(f"      ❌ Permission denied accessing {date_path}")
                continue
            
            recording_folders.sort()
            total_recordings += len(recording_folders)
            
            print(f"      🎬 Found {len(recording_folders)} recording folders:")
            
            # Explore each recording folder
            for recording_folder in recording_folders:
                recording_path = os.path.join(date_path, recording_folder)
                print(f"         🎬 {recording_folder}")
                
                # Look for resampled folder
                resampled_path = os.path.join(recording_path, 'resampled')
                if os.path.exists(resampled_path):
                    print(f"            📊 resampled/ folder found")
                    
                    # Find CSV files
                    csv_files = []
                    try:
                        for file in os.listdir(resampled_path):
                            if file.endswith('.csv'):
                                csv_files.append(file)
                                file_path = os.path.join(resampled_path, file)
                                file_size = os.path.getsize(file_path)
                                total_size_mb += file_size / (1024 * 1024)
                    except PermissionError:
                        print(f"            ❌ Permission denied accessing {resampled_path}")
                        continue
                    
                    csv_files.sort()
                    total_csv_files += len(csv_files)
                    
                    if csv_files:
                        print(f"            📄 CSV files ({len(csv_files)}):")
                        for csv_file in csv_files:
                            file_path = os.path.join(resampled_path, csv_file)
                            try:
                                file_size = os.path.getsize(file_path)
                                file_size_mb = file_size / (1024 * 1024)
                                print(f"               - {csv_file} ({file_size_mb:.2f} MB)")
                                
                                # Quick analysis of CSV structure
                                try:
                                    df = pd.read_csv(file_path, nrows=5)
                                    columns = list(df.columns)
                                    print(f"                 Columns: {', '.join(columns)}")
                                except Exception as e:
                                    print(f"                 ⚠️  Could not read CSV: {e}")
                            except OSError:
                                print(f"               - {csv_file} (size unknown)")
                    else:
                        print(f"            📄 No CSV files found")
                else:
                    print(f"            ❌ No resampled/ folder found")
            
            print()
    
    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"📅 Week folders: {total_weeks}")
    print(f"📅 Date folders: {total_dates}")
    print(f"🎬 Recording folders: {total_recordings}")
    print(f"📄 CSV files: {total_csv_files}")
    print(f"💾 Total size: {total_size_mb:.2f} MB")
    print()
    
    # Generate file list for copying
    print("=" * 80)
    print("📋 FILE LIST FOR COPYING")
    print("=" * 80)
    
    csv_file_list = []
    for week_folder in week_folders:
        week_path = os.path.join(nas_path, week_folder)
        try:
            for date_folder in os.listdir(week_path):
                date_path = os.path.join(week_path, date_folder)
                if os.path.isdir(date_path):
                    try:
                        for recording_folder in os.listdir(date_path):
                            if recording_folder.startswith('recording_'):
                                recording_path = os.path.join(date_path, recording_folder)
                                resampled_path = os.path.join(recording_path, 'resampled')
                                if os.path.exists(resampled_path):
                                    try:
                                        for file in os.listdir(resampled_path):
                                            if file.endswith('.csv'):
                                                file_path = os.path.join(resampled_path, file)
                                                csv_file_list.append(file_path)
                                    except PermissionError:
                                        continue
                    except PermissionError:
                        continue
        except PermissionError:
            continue
    
    print(f"Found {len(csv_file_list)} CSV files to copy:")
    for i, file_path in enumerate(csv_file_list, 1):
        print(f"{i:3d}. {file_path}")
    
    return csv_file_list

def analyze_csv_structure(csv_file_path: str):
    """
    Analyze the structure of a CSV file
    """
    try:
        df = pd.read_csv(csv_file_path, nrows=10)
        print(f"\n📊 Analysis of: {os.path.basename(csv_file_path)}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Shape: {df.shape}")
        print(f"   Data types:")
        for col, dtype in df.dtypes.items():
            print(f"      {col}: {dtype}")
        
        # Check for IMU data structure
        imu_columns = ['t_sec', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
        has_imu_structure = all(col in df.columns for col in imu_columns)
        print(f"   IMU structure: {'✅ Yes' if has_imu_structure else '❌ No'}")
        
        return df
    except Exception as e:
        print(f"❌ Error analyzing {csv_file_path}: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    nas_path = "/Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--path" and len(sys.argv) > 2:
            nas_path = sys.argv[2]
        elif sys.argv[1] == "--help":
            print("Usage: python3 explore_nas_data.py [--path <path>]")
            print("  --path <path>  Specify the path to the mounted NAS folder")
            print("  --help         Show this help message")
            print()
            print("Default path: /Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data")
            sys.exit(0)
        else:
            nas_path = sys.argv[1]  # Use first argument as path
    
    # Explore the NAS data
    csv_files = explore_nas_data(nas_path)
    
    # Analyze a few CSV files if found
    if csv_files:
        print("\n" + "=" * 80)
        print("🔍 CSV STRUCTURE ANALYSIS")
        print("=" * 80)
        
        # Analyze first few files
        for i, csv_file in enumerate(csv_files[:3]):
            analyze_csv_structure(csv_file)
            if i < 2:  # Don't analyze more than 3 files
                continue
            break
