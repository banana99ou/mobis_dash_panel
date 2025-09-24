#!/usr/bin/env python3
"""
Reorganize Week0 Recording Folders

This script reorganizes week0 recording folders to match the structure used in week3.
Based on the organizer.py logic from the Post processing folder.

Structure:
- Raw/: frames/, imu_raw.csv, CentC_serial_*.csv, HeadR_serial_*.csv (base only)
- temp/: CentC_resampled_100Hz.csv, HeadR_serial_*_Rot.csv, realsense_resampled_100Hz*.csv
- resampled/: everything else

Usage:
  python3 reorganize_week0.py [--dry-run]
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import List, Tuple

RAW_DIR = "Raw"
TEMP_DIR = "temp"
RESAMPLED_DIR = "resampled"

# Strict regexes for matching
RE_CENTC_SERIAL = re.compile(r"^CentC_serial_\d{8}_\d{6}_COM\d+\.csv$")
RE_HEADR_SERIAL_BASE = re.compile(r"^HeadR_serial_\d{8}_\d{6}_COM\d+\.csv$")
RE_HEADR_SERIAL_ROT = re.compile(r"^HeadR_serial_\d{8}_\d{6}_COM\d+_Rot\.csv$")

# Exact names for temp
TEMP_EXACT = {
    "CentC_resampled_100Hz.csv",
    "CentC_resampled_100Hz_LH.csv",
    "HeadR_resampled_100Hz.csv",
    "HeadR_resampled_100Hz_LH.csv",
    "realsense_resampled_100Hz.csv",
    "realsense_resampled_100Hz_LH.csv",
    "realsense_resampled_100Hz_Rot.csv",
}

def is_recording_dir(p: Path) -> bool:
    """Check if path is a recording directory"""
    return p.is_dir() and p.name.startswith("recording_")

def discover_recording_dirs(root: Path) -> List[Path]:
    """Discover all recording directories under root"""
    if is_recording_dir(root):
        return [root]
    
    # Search one level deep first, then recursively as fallback
    immediate = [d for d in root.iterdir() if is_recording_dir(d)]
    if immediate:
        return immediate
    return [d for d in root.rglob("recording_*") if d.is_dir()]

def ensure_subdirs(rec_dir: Path):
    """Ensure Raw, temp, and resampled subdirectories exist"""
    for name in (RAW_DIR, TEMP_DIR, RESAMPLED_DIR):
        (rec_dir / name).mkdir(exist_ok=True)

def unique_destination(dst: Path) -> Path:
    """If dst exists, append ' (n)' before suffix until unique"""
    if not dst.exists():
        return dst
    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1

def planned_moves_for_recording(rec_dir: Path) -> List[Tuple[Path, Path]]:
    """
    Generate planned moves for a recording directory
    Returns list of (src, dst) tuples
    """
    ensure_subdirs(rec_dir)
    raw_dir = rec_dir / RAW_DIR
    tmp_dir = rec_dir / TEMP_DIR
    res_dir = rec_dir / RESAMPLED_DIR
    
    moves = []
    moved_items = set()  # Track items we've already planned to move
    
    # 1) Explicit items to Raw
    frames_dir = rec_dir / "frames"
    if frames_dir.exists() and frames_dir.is_dir() and frames_dir.parent == rec_dir:
        moves.append((frames_dir, raw_dir / frames_dir.name))
        moved_items.add(frames_dir.name)
    
    imu_raw = rec_dir / "imu_raw.csv"
    if imu_raw.exists() and imu_raw.is_file() and imu_raw.parent == rec_dir:
        moves.append((imu_raw, raw_dir / imu_raw.name))
        moved_items.add(imu_raw.name)
    
    # Serial CSVs
    for item in rec_dir.iterdir():
        if not item.is_file() or item.name in moved_items:
            continue
        name = item.name
        if RE_CENTC_SERIAL.match(name):
            moves.append((item, raw_dir / name))
            moved_items.add(name)
        elif RE_HEADR_SERIAL_BASE.match(name):
            # Explicitly exclude *_Rot.csv (handled by temp)
            if not name.endswith("_Rot.csv"):
                moves.append((item, raw_dir / name))
                moved_items.add(name)
    
    # 2) Explicit items to temp
    for item in rec_dir.iterdir():
        if not item.is_file() or item.name in moved_items:
            continue
        name = item.name
        if name in TEMP_EXACT:
            moves.append((item, tmp_dir / name))
            moved_items.add(name)
        elif RE_HEADR_SERIAL_ROT.match(name):
            moves.append((item, tmp_dir / name))
            moved_items.add(name)
    
    # 3) Everything else in top-level recording dir → resampled
    for item in rec_dir.iterdir():
        # Skip the three target dirs themselves
        if item.name in (RAW_DIR, TEMP_DIR, RESAMPLED_DIR):
            continue
        # Skip items we already plan to move (avoid duplicates)
        if item.name in moved_items:
            continue
        if item.parent == rec_dir:
            # If it's a leftover directory or file, move it to resampled
            moves.append((item, res_dir / item.name))
            moved_items.add(item.name)
    
    return moves

def execute_moves(moves: List[Tuple[Path, Path]], dry_run: bool = False):
    """Perform the planned moves safely with collision handling"""
    for src, dst in moves:
        # If the src was already moved by an earlier rule, skip silently
        if not src.exists():
            continue
        # If src is already in the correct dst parent and same name, skip
        if src.resolve() == (dst.parent / src.name).resolve():
            continue
        # Ensure parent exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Resolve name collisions at destination
        final_dst = unique_destination(dst)
        action = f"MOVE: {src}  ->  {final_dst}"
        if dry_run:
            print("[DRY-RUN]", action)
        else:
            # Use shutil.move for both files and folders
            shutil.move(str(src), str(final_dst))
            print(action)

def reorganize_week0(nas_path: str = "/Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data", dry_run: bool = False):
    """Reorganize all recording folders in week0"""
    week0_path = Path(nas_path) / "week0"
    
    if not week0_path.exists():
        print(f"❌ Error: week0 path does not exist: {week0_path}")
        return
    
    print("=" * 80)
    print("🔄 WEEK0 REORGANIZATION")
    print("=" * 80)
    print(f"📁 Processing: {week0_path}")
    print(f"🔧 Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print()
    
    # Find all recording directories in week0
    recordings = discover_recording_dirs(week0_path)
    if not recordings:
        print("❌ No recording_* directories found in week0")
        return
    
    print(f"📊 Found {len(recordings)} recording folder(s):")
    for rec in recordings:
        print(f"   - {rec.relative_to(week0_path)}")
    print()
    
    all_moves = []
    for rec in recordings:
        print(f"== Planning moves for: {rec.name} ==")
        moves = planned_moves_for_recording(rec)
        
        # Filter out moves where src already under correct destination (idempotency)
        filtered = []
        for src, dst in moves:
            if not src.exists():
                continue
            # If src already in the target directory with same name, skip
            if src.parent.resolve() == dst.parent.resolve() and src.name == dst.name:
                continue
            filtered.append((src, dst))
        
        for src, dst in filtered:
            print(f"  plan: {src.name} -> {dst.parent.name}/")
        all_moves.extend(filtered)
        print()
    
    print(f"📊 Total planned operations: {len(all_moves)}")
    
    if dry_run:
        print("\n🔍 Dry-run mode: no changes made.")
        print("Run without --dry-run to execute the reorganization.")
    else:
        print("\n⚡ Executing moves...")
        execute_moves(all_moves, dry_run=False)
        print("✅ Done.")
    
    return len(all_moves)

def main():
    parser = argparse.ArgumentParser(description="Reorganize week0 recording folders to match week3 structure.")
    parser.add_argument("--path", "-p", 
                       default="/Volumes/NAS_01/main/code/Receive_Realsense/Experiment Data",
                       help="Path to the Experiment Data directory")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be changed without moving anything.")
    args = parser.parse_args()
    
    try:
        operations = reorganize_week0(args.path, args.dry_run)
        if operations > 0:
            print(f"\n🎉 Reorganization complete! {operations} operations performed.")
        else:
            print("\n✅ No reorganization needed - folders already properly structured.")
    except Exception as e:
        print(f"❌ Error during reorganization: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
