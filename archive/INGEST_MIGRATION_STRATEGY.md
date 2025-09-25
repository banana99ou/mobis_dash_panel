# Ingest Folder Migration Strategy

## Overview

This document outlines the strategy for migrating data from the `data/ingest/` folder to follow the new naming convention defined in `FILENAME_CONVENTION.md`. The migration will exclude video files (.avi, .mp4, .mov) and archive files (.zip, .rar, .7z) as requested.

## Current Data Analysis

### Legacy Format (Korean naming)
```
0811 Test01 sub02 이서윤 SLC/
├── CentC_resampled_100Hz_LH.csv      # Center Console IMU
├── HeadR_resampled_100Hz_LH.csv      # Headrest IMU  
├── realsense_resampled_100Hz_LH_Rot.csv  # RealSense IMU
└── video_zoh_100Hz.avi               # EXCLUDED
```

### Recording Format (Timestamp-based)
```
recording_20250804_113600_ND/
├── CentC_resampled_100Hz_LH.csv      # Center Console IMU
└── realsense_resampled_100Hz_LH.csv  # RealSense IMU
```

## Target Structure (Following FILENAME_CONVENTION.md)

### After Migration
```
data/motion_sickness/
├── 2024-08-11_single_lane_change/
│   └── test_001_이서윤/
│       ├── metadata.json
│       ├── imu_console_001.csv       # CentC → console
│       ├── imu_headrest_002.csv      # HeadR → headrest
│       └── imu_realsense_003.csv     # realsense → realsense
├── 2024-08-04_recording/
│   └── test_001_ND/
│       ├── metadata.json
│       ├── imu_console_001.csv
│       └── imu_realsense_002.csv
└── ...
```

## Migration Mapping Strategy

### 1. Directory Name Parsing

#### Legacy Format: `0811 Test01 sub02 이서윤 SLC`
| Component | Pattern | Example | New Format |
|-----------|---------|---------|------------|
| Date | `(\d{4})` | `0811` | `2024-08-11` |
| Test Number | `Test(\d+)` | `Test01` | `test_001` |
| Subject Number | `sub(\d+)` | `sub02` | Used for subject_id |
| Subject Name | `sub\d+\s+([^S]+?)\s+S` | `이서윤` | `이서윤` |
| Scenario | `(SLC\|S&G\|LW)` | `SLC` | `single_lane_change` |

#### Recording Format: `recording_20250804_113600_ND`
| Component | Pattern | Example | New Format |
|-----------|---------|---------|------------|
| Date | `(\d{8})` | `20250804` | `2024-08-04` |
| Time | `(\d{6})` | `113600` | Used for notes |
| Identifier | `_([A-Z0-9]+)$` | `ND` | `ND` |

### 2. Sensor File Mapping

| Current Filename | Sensor Type | Position | New Filename |
|------------------|-------------|----------|--------------|
| `CentC_resampled_100Hz_LH.csv` | `imu` | `console` | `imu_console_001.csv` |
| `HeadR_resampled_100Hz_LH.csv` | `imu` | `headrest` | `imu_headrest_002.csv` |
| `realsense_resampled_100Hz_LH_Rot.csv` | `imu` | `realsense` | `imu_realsense_003.csv` |

### 3. Scenario Mapping

| Current | New Format | Description |
|---------|------------|-------------|
| `SLC` | `single_lane_change` | Single Lane Change |
| `S&G` | `stop_and_go` | Stop and Go |
| `LW` | `lane_weaving` | Lane Weaving |
| `recording` | `recording` | General recording |

## File Filtering Strategy

### Excluded File Types
- **Video Files**: `.avi`, `.mp4`, `.mov`
- **Archive Files**: `.zip`, `.rar`, `.7z`
- **Hidden Files**: Files starting with `.`

### Included File Types
- **CSV Files**: `.csv` (sensor data)
- **JSON Files**: `.json` (metadata, if present)

## Metadata Generation

