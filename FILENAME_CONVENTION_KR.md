# 데이터 파일 네이밍 컨벤션

## 개요

This document defines the standardized naming convention for data files in the multi-project research data management system. The convention ensures files are self-describing, database-independent, and scalable across different research projects.

## 디렉토리 구조

```
data/
├── {project_name}/                        # 프로젝트별 폴더
│   ├── {date}_{scenario}/                 # 실험 폴더
│   │   ├── {test_id}_{subject}/           # 테스트 세션 폴더
│   │   │   ├── metadata.json              # 테스트 메타데이터
│   │   │   ├── {sensor_file}              # 센서 데이터 파일
│   │   │   └── ...
│   │   └── ...
│   ├── {date}_{scenario_2}/               # 같은 날 여러 시나리오
│   └── ...
├── {project_name_2}/
└── shared/                                # 프로젝트 간 공유 데이터
    ├── calibration/
    └── reference/
```

## 파일 명명 규칙

### 일반 형식

```
{sensor_type}_{position}_{sequence_id}.{extension}
```

### 구성 요소

| 구성 요소 | 설명 | 예시 | 규칙 |
|-----------|------|------|------|
| `sensor_type` | 센서 유형 | `imu`, `camera`, `gps`, `lidar`, `can` | 소문자, 언더스코어로 구분 |
| `position` | 물리적 위치 | `console`, `dashboard`, `passenger_rear`, `roof` | 소문자, 언더스코어로 구분 |
| `sequence_id` | 고유 식별자 | `001`, `002`, `003` | 0으로 패딩된 3자리 숫자 |
| `extension` | 파일 형식 | `csv`, `mp4`, `json`, `bin` | 표준 파일 확장자 |

### 예시

#### IMU 센서 파일
```
imu_console_001.csv          # 콘솔 위치의 IMU 센서, 첫 번째 센서
imu_dashboard_002.csv        # 대시보드 위치의 IMU 센서, 두 번째 센서
imu_passenger_rear_003.csv   # 승객석 후방 위치의 IMU 센서, 세 번째 센서
imu_roof_001.csv            # 지붕 위치의 IMU 센서, 첫 번째 센서
```

#### 카메라 파일
```
camera_dashboard_001.mp4     # 대시보드 카메라 영상
camera_rear_002.mp4         # 후방 카메라 영상
camera_side_left_001.mp4    # 좌측 사이드 카메라 영상
```

#### 기타 센서 유형
```
gps_roof_001.csv           # 지붕의 GPS 수신기
lidar_front_001.bin        # 전방 LiDAR 데이터
can_obd_001.csv           # CAN 버스 OBD 데이터
```

## 디렉토리 명명 규칙

### 프로젝트 폴더
```
{project_name}
```
- **형식**: 언더스코어가 있는 소문자
- **예시**: `motion_sickness`, `driver_behavior`, `vehicle_dynamics`

### 실험 폴더
```
{date}_{scenario}
```
- **형식**: `YYYY-MM-DD_scenario_name`
- **날짜**: ISO 형식 (YYYY-MM-DD)
- **시나리오**: 언더스코어가 있는 소문자
- **예시**: 
  - `2024-06-30_single_lane_change`
  - `2024-06-30_stop_and_go` (같은 날, 다른 시나리오)
  - `2024-07-01_highway_driving`

**참고**: 같은 날에 여러 시나리오가 수행되는 경우, 각 시나리오는 별도의 폴더를 가집니다:
- `2024-06-30_single_lane_change`
- `2024-06-30_stop_and_go`
- `2024-06-30_highway_driving`

### 테스트 세션 폴더
```
{test_id}_{subject}
```
- **형식**: `test_{sequence}_{subject_name}`
- **테스트 ID**: 0으로 패딩된 3자리 숫자
- **피험자**: 전체 이름 (한국어 또는 영어)
- **예시**:
  - `test_001_정현용`
  - `test_002_최지웅`
  - `test_001_John_Doe`

## 메타데이터 파일 구조

각 테스트 세션 폴더는 다음 구조를 가진 `metadata.json` 파일을 포함해야 합니다:

