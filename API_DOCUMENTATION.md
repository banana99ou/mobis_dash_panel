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

---

## 📊 최적화 파라미터 API (Optimization Parameter API)

최적화 파라미터, 결과, 시각화 데이터를 검색하고 조회할 수 있는 API입니다.

### 5. 최적화 파라미터 검색 (Search Optimization Parameters)

**GET** `/api/optimization/parameters`

다양한 조건으로 최적화 파라미터를 검색할 수 있습니다. 모든 쿼리 파라미터는 AND 조건으로 결합됩니다 (모든 조건을 만족하는 결과만 반환).

**Query Parameters:**
- `subject_id` (선택): 피험자 ID로 검색 (예: 'sub01', 'sub02')
- `scenario` (선택): 시나리오로 검색 (예: 'lw', 'slc', 's&g')
- `sensor` (선택): 센서 설정 코드로 검색 (예: 'H-IMU_N-VV', 'H-IMU_V-V')
- `strategy` (선택): 전략 번호로 검색 (0-4, 정수)
- `model` (선택): 모델명으로 검색 (예: 'MSIbase', 'OmanAP')
- `parameter_type` (선택): 파라미터 타입으로 검색 ('fullopt' 또는 '3opt')
- `data_type` (선택): 데이터 타입으로 검색 ('주행' 또는 '주행+휴식')

**Response:**
```json
{
  "status": "success",
  "count": 36,
  "data": [
    {
      "id": 41,
      "strategy_id": 1,
      "parameter_type": "fullopt",
      "data_type": "주행",
      "file_path": "data/motion_sickness/optimization/Driving/Parameter/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/slc_sub09_H-IMU_N-VV_parameters_fullopt.m",
      "file_name": "slc_sub09_H-IMU_N-VV_parameters_fullopt.m",
      "created_at": "2025-11-17 18:29:54",
      "updated_at": "2025-11-18 02:05:56",
      "strategy": {
        "number": 0,
        "name": "BySubjectScenarioSensor",
        "description": "피험자별 + 시나리오별 + 센서 세팅별 최적화"
      },
      "subjects": [
        {
          "id": "sub_009",
          "name": "정예린"
        }
      ],
      "scenarios": ["slc"],
      "sensor_settings": [
        {
          "code": "H-IMU_N-VV",
          "description": "Head IMU, No VV"
        }
      ],
      "results": [
        {
          "id": 155,
          "model_name": "MSIbase",
          "file_path": "data/motion_sickness/optimization/Driving/Results/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/MSIbase_fullopt.mat",
          "file_name": "MSIbase_fullopt.mat",
          "created_at": "2025-11-17 18:30:04"
        },
        {
          "id": 149,
          "model_name": "OmanAP",
          "file_path": "data/motion_sickness/optimization/Driving/Results/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/OmanAP_fullopt.mat",
          "file_name": "OmanAP_fullopt.mat",
          "created_at": "2025-11-17 18:30:04"
        }
      ],
      "visualizations": [
        {
          "id": 187,
          "type": "model_specific",
          "model_name": "MSIbase",
          "file_path": "data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_MSIbase_fullopt.png",
          "file_name": "slc_sub09_MSIbase_fullopt.png",
          "url": "/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_MSIbase_fullopt.png",
          "created_at": "2025-11-17 18:39:20"
        },
        {
          "id": 188,
          "type": "comparison",
          "model_name": null,
          "file_path": "data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png",
          "file_name": "slc_sub09_fullopt.png",
          "url": "/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png",
          "created_at": "2025-11-17 18:39:20"
        }
      ]
    }
  ]
}
```

**사용 예시:**

