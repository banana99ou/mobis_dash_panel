# Mobis Dashboard Panel

**자동화된 실험 데이터 데이터베이스 관리 시스템**  
Automated Experiment Data Database Management System

## 📋 시스템 개요

### 목적
- 다중 센서로부터 수집된 실험 데이터의 자동 관리 및 인덱싱
- 웹 기반 대시보드를 통한 직관적인 데이터 시각화
- REST API를 통한 프로그래밍 방식 데이터 쿼리
- 실험 시나리오별 데이터 분류 및 비교 분석

### 핵심 기능
- **자동 데이터 수집**: 파일 시스템 모니터링을 통한 실시간 데이터 인덱싱
- **웹 대시보드**: Plotly Dash 기반 인터랙티브 데이터 시각화
- **REST API**: 실험 검색 및 파일 경로 조회 API
- **다중 형식 지원**: 레거시 및 새로운 메타데이터 형식 지원
- **한국어 지원**: 완전한 한국어 인터페이스 및 문서화

### 실험 환경
- **실험 유형**: Single Lane Change, Stop and Go, Long Wave
- **센서 구성**: 다중 IMU 센서 동시 설치
- **데이터 형식**: CSV 파일 (가속도, 각속도 등)
- **서버 환경**: Docker 컨테이너 또는 직접 실행

## 🏗️ 시스템 아키텍처

### 기술 스택
- **Frontend**: Plotly Dash
- **Backend**: Python (Dash 내장 Flask 서버)
- **Database**: SQLite
- **Visualization**: Plotly
- **File Monitoring**: Python watchdog
- **Containerization**: Docker

### 현재 디렉토리 구조
```
mobis_dash_panel/
├── app.py                    # 메인 Dash 애플리케이션
├── database.py              # 데이터베이스 관리 (IMUDatabase 클래스)
├── data_watcher.py          # 자동 파일 모니터링
├── utils.py                 # 데이터 처리 유틸리티
├── test_api.py              # API 테스트 스크립트
├── requirements.txt         # Python 의존성
├── docker-compose.yml       # Docker 배포 설정
├── Dockerfile              # 컨테이너 빌드 설정
├── API_DOCUMENTATION.md    # REST API 문서
├── USER_GUIDE_KR.md        # 한국어 사용자 가이드
├── FILENAME_CONVENTION.md  # 파일 명명 규칙 (영어)
├── FILENAME_CONVENTION_KR.md # 파일 명명 규칙 (한국어)
├── data/                   # 실험 데이터 저장소
│   ├── motion_sickness/    # 멀미 연구 프로젝트
│   └── ingest/            # 레거시 데이터
├── db/
│   └── imu_data.db        # SQLite 데이터베이스
└── archive/               # 완료된 마이그레이션 스크립트
    ├── migration.py       # 레거시 데이터 마이그레이션
    └── show.py           # 기타 유틸리티
```

## 🎯 핵심 기능

### ✅ 완료된 기능
- **웹 대시보드**: Plotly Dash 기반 인터랙티브 데이터 시각화
- **자동 데이터 수집**: 파일 시스템 모니터링을 통한 실시간 인덱싱
- **REST API**: 실험 검색 및 파일 경로 조회 API
- **다중 센서 비교**: 여러 센서 데이터를 동시에 그래프로 표시
- **데이터 요약**: 각 센서별 통계 정보 (샘플 수, 지속 시간, 샘플링 레이트)
- **한국어 지원**: 완전한 한국어 인터페이스 및 문서화
- **Docker 지원**: 컨테이너 기반 배포

### 🔧 시스템 구성 요소
- **데이터베이스**: SQLite 기반 계층적 구조 (experiments, tests, sensors, data_quality)
- **자동 인덱싱**: metadata.json 파일을 스캔하여 자동으로 데이터베이스에 저장
- **파일 모니터링**: watchdog를 통한 실시간 파일 시스템 감시
- **API 엔드포인트**: 검색, 경로 조회, 센서 정보 조회
- **인터랙티브 UI**: 실험 → 테스트 → 센서 순서로 계층적 선택