```json
{
  "project": "motion_sickness",
  "experiment": {
    "id": "2024-06-30_single_lane_change",
    "date": "2024-06-30",
    "scenario": "single_lane_change",
    "description": "멀미 연구를 위한 단일 차선 변경 기동"
  },
  "test": {
    "id": "test_001_정현용",
    "sequence": 1,
    "subject": "정현용",
    "subject_id": "S001",
    "duration_sec": 120.5,
    "notes": "피험자가 경미한 불편함을 보고함"
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
    "notes": "45.2초에서 데이터에 미세한 간격 발생"
  }
}
```

## 완전한 예시

### 디렉토리 구조
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

### 파일 내용
- `imu_console_001.csv`: 콘솔 위치의 IMU 데이터
- `imu_passenger_rear_002.csv`: 승객석 후방 위치의 IMU 데이터
- `metadata.json`: 완전한 테스트 세션 메타데이터

## 명명 규칙

### 문자 제한
- **허용**: 문자 (a-z, A-Z), 숫자 (0-9), 언더스코어 (_), 하이픈 (-)
- **금지**: 공백, 특수 문자, 파일명의 유니코드 문자
- **대소문자**: 일관성을 위해 소문자 사용

### 길이 제한
- **파일명**: 최대 255자
- **디렉토리명**: 최대 255자
- **경로 길이**: 플랫폼 의존적 (Windows: 260자, Unix: 4096자)

### 예약된 이름
다음 예약된 이름은 피하세요:
- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` ~ `COM9`
- `LPT1` ~ `LPT9`

## 현재 구조에서의 마이그레이션

### 현재 형식
```
data/experiment_pilot/Day1/0630_test2_Single Lane Change_정현용/IMU_01.csv
```

### 새로운 형식
```
data/motion_sickness/2024-06-30_single_lane_change/test_002_정현용/imu_console_001.csv
```

### 마이그레이션 매핑
| 현재 구성 요소 | 새로운 구성 요소 | 예시 |
|----------------|------------------|------|
| `experiment_pilot` | `motion_sickness` | 프로젝트 이름 |
| `Day1` | `2024-06-30` | 날짜 추출 |
| `0630_test2_Single Lane Change_정현용` | `test_002_정현용` | 테스트 ID + 피험자 |
| `IMU_01.csv` | `imu_console_001.csv` | 자체 설명적 이름 |

## 검증 규칙

### 파일 명명 검증
1. 패턴과 일치해야 함: `{sensor_type}_{position}_{sequence_id}.{extension}`
2. 센서 유형은 승인된 목록에 있어야 함
3. 위치는 설명적이고 일관되어야 함
4. 시퀀스 ID는 0으로 패딩된 3자리 숫자여야 함
5. 확장자는 센서 유형에 적합해야 함

### 디렉토리 명명 검증
1. 프로젝트 이름: 언더스코어만 있는 소문자
2. 실험 폴더: `YYYY-MM-DD_scenario_name` 형식
3. 테스트 폴더: `test_{sequence}_{subject}` 형식
4. 특수 문자나 공백 없음

## 장점

### 자체 설명적
- 파일 이름에 의미 있는 정보 포함
- 기본 이해를 위한 데이터베이스 의존성 없음
- 센서 유형과 위치를 쉽게 식별 가능

### 확장 가능
- 새로운 센서 유형 추가 용이
- 새로운 프로젝트 추가 간단
- 모든 연구 영역에 걸쳐 일관성 유지

### 사람이 읽기 쉬움
- 직관적인 파일 구성
- 탐색하고 이해하기 쉬움
- 명확한 계층 구조와 관계

### 데이터베이스 친화적
- 자동화된 처리를 위한 일관된 패턴
- 파싱하고 인덱싱하기 쉬움
- 참조 무결성 유지

## 향후 확장

### 추가 센서 유형
- `eeg_*` - 뇌파 검사
- `ecg_*` - 심전도
- `emg_*` - 근전도
- `pressure_*` - 압력 센서
- `temperature_*` - 온도 센서

### 추가 파일 유형
- `config_*` - 설정 파일
- `calibration_*` - 보정 데이터
- `reference_*` - 참조 측정값
- `log_*` - 시스템 로그

---

*이 명세서는 버전 1.0이며, 새로운 요구사항이 나타나면 업데이트되어야 합니다.*
