# Data Migration Strategy: Current to New Naming Convention

## Current Data Structure Analysis

### Current Directory Structure
```
data/
└── experiment_pilot/
    └── Day1/
        ├── 0630_test1_Single Lane Change_최지웅/
        │   ├── IMU_01.csv
        │   └── metadata.json
        └── 0630_test2_Single Lane Change_정현용/
            ├── IMU_01.csv
            ├── IMU_02.csv
            └── metadata.json
```

### Current Metadata Structure
```json
{
  "experiment": {
    "date": "2024-06-30",
    "scenario": "Single Lane Change",
    "test_name": "Test1"
  },
  "sensors": [
    {
      "id": "IMU_01",
      "position": "콘솔",
      "file": "IMU_01.csv",
      "subject": "최지웅"
    }
  ]
}
```

### Current File Naming
- **Files**: `IMU_01.csv`, `IMU_02.csv`
- **Directories**: `0630_test1_Single Lane Change_최지웅`

## Target Structure (New Convention)

### Target Directory Structure
```
data/
└── motion_sickness/
    └── 2024-06-30_single_lane_change/
        ├── test_001_최지웅/
        │   ├── metadata.json
        │   └── imu_console_001.csv
        └── test_002_정현용/
            ├── metadata.json
            ├── imu_passenger_rear_001.csv
            └── imu_console_002.csv
```

### Target Metadata Structure
```json
{
  "project": "motion_sickness",
  "experiment": {
    "id": "2024-06-30_single_lane_change",
    "date": "2024-06-30",
    "scenario": "single_lane_change",
    "description": "Single lane change maneuver for motion sickness study"
  },
  "test": {
    "id": "test_001_최지웅",
    "sequence": 1,
    "subject": "최지웅",
    "subject_id": "S001",
    "duration_sec": 120.5,
    "notes": ""
  },
  "sensors": [
    {
      "file": "imu_console_001.csv",
      "type": "imu",
      "position": "console",
      "sequence": 1,
      "sample_rate_hz": 100,
      "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"]
    }
  ],
  "data_quality": {
    "completeness": 1.0,
    "anomalies": 0,
    "notes": ""
  }
}
```

## Migration Mapping Strategy

### 1. Project Name Mapping
| Current | New | Logic |
|---------|-----|-------|
| `experiment_pilot` | `motion_sickness` | Based on scenario type and research focus |

### 2. Directory Name Parsing
| Current Component | Parsing Logic | New Component |
|------------------|---------------|---------------|
| `Day1` | Extract date from metadata.json | `2024-06-30` |
| `0630_test1_Single Lane Change_최지웅` | Parse test number and subject | `test_001_최지웅` |
| `0630_test2_Single Lane Change_정현용` | Parse test number and subject | `test_002_정현용` |

### 3. File Name Conversion
| Current | Position Mapping | New |
|---------|------------------|-----|
| `IMU_01.csv` | `콘솔` → `console` | `imu_console_001.csv` |
| `IMU_01.csv` | `조수석후방` → `passenger_rear` | `imu_passenger_rear_001.csv` |
| `IMU_02.csv` | `콘솔` → `console` | `imu_console_002.csv` |

### 4. Position Translation Mapping
| Korean Position | English Position | Notes |
|----------------|------------------|-------|
| `콘솔` | `console` | Center console area |
| `조수석후방` | `passenger_rear` | Rear passenger area |
| `대시보드` | `dashboard` | Dashboard area |
| `지붕` | `roof` | Roof mounted |

## Implementation Strategy

### Phase 1: Analysis and Validation
1. **Scan Current Structure**
   - Recursively scan all directories in `data/`
   - Extract directory names and file lists
   - Parse existing metadata.json files
   - Validate data integrity

2. **Create Mapping Database**
   - Build mapping table for all current files
   - Identify conflicts and edge cases
   - Generate migration plan

### Phase 2: Metadata Enhancement
1. **Extract Additional Information**
   - Calculate file durations from CSV data
   - Determine sample rates from timestamps
   - Analyze data quality and completeness
   - Generate subject IDs

2. **Create New Metadata Structure**
   - Transform existing metadata to new format
   - Add missing fields with calculated values
   - Validate against new schema

### Phase 3: File System Migration
1. **Create New Directory Structure**
   - Create new project directories
   - Create experiment directories with proper naming
   - Create test session directories

2. **Rename and Move Files**
   - Rename files according to new convention
   - Move files to new locations
   - Update metadata.json files

3. **Validation and Cleanup**
   - Verify all files moved correctly
   - Validate new metadata structure
   - Remove old directory structure (optional)

## Detailed Implementation Plan

### Step 1: Directory Structure Parser
```python
def parse_current_structure(data_path):
    """
    Parse current directory structure and extract information
    """
    structure = {}
    
    for root, dirs, files in os.walk(data_path):
        if 'metadata.json' in files:
            # Extract information from directory path
            path_parts = root.split(os.sep)
            project = path_parts[-3]  # experiment_pilot
            day = path_parts[-2]      # Day1
            test_dir = path_parts[-1] # 0630_test1_Single Lane Change_최지웅
            
            # Parse test directory name
            test_info = parse_test_directory(test_dir)
            
            # Read metadata
            metadata = read_metadata(os.path.join(root, 'metadata.json'))
            
            structure[root] = {
                'project': project,
                'day': day,
                'test_info': test_info,
                'metadata': metadata,
                'files': files
            }
    
    return structure
```