## 📊 데이터베이스 스키마

### Experiments 테이블
```sql
CREATE TABLE experiments (
    id INTEGER PRIMARY KEY,
    date TEXT,
    scenario TEXT,        -- SingleLaneChange, StopAndGo
    description TEXT
);
```

### Tests 테이블
```sql
CREATE TABLE tests (
    id INTEGER PRIMARY KEY,
    experiment_id INTEGER,
    test_name TEXT,       -- Test1, Test2, Test3, ...
    file_path TEXT,
    imu_count INTEGER,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);
```

### Sensors 테이블
```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY,
    test_id INTEGER,
    sensor_id TEXT,       -- IMU_01, IMU_02, ...
    position TEXT,        -- 콘솔, 조수석후방, ...
    file_name TEXT,
    file_path TEXT,
    FOREIGN KEY (test_id) REFERENCES tests(id)
);
```

## 🚀 빠른 시작

### 1. 시스템 실행
```bash
# Docker를 사용한 실행
docker-compose up -d

# 또는 직접 실행
python app.py
```

### 2. 웹 인터페이스 접속
- 브라우저에서 `http://localhost:8050` 접속
- 비밀번호: `mobis1234`

### 3. API 테스트
```bash
# API 상태 확인
curl http://localhost:8050/api/health

# 실험 검색
curl "http://localhost:8050/api/search/tests?subject=정현용"
```

## 📚 문서화

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**: REST API 완전 가이드
- **[USER_GUIDE_KR.md](USER_GUIDE_KR.md)**: 한국어 사용자 가이드
- **[FILENAME_CONVENTION_KR.md](FILENAME_CONVENTION_KR.md)**: 파일 명명 규칙 (한국어)
- **[FILENAME_CONVENTION.md](FILENAME_CONVENTION.md)**: 파일 명명 규칙 (영어)

## 🎯 시스템 특징

### 자동화
- **실시간 파일 모니터링**: 새로운 데이터 자동 감지 및 인덱싱
- **자동 데이터베이스 업데이트**: metadata.json 변경 시 즉시 반영
- **디바운싱**: 파일 변경 시 중복 처리 방지

### 확장성
- **다중 프로젝트 지원**: 프로젝트별 데이터 분리
- **다양한 센서 유형**: IMU, 카메라, GPS 등 확장 가능
- **표준화된 명명 규칙**: 일관된 파일 및 디렉토리 구조

### 사용자 친화성
- **한국어 완전 지원**: 인터페이스 및 문서화
- **직관적인 웹 UI**: 드래그 앤 드롭, 인터랙티브 그래프
- **REST API**: 프로그래밍 방식 데이터 접근

## 🛠️ 설치 및 실행

### 요구사항
- Python 3.8+
- Docker (선택사항)

### 설치
```bash
# 의존성 설치
pip install -r requirements.txt

# 또는 Docker 사용
docker-compose up -d
```

### 실행
```bash
# 직접 실행
python app.py

# Docker 실행
docker-compose up -d
```

## 📝 사용법

### 웹 인터페이스
1. 브라우저에서 `http://localhost:8050` 접속
2. 비밀번호 `mobis1234` 입력
3. 실험 → 테스트 → 센서 순서로 선택
4. 데이터 타입 선택 (가속도/각속도)
5. "데이터 로드" 버튼으로 시각화

### API 사용
```bash
# 실험 검색
curl "http://localhost:8050/api/search/tests?subject=정현용"

# 파일 경로 조회
curl "http://localhost:8050/api/tests/1/paths"
```

## 🔧 문제 해결

### API 테스트
```bash
python test_api.py
```

### 데이터베이스 새로고침
웹 인터페이스에서 "🔄 DB 새로고침" 버튼 클릭

## 📄 라이선스

연구실 내부 사용 목적