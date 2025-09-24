# Mobis Dashboard API Documentation

## 개요 (Overview)

Mobis Dashboard는 실험 데이터를 자동으로 관리하고 쿼리할 수 있는 REST API를 제공합니다. 이 API를 통해 특정 실험을 검색하고 해당 실험 파일의 경로를 받을 수 있습니다.

The Mobis Dashboard provides a REST API for automated experiment data management and querying. Through this API, you can search for specific experiments and receive paths to the corresponding experiment files.

## 🚀 API 기본 정보 (Basic API Information)

- **Base URL**: `http://localhost:8050` (또는 서버 주소)
- **Content Type**: `application/json`
- **Authentication**: 현재 없음 (웹 인터페이스는 비밀번호 보호)

## 📋 API 엔드포인트 (API Endpoints)

### 1. 시스템 상태 확인 (Health Check)

**GET** `/api/health`

시스템이 정상적으로 작동하는지 확인합니다.

**Response:**
```json
{
  "status": "success",
  "message": "API is running",
  "version": "1.0.0"
}
```

**사용 예시:**
```bash
curl http://localhost:8050/api/health
```

### 2. 실험 검색 (Search Experiments)

**GET** `/api/search/tests`

다양한 조건으로 실험을 검색할 수 있습니다.

**Query Parameters:**
- `subject` (선택): 피험자 이름으로 검색
- `sensor_id` (선택): 센서 ID로 검색
- `scenario` (선택): 시나리오로 검색 (예: single_lane_change, stop_and_go, long_wave)
- `date` (선택): 날짜로 검색 (YYYY-MM-DD 형식)
- `project` (선택): 프로젝트명으로 검색

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": 1,
      "test_id": "test_001_sub01_정현용",
      "test_name": "test_001_sub01_정현용",
      "sequence": 1,
      "subject": "정현용",
      "subject_id": "S001",
      "duration_sec": 120.5,
      "notes": "Subject reported mild discomfort",
      "imu_count": 3,
      "created_at": "2024-08-11 10:30:00",
      "project": "motion_sickness",
      "experiment_id": "2024-08-11_single_lane_change",
      "date": "2024-08-11",
      "scenario": "single_lane_change",
      "description": "Single lane change maneuver for motion sickness study"
    }
  ]
}
```

**사용 예시:**

```bash
# 모든 실험 검색
curl "http://localhost:8050/api/search/tests"

# 피험자별 검색
curl "http://localhost:8050/api/search/tests?subject=정현용"

# 시나리오별 검색
curl "http://localhost:8050/api/search/tests?scenario=single_lane_change"

# 복합 검색
curl "http://localhost:8050/api/search/tests?subject=정현용&scenario=single_lane_change"

# 날짜별 검색
curl "http://localhost:8050/api/search/tests?date=2024-08-11"
```

### 3. 실험 파일 경로 조회 (Get Experiment File Paths)

**GET** `/api/tests/{test_id}/paths`

특정 실험의 모든 파일 경로를 조회합니다.

**Path Parameters:**
- `test_id`: 실험 ID (정수)

**Response:**
```json
{
  "status": "success",
  "data": {
    "test_id": 1,
    "test_id_str": "test_001_sub01_정현용",
    "test_name": "test_001_sub01_정현용",
    "sequence": 1,
    "subject": "정현용",
    "subject_id": "S001",
    "duration_sec": 120.5,
    "project": "motion_sickness",
    "experiment_id": "2024-08-11_single_lane_change",
    "experiment_date": "2024-08-11",
    "scenario": "single_lane_change",
    "description": "Single lane change maneuver for motion sickness study",
    "experiment_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용",
    "metadata_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용/metadata.json",
    "sensor_files": [
      {
        "sensor_id": "imu_console_001",
        "sensor_type": "imu",
        "position": "console",
        "sequence": 1,
        "sample_rate_hz": 100.0,
        "file_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용/imu_console_001.csv"
      },
      {
        "sensor_id": "imu_passenger_rear_002",
        "sensor_type": "imu",
        "position": "passenger_rear",
        "sequence": 2,
        "sample_rate_hz": 100.0,
        "file_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용/imu_passenger_rear_002.csv"
      }
    ]
  }
}
```

**사용 예시:**
```bash
curl "http://localhost:8050/api/tests/1/paths"
```

### 4. 실험 센서 정보 조회 (Get Experiment Sensor Information)

**GET** `/api/tests/{test_id}/sensors`

특정 실험의 센서 정보를 조회합니다.

**Path Parameters:**
- `test_id`: 실험 ID (정수)

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": 1,
      "sensor_id": "imu_console_001",
      "sensor_type": "imu",
      "position": "console",
      "sequence": 1,
      "sample_rate_hz": 100.0,
      "file_name": "imu_console_001.csv",
      "file_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용/imu_console_001.csv"
    },
    {
      "id": 2,
      "sensor_id": "imu_passenger_rear_002",
      "sensor_type": "imu",
      "position": "passenger_rear",
      "sequence": 2,
      "sample_rate_hz": 100.0,
      "file_name": "imu_passenger_rear_002.csv",
      "file_path": "/path/to/data/motion_sickness/2024-08-11_single_lane_change/test_001_sub01_정현용/imu_passenger_rear_002.csv"
    }
  ]
}
```