```bash
# 모든 최적화 파라미터 검색
curl "http://localhost:8050/api/optimization/parameters"

# 피험자별 검색
curl "http://localhost:8050/api/optimization/parameters?subject_id=sub09"

# 시나리오별 검색
curl "http://localhost:8050/api/optimization/parameters?scenario=slc"

# 전략별 검색
curl "http://localhost:8050/api/optimization/parameters?strategy=0"

# 센서 설정별 검색
curl "http://localhost:8050/api/optimization/parameters?sensor=H-IMU_N-VV"

# 모델별 검색
curl "http://localhost:8050/api/optimization/parameters?model=MSIbase"

# 파라미터 타입별 검색
curl "http://localhost:8050/api/optimization/parameters?parameter_type=fullopt"

# 데이터 타입별 검색
curl "http://localhost:8050/api/optimization/parameters?data_type=주행"

# 복합 검색 (모든 조건 AND)
curl "http://localhost:8050/api/optimization/parameters?subject_id=sub09&scenario=slc&strategy=0&parameter_type=fullopt"
```

**시각화 이미지 URL 추출 및 브라우저에서 보기:**

```bash
# 1. 필터링하여 검색 (예: strategy=0, subject_id=sub09, scenario=slc)
curl "http://localhost:8050/api/optimization/parameters?strategy=0&subject_id=sub09&scenario=slc" > response.json

# 2. 응답에서 visualization URL 추출 (grep 사용)
grep -o '"url": "[^"]*"' response.json

# 또는 jq를 사용하여 더 깔끔하게 추출
curl -s "http://localhost:8050/api/optimization/parameters?strategy=0&subject_id=sub09&scenario=slc" | \
  jq -r '.data[].visualizations[].url' | grep -v null

# 3. 추출된 URL을 브라우저에서 열기
# 예시 URL: /api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png
브라우저에서 접근: "http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png"
```

### 6. 최적화 파라미터 상세 정보 조회 (Get Optimization Parameter Detail)

**GET** `/api/optimization/parameters/{parameter_id}`

특정 최적화 파라미터의 상세 정보를 조회합니다. 검색 결과와 동일한 구조이지만, 더 상세한 메타데이터를 포함할 수 있습니다.

**Path Parameters:**
- `parameter_id`: 파라미터 ID (정수)

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 41,
    "strategy_id": 1,
    "parameter_type": "fullopt",
    "data_type": "주행",
    "file_path": "data/motion_sickness/optimization/Driving/Parameter/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/slc_sub09_H-IMU_N-VV_parameters_fullopt.m",
    "file_name": "slc_sub09_H-IMU_N-VV_parameters_fullopt.m",
    "created_at": "2025-11-17 18:29:54",
    "updated_at": "2025-11-18 02:05:56",
    "strategy": {
      "number": 0,
      "name": "BySubjectScenarioSensor",
      "description": "피험자별 + 시나리오별 + 센서 세팅별 최적화"
    },
    "subjects": [
      {
        "id": "sub_009",
        "name": "정예린"
      }
    ],
    "scenarios": ["slc"],
    "sensor_settings": [
      {
        "code": "H-IMU_N-VV",
        "description": "Head IMU, No VV"
      }
    ],
    "results": [
      {
        "id": 155,
        "model_name": "MSIbase",
        "file_path": "data/motion_sickness/optimization/Driving/Results/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/MSIbase_fullopt.mat",
        "file_name": "MSIbase_fullopt.mat",
        "created_at": "2025-11-17 18:30:04"
      }
    ],
    "visualizations": [
      {
        "id": 187,
        "type": "model_specific",
        "model_name": "MSIbase",
        "file_path": "data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_MSIbase_fullopt.png",
        "file_name": "slc_sub09_MSIbase_fullopt.png",
        "url": "/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_MSIbase_fullopt.png",
        "created_at": "2025-11-17 18:39:20"
      },
      {
        "id": 188,
        "type": "comparison",
        "model_name": null,
        "file_path": "data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png",
        "file_name": "slc_sub09_fullopt.png",
        "url": "/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png",
        "created_at": "2025-11-17 18:39:20"
      }
    ]
  }
}
```

**사용 예시:**
```bash
# 파라미터 ID로 상세 정보 조회
curl "http://localhost:8050/api/optimization/parameters/41"

# 응답에서 visualization URL 추출
curl -s "http://localhost:8050/api/optimization/parameters/41" | \
  jq -r '.data.visualizations[].url' | grep -v null