### New Metadata Structure
```json
{
  "project": "motion_sickness",
  "experiment": {
    "id": "2024-08-11_single_lane_change",
    "date": "2024-08-11",
    "scenario": "single_lane_change",
    "description": "single_lane_change experiment for motion sickness study"
  },
  "test": {
    "id": "test_001_이서윤",
    "sequence": 1,
    "subject": "이서윤",
    "subject_id": "S001",
    "duration_sec": 120.5,
    "notes": "Migrated from ingest folder"
  },
  "sensors": [
    {
      "file": "imu_console_001.csv",
      "type": "imu",
      "position": "console",
      "sequence": 1,
      "sample_rate_hz": 100.0,
      "data_points": 186161,
      "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"],
      "description": "Center console IMU"
    }
  ],
  "data_quality": {
    "completeness": 1.0,
    "anomalies": 0,
    "notes": "Data migrated from ingest folder"
  },
  "migration_info": {
    "migrated_at": "2024-01-20T10:30:00",
    "source_format": "legacy_ingest",
    "original_directory": "0811 Test01 sub02 이서윤 SLC"
  }
}
```

## Implementation Features

### 1. Safety Features
- **Backup Creation**: Complete backup of ingest folder before migration
- **Dry Run Mode**: Preview migration plan without executing
- **Validation**: Verify all files copied correctly with size checks
- **Rollback**: Original data preserved in backup

### 2. Data Analysis
- **Automatic Metrics**: Calculate duration, sample rate, data points from CSV files
- **Sensor Detection**: Automatically identify sensor types from filenames
- **Quality Assessment**: Basic data quality metrics

### 3. Error Handling
- **Graceful Degradation**: Continue migration even if some files fail
- **Detailed Logging**: Comprehensive log of all operations
- **Conflict Resolution**: Handle duplicate names and directory conflicts

## Migration Process

### Phase 1: Analysis
1. Scan ingest folder for directories with CSV files
2. Parse directory names to extract metadata
3. Identify sensor types from filenames
4. Calculate file metrics (duration, sample rate, data points)

### Phase 2: Planning
1. Generate new directory structure
2. Create file mapping plan
3. Generate metadata for each test session
4. Validate plan for conflicts

### Phase 3: Execution
1. Create backup of original data
2. Create new directory structure
3. Copy and rename CSV files
4. Generate metadata.json files
5. Validate migration success

### Phase 4: Validation
1. Verify all directories created
2. Check all files copied with correct sizes
3. Validate metadata.json files
4. Generate migration report

## Usage Instructions

### 1. Dry Run (Recommended First)
```bash
python migrate_ingest_data.py
# Select 'y' for dry run to preview the migration plan
```

### 2. Full Migration
```bash
python migrate_ingest_data.py
# Select 'y' to continue, 'n' for dry run
```

### 3. Check Results
- Review `ingest_migration_log.txt` for detailed log
- Check `data/motion_sickness/` for migrated data
- Original data preserved in `data_backup/ingest/`

## Expected Outcomes

### Before Migration
- **Legacy Structure**: Inconsistent naming, mixed formats
- **File Types**: CSV + video + zip files mixed together
- **Metadata**: Minimal or missing metadata
- **Organization**: Difficult to query and analyze

### After Migration
- **Standardized Structure**: Consistent naming following convention
- **Clean Data**: Only CSV files with proper metadata
- **Rich Metadata**: Complete metadata with calculated metrics
- **Database Ready**: Structure ready for database integration
- **Queryable**: Easy to search and filter by subject, scenario, date

## Integration with Database

After migration, the new structure can be easily integrated with the existing database system:

```python
# Update database with migrated data
from database import db
db.scan_and_index_data('data/motion_sickness')
```

## Risk Mitigation

### 1. Data Safety
- Complete backup before any changes
- Non-destructive migration (original data preserved)
- Validation checks at every step

### 2. Rollback Plan
- Original data in `data_backup/ingest/`
- Migration log for tracking changes
- Simple restore process if needed

### 3. Quality Assurance
- File size validation
- Metadata structure validation
- Sample data verification

## Future Enhancements

### 1. Batch Processing
- Process multiple ingest folders
- Parallel processing for large datasets
- Progress tracking for long operations

### 2. Advanced Analytics
- Data quality scoring
- Anomaly detection
- Statistical summaries

### 3. Integration Features
- Direct database integration
- API endpoints for migration
- Web interface for monitoring

---

*This migration strategy ensures a smooth transition from the current ingest folder structure to the standardized naming convention while preserving data integrity and excluding unwanted file types.*
