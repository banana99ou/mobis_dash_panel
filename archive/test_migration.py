#!/usr/bin/env python3
"""
Test Migration Script: Validate migration logic without moving files
"""

import os
import json
from pathlib import Path
from migrate_data import DataMigrator

def test_migration_logic():
    """Test the migration logic without actually moving files"""
    print("Testing Migration Logic")
    print("=" * 40)
    
    # Create migrator instance
    migrator = DataMigrator()
    
    # Test 1: Parse current structure
    print("\n1. Testing structure parsing...")
    structure = migrator.parse_current_structure()
    
    if not structure:
        print("❌ No data found to test")
        return False
    
    print(f"✅ Found {len(structure)} test sessions to migrate")
    
    # Test 2: Generate migration plan
    print("\n2. Testing migration plan generation...")
    migration_plan = migrator.generate_migration_plan(structure)
    
    print(f"✅ Generated migration plan for {len(migration_plan)} sessions")
    
    # Test 3: Display migration plan
    print("\n3. Migration Plan Preview:")
    print("-" * 40)
    
    for i, plan in enumerate(migration_plan, 1):
        print(f"\nSession {i}:")
        print(f"  Old Path: {plan['old_path']}")
        print(f"  New Path: {plan['new_path']}")
        print(f"  Test ID: {plan['new_structure_info']['test_id']}")
        print(f"  Subject: {plan['new_structure_info']['subject']}")
        print(f"  Files to migrate:")
        
        for file_mapping in plan['file_mappings']:
            print(f"    {file_mapping['old_name']} -> {file_mapping['new_name']}")
    
    # Test 4: Validate metadata transformation
    print("\n4. Testing metadata transformation...")
    
    for i, plan in enumerate(migration_plan, 1):
        print(f"\nSession {i} Metadata Preview:")
        metadata = plan['new_metadata']
        print(f"  Project: {metadata['project']}")
        print(f"  Experiment ID: {metadata['experiment']['id']}")
        print(f"  Test ID: {metadata['test']['id']}")
        print(f"  Subject: {metadata['test']['subject']}")
        print(f"  Duration: {metadata['test']['duration_sec']}s")
        print(f"  Sensors: {len(metadata['sensors'])}")
        
        for sensor in metadata['sensors']:
            print(f"    - {sensor['file']} ({sensor['position']}, {sensor['sample_rate_hz']}Hz)")
    
    # Test 5: Check for potential issues
    print("\n5. Checking for potential issues...")
    issues = []
    
    for plan in migration_plan:
        # Check if old files exist
        for file_mapping in plan['file_mappings']:
            if not os.path.exists(file_mapping['old_file']):
                issues.append(f"Source file not found: {file_mapping['old_file']}")
        
        # Check for duplicate test IDs
        test_id = plan['new_structure_info']['test_id']
        duplicate_count = sum(1 for p in migration_plan if p['new_structure_info']['test_id'] == test_id)
        if duplicate_count > 1:
            issues.append(f"Duplicate test ID: {test_id}")
    
    if issues:
        print("⚠️  Potential issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No issues found")
    
    # Test 6: Show expected directory structure
    print("\n6. Expected New Directory Structure:")
    print("-" * 40)
    
    # Group by experiment
    experiments = {}
    for plan in migration_plan:
        exp_id = plan['new_metadata']['experiment']['id']
        if exp_id not in experiments:
            experiments[exp_id] = []
        experiments[exp_id].append(plan)
    
    for exp_id, plans in experiments.items():
        print(f"\ndata/motion_sickness/{exp_id}/")
        for plan in plans:
            test_id = plan['new_structure_info']['test_id']
            print(f"  └── {test_id}/")
            print(f"      ├── metadata.json")
            for file_mapping in plan['file_mappings']:
                print(f"      └── {file_mapping['new_name']}")
    
    print(f"\n✅ Migration logic test completed successfully!")
    print(f"Ready to migrate {len(migration_plan)} test sessions")
    
    return True

def main():
    """Main test function"""
    try:
        success = test_migration_logic()
        if success:
            print("\n🎉 All tests passed! Migration is ready to proceed.")
            print("\nTo run the actual migration:")
            print("  python migrate_data.py")
        else:
            print("\n❌ Tests failed. Please check the issues above.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