```

### 7. 최적화 파일 서빙 (Serve Optimization Files)

**GET** `/api/optimization/files/{file_path}`

최적화 관련 파일 (PNG 시각화, MAT 결과 파일, M 파라미터 파일 등)을 웹 URL을 통해 제공합니다.

**Path Parameters:**
- `file_path`: 파일 경로 (워크스페이스 루트 기준 상대 경로)

**Response:**
파일 바이너리 데이터 (Content-Type은 파일 확장자에 따라 자동 결정)

**사용 예시:**

**방법 1: API 응답에서 URL 추출 후 브라우저에서 열기**

```bash
# 1. 필터링하여 검색하고 visualization URL 추출
curl -s "http://localhost:8050/api/optimization/parameters?strategy=0&subject_id=sub09&scenario=slc" | \
  jq -r '.data[].visualizations[].url' | grep -v null | head -1

# 출력 예시: /api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png

# 2. 브라우저에서 열기 (Base URL 추가)
# http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png
```

**방법 2: curl로 파일 다운로드**

```bash
# PNG 시각화 파일 다운로드
curl "http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png" --output figure.png

# MAT 결과 파일 다운로드
curl "http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Results/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/MSIbase_fullopt.mat" --output result.mat

# M 파라미터 파일 다운로드
curl "http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Parameter/Strategy0_BySubjectScenarioSensor/slc_sub09/H-IMU_N-VV/slc_sub09_H-IMU_N-VV_parameters_fullopt.m" --output parameter.m
```

**방법 3: 브라우저에서 직접 이미지 보기**

API 응답에서 얻은 `url` 필드를 사용하여 브라우저 주소창에 입력:

```
http://localhost:8050/api/optimization/files/data/motion_sickness/optimization/Driving/Graph/Strategy0_BySubjectScenarioSensor/slc_sub09/slc_sub09_fullopt.png
```

**완전한 워크플로우 예시:**

```bash
# Step 1: 필터링하여 검색
curl -s "http://localhost:8050/api/optimization/parameters?strategy=0&subject_id=sub09&scenario=slc" > response.json

# Step 2: visualization URL 추출 (grep 사용)
grep -o '"url": "[^"]*"' response.json | grep -v null

# Step 3: URL을 변수에 저장하고 브라우저에서 열기 (macOS)
URL=$(curl -s "http://localhost:8050/api/optimization/parameters?strategy=0&subject_id=sub09&scenario=slc" | \
  jq -r '.data[].visualizations[].url' | grep -v null | head -1)
open "http://localhost:8050${URL}"

# 또는 Linux의 경우
# xdg-open "http://localhost:8050${URL}"
```

**참고:**
- 시각화 파일의 `url` 필드는 이 엔드포인트를 가리킵니다
- 파일 경로는 워크스페이스 루트 기준 상대 경로여야 합니다
- 워크스페이스 밖의 파일은 접근할 수 없습니다 (보안)
- **중요**: API 응답에서 얻은 `url` 필드를 그대로 사용하세요. 문서의 예시 경로는 참고용이며, 실제 경로는 API 응답을 확인해야 합니다

---

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

def search_optimization_parameters(subject_id=None, scenario=None, strategy=None, model=None):
    """최적화 파라미터 검색"""
    params = {}
    if subject_id:
        params['subject_id'] = subject_id
    if scenario:
        params['scenario'] = scenario
    if strategy is not None:
        params['strategy'] = strategy
    if model:
        params['model'] = model
    
    response = requests.get(f"{BASE_URL}/api/optimization/parameters", params=params)
    return response.json()

def get_optimization_parameter_detail(parameter_id):
    """최적화 파라미터 상세 정보 조회"""
    response = requests.get(f"{BASE_URL}/api/optimization/parameters/{parameter_id}")
    return response.json()

# 최적화 파라미터 사용 예시
# 1. Strategy 0 파라미터 검색 (필터링)
params = search_optimization_parameters(strategy=0, subject_id="sub09", scenario="slc")
print(f"Found {params['count']} parameters")

# 2. 첫 번째 파라미터의 상세 정보 및 시각화 URL 조회
if params['data']:
    param_id = params['data'][0]['id']
    detail = get_optimization_parameter_detail(param_id)
    print(f"Parameter file: {detail['data']['file_path']}")
    for viz in detail['data']['visualizations']:
        if viz.get('url'):
            full_url = f"{BASE_URL}{viz['url']}"
            print(f"Visualization URL: {full_url}")
            # 브라우저에서 열기 (선택사항)
            # import webbrowser
            # webbrowser.open(full_url)
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

// 최적화 파라미터 검색
async function searchOptimizationParameters(subjectId, scenario, strategy) {
    const params = new URLSearchParams();
    if (subjectId) params.append('subject_id', subjectId);
    if (scenario) params.append('scenario', scenario);
    if (strategy !== undefined) params.append('strategy', strategy);
    
    const response = await fetch(`http://localhost:8050/api/optimization/parameters?${params}`);
    return await response.json();
}

