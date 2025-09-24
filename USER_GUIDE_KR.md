# Mobis Dashboard 사용자 가이드 (한국어)

## 📋 시스템 개요

Mobis Dashboard는 실험 데이터를 자동으로 관리하고 시각화하는 웹 기반 시스템입니다. 이 시스템을 통해 실험 데이터를 쉽게 검색하고 분석할 수 있습니다.

## 🚀 시스템 시작하기

### 1. 웹 인터페이스 접속
- 브라우저에서 `http://localhost:8050` (또는 서버 주소) 접속
- 비밀번호: `mobis1234` 입력 후 로그인

### 2. 기본 화면 구성
- **좌측 패널**: 실험 선택 및 설정
- **메인 화면**: 데이터 시각화 그래프
- **우측 하단**: 데이터 요약 정보

## 📊 데이터 시각화 사용법

### 1단계: 실험 선택
1. 좌측 패널에서 "실험 선택" 드롭다운 클릭
2. 원하는 실험 선택 (예: motion_sickness - 2024-08-11 - single_lane_change)

### 2단계: 테스트 선택
1. "테스트 선택" 드롭다운에서 특정 테스트 선택
2. 피험자 정보와 센서 개수 확인

### 3단계: 센서 선택
1. "센서 선택" 체크리스트에서 비교할 센서들 선택
2. 각 센서의 위치와 샘플링 레이트 확인

### 4단계: 데이터 타입 선택
- **가속도**: X, Y, Z축 가속도 데이터
- **각속도**: X, Y, Z축 각속도 데이터

### 5단계: 데이터 로드
1. "데이터 로드" 버튼 클릭
2. 그래프에서 데이터 확인
3. 우측 하단 패널에서 데이터 요약 정보 확인

## 🔍 API를 통한 데이터 검색

### 기본 검색 명령어

```bash
# 모든 실험 검색
curl "http://localhost:8050/api/search/tests"

# 피험자별 검색
curl "http://localhost:8050/api/search/tests?subject=정현용"

# 시나리오별 검색
curl "http://localhost:8050/api/search/tests?scenario=single_lane_change"

# 날짜별 검색
curl "http://localhost:8050/api/search/tests?date=2024-08-11"
```

### 실험 파일 경로 조회

```bash
# 특정 실험의 파일 경로 조회
curl "http://localhost:8050/api/tests/1/paths"
```

## 📁 파일 명명 규칙

### 디렉토리 구조
```
data/
└── motion_sickness/                    # 프로젝트 폴더
    ├── 2024-08-11_single_lane_change/  # 실험 폴더 (날짜_시나리오)
    │   ├── test_001_sub01_정현용/      # 테스트 폴더 (test_순서_sub번호_피험자명)
    │   │   ├── metadata.json           # 메타데이터 파일
    │   │   ├── imu_console_001.csv     # 센서 데이터 파일
    │   │   └── imu_passenger_rear_002.csv
    │   └── test_002_sub02_최지웅/
    └── 2024-08-12_stop_and_go/
```

### 파일 명명 규칙

#### 센서 파일
- **형식**: `{센서유형}_{위치}_{순서}.csv`
- **예시**: 
  - `imu_console_001.csv` - 콘솔 위치의 IMU 센서
  - `imu_dashboard_002.csv` - 대시보드 위치의 IMU 센서
  - `imu_passenger_rear_003.csv` - 승객석 후방 위치의 IMU 센서

#### 센서 위치 표준
- `console` - 콘솔
- `dashboard` - 대시보드
- `passenger_rear` - 승객석 후방
- `roof` - 지붕
- `driver_seat` - 운전석
- `passenger_seat` - 승객석

#### 시나리오 표준
- `single_lane_change` - 단일 차선 변경
- `stop_and_go` - 정지 및 출발
- `long_wave` - 장파 주행

## 📝 메타데이터 파일 구조

각 테스트 폴더에는 `metadata.json` 파일이 포함되어야 합니다:

```json
{
  "project": "motion_sickness",
  "experiment": {
    "id": "2024-08-11_single_lane_change",
    "date": "2024-08-11",
    "scenario": "single_lane_change",
    "description": "멀미 연구를 위한 단일 차선 변경 기동"
  },
  "test": {
    "id": "test_001_sub01_정현용",
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
    }
  ],
  "data_quality": {
    "completeness": 0.98,
    "anomalies": 3,
    "notes": "45.2초에서 데이터에 미세한 간격 발생"
  }
}
```

## 🔧 새로운 실험 데이터 추가

### 1. 폴더 구조 생성
```
data/motion_sickness/2024-08-15_single_lane_change/test_001_sub01_김철수/
```

### 2. 센서 파일 추가
- 파일명 규칙에 따라 센서 데이터 파일 추가
- 예: `imu_console_001.csv`, `imu_dashboard_002.csv`

### 3. 메타데이터 파일 생성
- `metadata.json` 파일을 위의 구조에 따라 생성
- 모든 센서 정보를 정확히 입력

### 4. 자동 인덱싱 확인
- 시스템이 자동으로 새로운 데이터를 감지하고 데이터베이스에 추가
- 웹 인터페이스에서 새 실험이 나타나는지 확인

## 📊 데이터 분석 팁

### 그래프 사용법
- **줌**: 마우스 휠로 확대/축소
- **범위 선택**: 드래그로 특정 구간 선택
- **센서 on/off**: 범례에서 센서 클릭하여 표시/숨김
- **데이터 포인트**: 마우스 오버로 정확한 값 확인

### 데이터 요약 정보
- **샘플 수**: 전체 데이터 포인트 개수
- **지속 시간**: 실험 총 시간 (초)
- **샘플링 레이트**: 초당 데이터 포인트 수 (Hz)

## 🚨 문제 해결

### 웹 인터페이스가 로드되지 않는 경우
1. 서버가 실행 중인지 확인
2. 포트 8050이 사용 가능한지 확인
3. 브라우저 캐시 삭제 후 재시도

### 데이터가 표시되지 않는 경우
1. 파일 경로가 올바른지 확인
2. CSV 파일 형식이 올바른지 확인
3. 메타데이터 파일이 올바른 형식인지 확인

### API가 응답하지 않는 경우
1. `curl http://localhost:8050/api/health`로 서버 상태 확인
2. 네트워크 연결 확인
3. 방화벽 설정 확인

## 📞 지원 및 문의

시스템 사용 중 문제가 발생하면:
1. 이 가이드의 문제 해결 섹션 참조
2. `test_api.py` 스크립트로 API 테스트
3. 시스템 관리자에게 문의

## 🔄 시스템 업데이트

### 데이터베이스 새로고침
- 웹 인터페이스에서 "🔄 DB 새로고침" 버튼 클릭
- 새로운 데이터가 자동으로 인덱싱됨

### 로그 확인
- 시스템 로그는 콘솔에서 확인 가능
- 오류 발생 시 로그 메시지 확인

---

이 가이드를 통해 Mobis Dashboard를 효과적으로 활용하여 실험 데이터를 관리하고 분석할 수 있습니다.
