# Mobis Dashboard Panel - Project Specification

**Version**: 1.0  
**Last Updated**: 2025-01-04  
**Purpose**: This document serves as the anchor specification for the entire project, providing a comprehensive overview of architecture, features, and implementation status.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Feature Status](#feature-status)
5. [API Endpoints](#api-endpoints)
6. [File Structure](#file-structure)
7. [Data Flow](#data-flow)
8. [Development Guidelines](#development-guidelines)

---

## Project Overview

### Purpose
**Mobis Dashboard Panel** is an automated experiment data database management system designed for:
- Automatic indexing and management of multi-sensor experimental data
- Web-based dashboard for intuitive data visualization
- REST API for programmatic data querying
- Classification and comparative analysis of experimental scenarios

### Key Use Cases
1. **Real-time Data Monitoring**: Automatically detect and index new experimental data files
2. **Data Visualization**: Interactive web dashboard for viewing IMU sensor data (acceleration, gyroscope)
3. **Data Search**: Search experiments, tests, and sensors by various criteria (subject, scenario, date, project)
4. **Optimization Parameter Management**: Index and search optimization parameters, results, and visualizations
5. **Cross-sensor Comparison**: Compare multiple sensor data simultaneously on interactive graphs

### Target Users
- Research team members conducting motion sickness experiments
- Data analysts reviewing experimental results
- Developers integrating with the system via API

---

## System Architecture

### Technology Stack
- **Frontend**: Plotly Dash (Python-based web framework)
- **Backend**: Python (Dash built-in Flask server)
- **Database**: SQLite (`db/imu_data.db`)
- **Visualization**: Plotly graphs
- **File Monitoring**: Python `watchdog` library
- **Containerization**: Docker (optional)

### System Components

#### 1. Main Application (`app.py`)
- Dash web application with Flask server
- User authentication (password-based)
- Interactive dashboard UI
- REST API endpoints
- Real-time data refresh (2-second interval)

#### 2. Database Layer (`database.py`)
- `IMUDatabase` class managing all database operations
- Schema initialization and migration
- Data indexing and search functionality
- Optimization parameter management

#### 3. File Watcher (`data_watcher.py`)
- Background process monitoring file system changes
- Automatic re-indexing on file changes
- Debouncing to prevent duplicate processing
- Separate watchers for test data and optimization data

#### 4. Utilities (`utils.py`)
- Data loading and processing functions
- Graph generation utilities
- Sensor data summary calculations

### Deployment Options
1. **Direct Execution**: `python app.py` (runs on `http://localhost:8050`)
2. **Docker**: `docker-compose up -d`

---

## Database Schema

### Core Tables

#### `experiments`
Stores experiment sessions (date, scenario, project).
```sql
- id (PRIMARY KEY)
- project (TEXT)
- experiment_id (TEXT)
- date (TEXT, NOT NULL)
- scenario (TEXT, NOT NULL)  -- e.g., 'single_lane_change', 'stop_and_go', 'long_wave'
- description (TEXT)
- created_at (TIMESTAMP)
```

#### `tests`
Stores individual test sessions within an experiment.
```sql
- id (PRIMARY KEY)
- experiment_id (FOREIGN KEY -> experiments)
- test_id (TEXT)  -- e.g., 'test_001'
- test_name (TEXT, NOT NULL)
- sequence (INTEGER)
- subject (TEXT)  -- e.g., '정현용'
- subject_id (TEXT)  -- e.g., 'sub01'
- duration_sec (REAL)
- notes (TEXT)
- file_path (TEXT, NOT NULL)  -- path to metadata.json
- imu_count (INTEGER)
- metadata_hash (TEXT)
- created_at (TIMESTAMP)
```

#### `sensors`
Stores individual sensor data files within a test.
```sql
- id (PRIMARY KEY)
- test_id (FOREIGN KEY -> tests)
- sensor_id (TEXT, NOT NULL)  -- e.g., 'IMU_01'
- sensor_type (TEXT)  -- e.g., 'imu'
- position (TEXT)  -- e.g., 'console', 'passenger_rear'
- sequence (INTEGER)
- sample_rate_hz (REAL)
- file_name (TEXT, NOT NULL)
- file_path (TEXT, NOT NULL)
- created_at (TIMESTAMP)
```

#### `data_quality`
Stores data quality metrics for tests.
```sql
- id (PRIMARY KEY)
- test_id (FOREIGN KEY -> tests)
- completeness (REAL)
- anomalies (INTEGER)
- notes (TEXT)
- created_at (TIMESTAMP)
```

### Optimization Tables

#### `optimization_strategies`
Lookup table for optimization strategies (0-4).
```sql
- id (PRIMARY KEY)
- strategy_number (INTEGER, UNIQUE, NOT NULL)
- strategy_name (TEXT, NOT NULL)
- description (TEXT)
- requires_subject (INTEGER, DEFAULT 0)
- requires_scenario (INTEGER, DEFAULT 0)
- requires_sensor_setting (INTEGER, DEFAULT 0)
- created_at (TIMESTAMP)
```

**Strategy Definitions**:
- **Strategy 0**: Subject + Scenario + Sensor specific
- **Strategy 1**: All tests for subject (across scenarios)
- **Strategy 2**: All tests for subject + scenario
- **Strategy 3**: All tests for scenario (across subjects)
- **Strategy 4**: All tests in database

#### `sensor_settings`
Lookup table for sensor configuration codes (e.g., 'H-IMU_N-VV').
```sql
- id (PRIMARY KEY)
- sensor_setting_code (TEXT, UNIQUE, NOT NULL)
- description (TEXT)
- sensor_components (TEXT)  -- e.g., 'H-IMU, V-IMU, S-IMU'
- created_at (TIMESTAMP)
```

#### `optimization_parameters`
Stores optimization parameter files (.m files).
```sql
- id (PRIMARY KEY)
- strategy_id (FOREIGN KEY -> optimization_strategies)
- parameter_type (TEXT, NOT NULL)  -- 'fullopt' or '3opt'
- data_type (TEXT, NOT NULL)  -- '주행' or '주행+휴식'
- file_path (TEXT, NOT NULL)
- file_name (TEXT, NOT NULL)
- file_hash (TEXT)
- metadata (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### Junction Tables (Many-to-Many)
- `optimization_parameter_subjects`: Links parameters to subjects
- `optimization_parameter_scenarios`: Links parameters to scenarios
- `optimization_parameter_sensor_settings`: Links parameters to sensor settings

#### `optimization_results`
Stores optimization result files (.mat files).
```sql
- id (PRIMARY KEY)
- parameter_id (FOREIGN KEY -> optimization_parameters)
- model_name (TEXT, NOT NULL)  -- e.g., 'MSIbase', 'OmanAP'
- result_file_path (TEXT, NOT NULL)
- result_file_name (TEXT, NOT NULL)
- file_hash (TEXT)
- metadata (TEXT)  -- JSON with RMSE, R2, etc.
- created_at (TIMESTAMP)
- UNIQUE(parameter_id, model_name)
```

#### `optimization_visualizations`
Stores visualization files (.png files).
```sql
- id (PRIMARY KEY)
- parameter_id (FOREIGN KEY -> optimization_parameters)
- visualization_type (TEXT, NOT NULL)  -- 'model_specific' or 'comparison'
- model_name (TEXT)  -- NULL for comparison types
- graph_file_path (TEXT, NOT NULL)
- graph_file_name (TEXT, NOT NULL)
- file_hash (TEXT)
- created_at (TIMESTAMP)
```

---

## Feature Status

### ✅ Completed Features

#### Data Management
- ✅ Raw data search API (`/api/search/tests`)
- ✅ Automatic file system monitoring (`data_watcher.py`)
- ✅ Metadata.json parsing and indexing
- ✅ Database insertion with hash-based duplicate detection
- ✅ Database synchronization (removes deleted files)

#### Web Dashboard
- ✅ Password-protected login system
- ✅ Interactive experiment/test/sensor selection
- ✅ Real-time data visualization (Plotly graphs)
- ✅ Multi-sensor comparison graphs
- ✅ Data summary panel (sample count, duration, sampling rate)
- ✅ Graph height adjustment slider
- ✅ Collapsible sidebar and summary panel
- ✅ Periodic data refresh (2-second interval)

#### Optimization System
- ✅ Optimization database schema (all tables)
- ✅ Lookup table population (strategies, sensor settings)
- ✅ Parameter file indexing (`.m` files)
- ✅ Result file indexing (`.mat` files)
- ✅ Visualization file indexing (`.png` files)
- ✅ Optimization parameter search API (`/api/optimization/parameters`)
- ✅ Parameter detail API (`/api/optimization/parameters/<id>`)
- ✅ Optimization file serving API (`/api/optimization/files/<path>`)
- ✅ Automatic optimization data indexing (`scan_and_index_optimization_data`)

#### Infrastructure
- ✅ Docker containerization support
- ✅ Database backup functionality
- ✅ Error handling in APIs
- ✅ Korean language interface

### 🔄 In Progress / Partially Complete

#### Data Management
- ⚠️ File watching system exists but needs extension for raw data ingest
- ⚠️ Bulk import functionality (not yet implemented)

#### Optimization System
- ⚠️ Parameter-to-test linking algorithm (junction tables exist but linking logic may need refinement)
- ⚠️ Metadata extraction from .mat files (basic structure exists, may need enhancement)

### 📋 Planned Features (from FEATURES.md)

#### Data Management
- [ ] Enhanced raw data ingest system
  - [ ] Extended file watching system
  - [ ] Enhanced metadata parsing and validation
  - [ ] Improved duplicate detection and handling
- [ ] Bulk import functionality
- [ ] Data validation and quality checks
- [ ] Import logging and reporting

#### Optimization System
- [ ] Figure generation from result .mat files
  - [ ] MATLAB script integration or Python equivalent
  - [ ] Batch figure generation
  - [ ] Generation queue/job system
  - [ ] Status tracking
- [ ] Enhanced metadata extraction from .mat files (RMSE, R2, etc.)
- [ ] Migration script for existing optimization files
  - [ ] Batch indexing with progress reporting
  - [ ] Rollback capability

#### Infrastructure
- [ ] Comprehensive API documentation (OpenAPI/Swagger)
- [ ] Unit and integration tests
- [ ] Performance optimization
  - [ ] Query optimization
  - [ ] Caching layer
  - [ ] API response pagination
  - [ ] Connection pooling

---

## API Endpoints

### Test Data APIs

#### `GET /api/search/tests`
Search for tests by various criteria.

**Query Parameters**:
- `subject` (optional): Subject name
- `subject_id` (optional): Subject ID (e.g., 'sub01')
- `sensor_id` (optional): Sensor ID
- `scenario` (optional): Scenario name
- `date` (optional): Experiment date
- `project` (optional): Project name

**Response**:
```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "test_id": 1,
      "test_name": "Test1",
      "subject": "정현용",
      "scenario": "single_lane_change",
      ...
    }
  ]
}
```

#### `GET /api/tests/<test_id>/paths`
Get file paths for a specific test.

#### `GET /api/tests/<test_id>/sensors`
Get sensor information for a specific test.

### Optimization APIs

#### `GET /api/optimization/parameters`
Search optimization parameters.

**Query Parameters**:
- `subject_id` (optional): Subject ID
- `scenario` (optional): Scenario (e.g., 'lw', 'slc', 's&g')
- `sensor` (optional): Sensor setting code
- `strategy` (optional): Strategy number (0-4)
- `model` (optional): Model name
- `parameter_type` (optional): 'fullopt' or '3opt'
- `data_type` (optional): '주행' or '주행+휴식'

**Response**:
```json
{
  "status": "success",
  "count": 3,
  "data": [
    {
      "id": 1,
      "strategy": 0,
      "parameter_type": "fullopt",
      "data_type": "주행",
      "results": [...],
      "visualizations": [
        {
          "file_path": "...",
          "url": "/api/optimization/files/..."
        }
      ]
    }
  ]
}
```

#### `GET /api/optimization/parameters/<parameter_id>`
Get detailed information for a specific parameter.

#### `GET /api/optimization/files/<path>`
Serve optimization files (PNG, MAT, etc.) via web URL.

### System APIs

#### `GET /api/health`
Health check endpoint.

---

## File Structure

### Directory Layout
```
mobis_dash_panel/
├── app.py                    # Main Dash application
├── database.py              # Database management (IMUDatabase class)
├── data_watcher.py          # File system monitoring
├── utils.py                 # Data processing utilities
├── test_api.py              # API testing script
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker deployment
├── Dockerfile              # Container build
│
├── PROJECT_SPEC.md         # This document (anchor spec)
├── FEATURES.md             # Feature todo list
├── Readme.md              # User-facing documentation
├── API_DOCUMENTATION.md    # REST API documentation
├── USER_GUIDE_KR.md        # Korean user guide
├── FILENAME_CONVENTION.md  # File naming rules (English)
├── FILENAME_CONVENTION_KR.md # File naming rules (Korean)
│
├── data/                   # Experiment data storage
│   ├── motion_sickness/    # Motion sickness project
│   │   ├── {date}_{scenario}/
│   │   │   ├── {test_id}_{subject}/
│   │   │   │   ├── metadata.json
│   │   │   │   ├── imu_console_001.csv
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── 데이터베이스/      # Optimization data
│       ├── 전략별최적화파라미터(주행)/
│       ├── 전략별최적화결과(주행)/
│       ├── 전략별최적화그래프(주행)/
│       └── ...
│
├── db/
│   └── imu_data.db         # SQLite database
│
└── archive/               # Completed migration scripts
    ├── migration.py
    └── ...
```

### File Naming Convention

#### Test Data Files
Format: `{sensor_type}_{position}_{sequence_id}.{extension}`

Examples:
- `imu_console_001.csv`
- `imu_passenger_rear_002.csv`
- `imu_headrest_001.csv`

#### Optimization Parameter Files
Format: `Strategy{strategy}_{subject_id}_{scenario}_{sensor_setting}_{data_type}_{parameter_type}.m`

Examples:
- `Strategy0_sub01_lw_H-IMU_N-VV_주행_fullopt.m`
- `Strategy1_sub02_slc_H-IMU_V-V_주행+휴식_3opt.m`

#### Optimization Result Files
Format: `{model_name}_Strategy{strategy}_{subject_id}_{scenario}_{sensor_setting}_{data_type}_{parameter_type}.mat`

#### Optimization Visualization Files
Format: `{visualization_type}_{model_name?}_Strategy{strategy}_{subject_id}_{scenario}_{sensor_setting}_{data_type}_{parameter_type}.png`

---

## Data Flow

### Test Data Flow

1. **Data Collection**: CSV files and metadata.json created in `data/{project}/{date}_{scenario}/{test_id}_{subject}/`

2. **File Monitoring**: `data_watcher.py` detects new/modified files

3. **Indexing**: `database.scan_and_index_data()` processes metadata.json files:
   - Parses metadata.json
   - Creates/updates experiments, tests, sensors records
   - Calculates file hashes for duplicate detection

4. **Database Storage**: Data stored in SQLite with relationships maintained

5. **Web Access**: Dashboard queries database and displays data

### Optimization Data Flow

1. **File Detection**: `.m`, `.mat`, `.png` files in `data/데이터베이스/` directories

2. **Indexing**: `database.scan_and_index_optimization_data()`:
   - Scans optimization directories
   - Parses filenames to extract metadata
   - Creates parameter records with junction table links
   - Links results and visualizations to parameters

3. **Search**: API queries optimization tables with filters

4. **Visualization**: Web URLs generated for PNG files served via `/api/optimization/files/`

---

## Development Guidelines

### Code Style
- Follow Python PEP 8 conventions
- Use type hints where appropriate
- Document functions with docstrings
- Use Korean comments for user-facing features

### Database Operations
- Always use context managers (`with sqlite3.connect(...)`)
- Use transactions for multi-step operations
- Handle Unicode normalization (NFC) for file paths
- Use parameterized queries to prevent SQL injection

### Error Handling
- Return structured JSON responses from APIs
- Log errors appropriately
- Provide user-friendly error messages in Korean

### Testing
- Test API endpoints with `test_api.py`
- Verify database operations manually
- Check file watching functionality

### Deployment
- Database backups: Automatic backups created before major operations
- Docker: Use `docker-compose up -d` for production
- Environment variables: Consider moving password to environment variable

### Adding New Features
1. Update `FEATURES.md` with feature status
2. Update this `PROJECT_SPEC.md` if architecture changes
3. Update `API_DOCUMENTATION.md` for new endpoints
4. Update `USER_GUIDE_KR.md` for user-facing changes

---

## Key Decisions & Rationale

### Why SQLite?
- Simple deployment (single file)
- No external dependencies
- Sufficient for research team scale
- Easy backup (copy .db file)

### Why Junction Tables for Optimization Parameters?
- Parameters can be linked to multiple subjects/scenarios/sensors
- Strategy-specific linking logic (Strategy 0-4)
- Flexible querying without denormalization

### Why File Watching Instead of Scheduled Scans?
- Real-time updates
- Lower resource usage
- Immediate feedback when new data arrives

### Why Plotly Dash?
- Python-native (no separate frontend build)
- Interactive graphs out of the box
- Rapid prototyping
- Built-in Flask server

---

## Future Considerations

### Potential Enhancements
1. **Multi-user Support**: User accounts, permissions
2. **Data Export**: Export filtered data as CSV/Excel
3. **Advanced Visualization**: 3D plots, correlation matrices
4. **Notification System**: Email alerts for new data
5. **Database Migration Tool**: GUI for schema migrations
6. **API Authentication**: Token-based authentication for API access
7. **PostgreSQL Migration**: If scale requires it

### Performance Optimizations
- Implement caching for frequent queries
- Add pagination to API responses
- Optimize database queries with better indexes
- Consider connection pooling if moving to PostgreSQL

---

## References

- **Feature List**: See `FEATURES.md` for detailed feature tracking
- **API Details**: See `API_DOCUMENTATION.md` for complete API reference
- **User Guide**: See `USER_GUIDE_KR.md` for end-user documentation
- **File Naming**: See `FILENAME_CONVENTION.md` for naming standards

---

**Document Maintenance**: This specification should be updated whenever:
- Major features are completed
- Architecture changes are made
- Database schema is modified
- New APIs are added
- Significant design decisions are made

**Last Review**: Review this document monthly or after major feature releases.