**사용 예시:**
```bash
curl "http://localhost:8050/api/tests/1/sensors"
```

## 🔍 실제 사용 예시 (Real Usage Examples)

### Python을 사용한 API 호출

```python
import requests
import json

# API 기본 URL
BASE_URL = "http://localhost:8050"

def search_experiments(subject=None, scenario=None, date=None):
    """실험 검색"""
    params = {}
    if subject:
        params['subject'] = subject
    if scenario:
        params['scenario'] = scenario
    if date:
        params['date'] = date
    
    response = requests.get(f"{BASE_URL}/api/search/tests", params=params)
    return response.json()

def get_experiment_paths(test_id):
    """실험 파일 경로 조회"""
    response = requests.get(f"{BASE_URL}/api/tests/{test_id}/paths")
    return response.json()

# 사용 예시
# 1. 정현용 피험자의 모든 실험 검색
experiments = search_experiments(subject="정현용")
print(f"Found {experiments['count']} experiments")

# 2. 첫 번째 실험의 파일 경로 조회
if experiments['data']:
    test_id = experiments['data'][0]['id']
    paths = get_experiment_paths(test_id)
    print(f"Experiment path: {paths['data']['experiment_path']}")
    print(f"Metadata path: {paths['data']['metadata_path']}")
    for sensor in paths['data']['sensor_files']:
        print(f"Sensor {sensor['sensor_id']}: {sensor['file_path']}")
```

### JavaScript를 사용한 API 호출

```javascript
// 실험 검색
async function searchExperiments(subject, scenario) {
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    if (scenario) params.append('scenario', scenario);
    
    const response = await fetch(`http://localhost:8050/api/search/tests?${params}`);
    return await response.json();
}

// 실험 파일 경로 조회
async function getExperimentPaths(testId) {
    const response = await fetch(`http://localhost:8050/api/tests/${testId}/paths`);
    return await response.json();
}

// 사용 예시
searchExperiments("정현용", "single_lane_change")
    .then(data => {
        console.log(`Found ${data.count} experiments`);
        if (data.data.length > 0) {
            return getExperimentPaths(data.data[0].id);
        }
    })
    .then(paths => {
        if (paths) {
            console.log("Experiment paths:", paths.data);
        }
    });
```

## 📊 데이터 구조 (Data Structure)

### 실험 데이터 (Experiment Data)
- `id`: 고유 실험 ID
- `test_id`: 테스트 식별자
- `subject`: 피험자 이름
- `scenario`: 실험 시나리오 (single_lane_change, stop_and_go, long_wave)
- `date`: 실험 날짜
- `project`: 프로젝트명
- `duration_sec`: 실험 지속 시간 (초)
- `imu_count`: IMU 센서 개수

### 센서 데이터 (Sensor Data)
- `sensor_id`: 센서 식별자
- `sensor_type`: 센서 유형 (imu, camera, gps 등)
- `position`: 센서 위치 (console, dashboard, passenger_rear 등)
- `sample_rate_hz`: 샘플링 레이트
- `file_path`: 센서 데이터 파일 경로

## 🚨 오류 처리 (Error Handling)

API는 표준 HTTP 상태 코드를 사용합니다:

- `200 OK`: 성공
- `404 Not Found`: 요청한 리소스를 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

**오류 응답 예시:**
```json
{
  "status": "error",
  "message": "Test with ID 999 not found"
}
```

## 🔧 API 테스트 (API Testing)

시스템에 포함된 `test_api.py` 스크립트를 사용하여 API를 테스트할 수 있습니다:

```bash
# 기본 테스트 실행
python test_api.py

# 다른 서버 주소로 테스트
python test_api.py http://your-server:8050
```

## 📝 주의사항 (Notes)

1. **파일 경로**: API에서 반환되는 파일 경로는 서버의 절대 경로입니다.
2. **한글 지원**: 피험자 이름과 시나리오는 한글을 지원합니다.
3. **실시간 업데이트**: 새로운 실험 데이터가 추가되면 자동으로 API에서 검색 가능합니다.
4. **대소문자 구분**: 검색 시 대소문자를 구분합니다.

## 🆘 문제 해결 (Troubleshooting)

### API가 응답하지 않는 경우
1. 서버가 실행 중인지 확인: `curl http://localhost:8050/api/health`
2. 포트 8050이 사용 가능한지 확인
3. 방화벽 설정 확인

### 검색 결과가 없는 경우
1. 데이터베이스가 최신 상태인지 확인
2. 검색 조건이 올바른지 확인
3. 한글 인코딩 문제 확인

### 파일 경로에 접근할 수 없는 경우
1. 파일이 실제로 존재하는지 확인
2. 파일 권한 확인
3. 서버와 클라이언트의 파일 시스템 차이 확인

---

이 API 문서를 통해 Mobis Dashboard의 실험 데이터를 효율적으로 검색하고 활용할 수 있습니다.