// 최적화 파라미터 상세 정보 조회
async function getOptimizationParameterDetail(parameterId) {
    const response = await fetch(`http://localhost:8050/api/optimization/parameters/${parameterId}`);
    return await response.json();
}

// 최적화 파라미터 사용 예시
searchOptimizationParameters("sub09", "slc", 0)
    .then(data => {
        console.log(`Found ${data.count} parameters`);
        if (data.data.length > 0) {
            return getOptimizationParameterDetail(data.data[0].id);
        }
    })
    .then(detail => {
        if (detail) {
            console.log("Parameter detail:", detail.data);
            detail.data.visualizations.forEach(viz => {
                if (viz.url) {
                    const fullUrl = `http://localhost:8050${viz.url}`;
                    console.log(`Visualization: ${fullUrl}`);
                    // 브라우저에서 새 탭으로 열기 (선택사항)
                    // window.open(fullUrl, '_blank');
                }
            });
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

### 최적화 파라미터 데이터 (Optimization Parameter Data)
- `id`: 파라미터 고유 ID
- `strategy_id`: 전략 ID
- `strategy`: 전략 정보 객체
  - `number`: 전략 번호 (0-4)
  - `name`: 전략 이름
  - `description`: 전략 설명
- `parameter_type`: 파라미터 타입 ('fullopt' 또는 '3opt')
- `data_type`: 데이터 타입 ('주행' 또는 '주행+휴식')
- `file_path`: 파라미터 파일 경로 (.m 파일)
- `file_name`: 파일명
- `file_hash`: 파일 해시값
- `metadata`: 메타데이터 (JSON 문자열)
- `subjects`: 피험자 ID 배열 (junction table에서)
- `scenarios`: 시나리오 배열 (junction table에서)
- `sensor_settings`: 센서 설정 배열 (junction table에서)
  - `code`: 센서 설정 코드
  - `description`: 설명
  - `components`: 센서 구성 요소
- `results`: 결과 파일 배열
  - `id`: 결과 ID
  - `model_name`: 모델명
  - `file_path`: 결과 파일 경로 (.mat 파일)
  - `file_hash`: 파일 해시값
  - `metadata`: 메타데이터 (RMSE, R2 등)
- `visualizations`: 시각화 파일 배열
  - `id`: 시각화 ID
  - `type`: 시각화 타입 ('model_specific' 또는 'comparison')
  - `model_name`: 모델명 (model_specific인 경우)
  - `file_path`: 시각화 파일 경로 (.png 파일)
  - `url`: 웹 URL (파일 서빙 엔드포인트)

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

1. **파일 경로**: 
   - Raw data API: 반환되는 파일 경로는 서버의 절대 경로입니다.
   - Optimization API: 시각화 파일은 웹 URL (`/api/optimization/files/...`)을 반환하며, 파라미터 및 결과 파일은 절대 경로를 반환합니다.
2. **한글 지원**: 피험자 이름과 시나리오는 한글을 지원합니다.
3. **실시간 업데이트**: 새로운 실험 데이터가 추가되면 자동으로 API에서 검색 가능합니다.
4. **대소문자 구분**: 검색 시 대소문자를 구분합니다.
5. **검색 조건**: 최적화 파라미터 검색의 모든 쿼리 파라미터는 AND 조건으로 결합됩니다 (현재 OR 조건은 지원하지 않습니다).
6. **전략 번호**: 최적화 전략 번호는 0-4 사이의 정수입니다.

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
