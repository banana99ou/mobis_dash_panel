# Data File Naming Convention Specification

## Overview

This document defines the standardized naming convention for data files in the multi-project research data management system. The convention ensures files are self-describing, database-independent, and scalable across different research projects.

## Directory Structure

```
data/
├── {project_name}/                        # Project-specific folder
│   ├── {date}_{scenario}/                 # Experiment folder
│   │   ├── {test_id}_{subject}/           # Test session folder
│   │   │   ├── metadata.json              # Test metadata
│   │   │   ├── {sensor_file}              # Sensor data files
│   │   │   └── ...
│   │   └── ...
│   ├── {date}_{scenario_2}/               # Multiple scenarios same day
│   └── ...
├── {project_name_2}/
└── shared/                                # Cross-project data
    ├── calibration/
    └── reference/
```

## File Naming Convention

### General Format

```
{sensor_type}_{position}_{sequence_id}.{extension}
```

### Components

| Component | Description | Examples | Rules |
|-----------|-------------|----------|-------|
| `sensor_type` | Type of sensor | `imu`, `camera`, `gps`, `lidar`, `can` | Lowercase, underscore-separated |
| `position` | Physical location | `console`, `dashboard`, `passenger_rear`, `roof` | Lowercase, underscore-separated |
| `sequence_id` | Unique identifier | `001`, `002`, `003` | Zero-padded 3-digit number |
| `extension` | File format | `csv`, `mp4`, `json`, `bin` | Standard file extensions |

### Examples

#### IMU Sensor Files
```
imu_console_001.csv          # IMU sensor at console, first sensor
imu_dashboard_002.csv        # IMU sensor at dashboard, second sensor
imu_passenger_rear_003.csv   # IMU sensor at passenger rear, third sensor
imu_roof_001.csv            # IMU sensor on roof, first sensor
```

#### Camera Files
```
camera_dashboard_001.mp4     # Dashboard camera video
camera_rear_002.mp4         # Rear camera video
camera_side_left_001.mp4    # Left side camera video
```

#### Other Sensor Types
```
gps_roof_001.csv           # GPS receiver on roof
lidar_front_001.bin        # Front LiDAR data
can_obd_001.csv           # CAN bus OBD data
```

## Directory Naming Convention

### Project Folder
```
{project_name}
```
- **Format**: Lowercase with underscores
- **Examples**: `motion_sickness`, `driver_behavior`, `vehicle_dynamics`

### Experiment Folder
```
{date}_{scenario}
```
- **Format**: `YYYY-MM-DD_scenario_name`
- **Date**: ISO format (YYYY-MM-DD)
- **Scenario**: Lowercase with underscores
- **Examples**: 
  - `2024-06-30_single_lane_change`
  - `2024-06-30_stop_and_go` (same day, different scenario)
  - `2024-07-01_highway_driving`

**Note**: If multiple scenarios are conducted on the same day, each scenario gets its own folder:
- `2024-06-30_single_lane_change`
- `2024-06-30_stop_and_go`
- `2024-06-30_highway_driving`

### Test Session Folder
```
{test_id}_{subject}
```
- **Format**: `test_{sequence}_{subject_name}`
- **Test ID**: Zero-padded 3-digit number
- **Subject**: Full name (Korean or English)
- **Examples**:
  - `test_001_정현용`
  - `test_002_최지웅`
  - `test_001_John_Doe`

## Metadata File Structure