### Step 2: Test Directory Parser
```python
def parse_test_directory(test_dir_name):
    """
    Parse test directory name: 0630_test1_Single Lane Change_최지웅
    """
    import re
    
    # Extract date (0630)
    date_match = re.match(r'(\d{4})', test_dir_name)
    date = date_match.group(1) if date_match else None
    
    # Extract test number (test1)
    test_match = re.search(r'test(\d+)', test_dir_name)
    test_num = int(test_match.group(1)) if test_match else None
    
    # Extract scenario (Single Lane Change)
    scenario_match = re.search(r'test\d+_(.+?)_', test_dir_name)
    scenario = scenario_match.group(1) if scenario_match else None
    
    # Extract subject name (최지웅)
    subject_match = re.search(r'_(.+)$', test_dir_name)
    subject = subject_match.group(1) if subject_match else None
    
    return {
        'date': date,
        'test_number': test_num,
        'scenario': scenario,
        'subject': subject
    }
```

### Step 3: Position Translator
```python
def translate_position(korean_position):
    """
    Translate Korean position to English
    """
    position_map = {
        '콘솔': 'console',
        '조수석후방': 'passenger_rear',
        '대시보드': 'dashboard',
        '지붕': 'roof'
    }
    
    return position_map.get(korean_position, korean_position.lower())
```

### Step 4: File Name Generator
```python
def generate_new_filename(sensor_type, position, sequence):
    """
    Generate new filename according to convention
    """
    return f"{sensor_type}_{position}_{sequence:03d}.csv"

def generate_new_directory_name(date, scenario, test_num, subject):
    """
    Generate new directory name according to convention
    """
    # Convert date format
    formatted_date = f"2024-{date[:2]}-{date[2:]}"
    
    # Convert scenario to lowercase with underscores
    formatted_scenario = scenario.lower().replace(' ', '_')
    
    # Generate test ID
    test_id = f"test_{test_num:03d}_{subject}"
    
    return formatted_date, formatted_scenario, test_id
```

### Step 5: Metadata Transformer
```python
def transform_metadata(old_metadata, new_structure_info):
    """
    Transform old metadata to new format
    """
    new_metadata = {
        "project": "motion_sickness",
        "experiment": {
            "id": f"{new_structure_info['date']}_{new_structure_info['scenario']}",
            "date": new_structure_info['date'],
            "scenario": new_structure_info['scenario'],
            "description": f"{new_structure_info['scenario']} maneuver for motion sickness study"
        },
        "test": {
            "id": new_structure_info['test_id'],
            "sequence": new_structure_info['test_number'],
            "subject": new_structure_info['subject'],
            "subject_id": f"S{new_structure_info['test_number']:03d}",
            "duration_sec": calculate_duration(new_structure_info['files']),
            "notes": ""
        },
        "sensors": [],
        "data_quality": {
            "completeness": 1.0,
            "anomalies": 0,
            "notes": ""
        }
    }
    
    # Transform sensors
    for i, sensor in enumerate(old_metadata['sensors']):
        new_sensor = {
            "file": generate_new_filename('imu', translate_position(sensor['position']), i+1),
            "type": "imu",
            "position": translate_position(sensor['position']),
            "sequence": i+1,
            "sample_rate_hz": 100,  # Calculate from CSV data
            "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"]
        }
        new_metadata['sensors'].append(new_sensor)
    
    return new_metadata
```

## Migration Script Structure

### Main Migration Script
```python
#!/usr/bin/env python3
"""
Data Migration Script: Current to New Naming Convention
"""

import os
import json
import shutil
from pathlib import Path

def main():
    # Configuration
    source_path = "data"
    backup_path = "data_backup"
    
    # Step 1: Create backup
    create_backup(source_path, backup_path)
    
    # Step 2: Parse current structure
    current_structure = parse_current_structure(source_path)
    
    # Step 3: Generate migration plan
    migration_plan = generate_migration_plan(current_structure)
    
    # Step 4: Execute migration
    execute_migration(migration_plan)
    
    # Step 5: Validate migration
    validate_migration()

if __name__ == "__main__":
    main()
```

## Risk Mitigation

### 1. Backup Strategy
- Create complete backup before migration
- Test migration on copy first
- Keep original structure until validation complete

### 2. Validation Checks
- Verify all files moved correctly
- Check metadata integrity
- Validate new directory structure
- Test data access after migration

### 3. Rollback Plan
- Keep backup of original structure
- Document all changes made
- Prepare rollback script if needed

## Expected Outcomes

### Before Migration
- 2 test sessions
- 3 IMU files total
- Inconsistent naming
- Basic metadata

### After Migration
- 2 test sessions in new structure
- 3 properly named IMU files
- Complete metadata with all required fields
- Standardized directory structure
- Ready for database integration

## Next Steps

1. **Review and Approve Strategy**
2. **Create Migration Script**
3. **Test on Backup Data**
4. **Execute Migration**
5. **Validate Results**
6. **Update Database Integration**
7. **Document Changes**

---

*This migration strategy ensures a smooth transition from the current structure to the new naming convention while preserving all data integrity.*
