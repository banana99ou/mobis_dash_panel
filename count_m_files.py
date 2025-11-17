#!/usr/bin/env python3
"""
Count .m files in optimization directory structure
Used to debug parsing issues and verify file structure
"""

import os
from pathlib import Path
from collections import defaultdict

def count_m_files(base_path='data/motion_sickness/optimization'):
    """Count .m files by directory structure"""
    counts = defaultdict(int)
    total = 0
    
    print(f"Scanning .m files in: {base_path}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(base_path):
        m_files = [f for f in files if f.endswith('.m')]
        if m_files:
            rel_path = os.path.relpath(root, base_path)
            counts[rel_path] = len(m_files)
            total += len(m_files)
            
            # Show first few files in each directory
            if len(m_files) <= 5:
                print(f"{rel_path}: {len(m_files)} files")
                for f in m_files:
                    print(f"  - {f}")
            else:
                print(f"{rel_path}: {len(m_files)} files")
                for f in m_files[:3]:
                    print(f"  - {f}")
                print(f"  ... and {len(m_files) - 3} more")
    
    print("=" * 60)
    print(f"Total .m files: {total}")
    print(f"Directories with .m files: {len(counts)}")
    
    # Summary by data type
    print("\nSummary by data type:")
    for data_type in ['Driving', 'Driving+Rest']:
        data_path = os.path.join(base_path, data_type)
        if os.path.exists(data_path):
            type_count = sum(counts[k] for k in counts if k.startswith(data_type))
            print(f"  {data_type}: {type_count} files")
    
    return counts, total

if __name__ == "__main__":
    import sys
    base_path = sys.argv[1] if len(sys.argv) > 1 else 'data/motion_sickness/optimization'
    count_m_files(base_path)