Each test session folder must contain a `metadata.json` file with the following structure:

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
    "id": "test_001_정현용",
    "sequence": 1,
    "subject": "정현용",
    "subject_id": "S001",
    "duration_sec": 120.5,
    "notes": "Subject reported mild discomfort"
  },
  "sensors": [
    {
      "file": "imu_console_001.csv",
      "type": "imu",
      "position": "console",
      "sequence": 1,
      "sample_rate_hz": 100,
      "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"]
    },
    {
      "file": "imu_passenger_rear_002.csv",
      "type": "imu", 
      "position": "passenger_rear",
      "sequence": 2,
      "sample_rate_hz": 100,
      "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"]
    }
  ],
  "data_quality": {
    "completeness": 0.98,
    "anomalies": 3,
    "notes": "Minor gaps in data at 45.2s"
  }
}
```

## Complete Example

### Directory Structure
```
data/
└── motion_sickness/
    ├── 2024-06-30_single_lane_change/
    │   ├── test_001_정현용/
    │   │   ├── metadata.json
    │   │   ├── imu_console_001.csv
    │   │   └── imu_passenger_rear_002.csv
    │   └── test_002_최지웅/
    │       ├── metadata.json
    │       └── imu_console_001.csv
    ├── 2024-06-30_stop_and_go/
    │   └── test_001_정현용/
    │       ├── metadata.json
    │       └── imu_console_001.csv
    └── 2024-07-01_highway_driving/
        └── test_001_김철수/
            ├── metadata.json
            └── imu_dashboard_001.csv
```

### File Contents
- `imu_console_001.csv`: IMU data from console position
- `imu_passenger_rear_002.csv`: IMU data from passenger rear position
- `metadata.json`: Complete test session metadata

## Naming Rules

### Character Restrictions
- **Allowed**: Letters (a-z, A-Z), numbers (0-9), underscores (_), hyphens (-)
- **Prohibited**: Spaces, special characters, Unicode characters in filenames
- **Case**: Use lowercase for consistency

### Length Limits
- **Filename**: Maximum 255 characters
- **Directory name**: Maximum 255 characters
- **Path length**: Platform-dependent (Windows: 260 chars, Unix: 4096 chars)

### Reserved Names
Avoid these reserved names:
- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` through `COM9`
- `LPT1` through `LPT9`

## Migration from Current Structure

### Current Format
```
data/experiment_pilot/Day1/0630_test2_Single Lane Change_정현용/IMU_01.csv
```

### New Format
```
data/motion_sickness/2024-06-30_single_lane_change/test_002_정현용/imu_console_001.csv
```

### Migration Mapping
| Current Component | New Component | Example |
|------------------|---------------|---------|
| `experiment_pilot` | `motion_sickness` | Project name |
| `Day1` | `2024-06-30` | Date extraction |
| `0630_test2_Single Lane Change_정현용` | `test_002_정현용` | Test ID + subject |
| `IMU_01.csv` | `imu_console_001.csv` | Self-describing name |

## Validation Rules

### File Naming Validation
1. Must match pattern: `{sensor_type}_{position}_{sequence_id}.{extension}`
2. Sensor type must be from approved list
3. Position must be descriptive and consistent
4. Sequence ID must be zero-padded 3-digit number
5. Extension must be appropriate for sensor type

### Directory Naming Validation
1. Project name: lowercase with underscores only
2. Experiment folder: `YYYY-MM-DD_scenario_name` format
3. Test folder: `test_{sequence}_{subject}` format
4. No special characters or spaces

## Benefits

### Self-Describing
- Files contain meaningful information in their names
- No database dependency for basic understanding
- Easy to identify sensor type and location

### Scalable
- Easy to add new sensor types
- Simple to add new projects
- Consistent across all research areas

### Human-Readable
- Intuitive file organization
- Easy to browse and understand
- Clear hierarchy and relationships

### Database-Friendly
- Consistent patterns for automated processing
- Easy to parse and index
- Maintains referential integrity

## Future Extensions

### Additional Sensor Types
- `eeg_*` - Electroencephalography
- `ecg_*` - Electrocardiography
- `emg_*` - Electromyography
- `pressure_*` - Pressure sensors
- `temperature_*` - Temperature sensors

### Additional File Types
- `config_*` - Configuration files
- `calibration_*` - Calibration data
- `reference_*` - Reference measurements
- `log_*` - System logs

---

*This specification is version 1.0 and should be updated as new requirements emerge.*
