# IMU Data Manager

연구실에서 수집한 IMU 센서 데이터를 체계적으로 관리하고 시각화하는 웹 기반 데이터 관리 시스템

## 📋 프로젝트 개요

### 목적
- 다중 IMU 센서로부터 수집된 시계열 데이터(CSV)의 체계적 관리
- 웹 인터페이스를 통한 직관적인 데이터 시각화
- 실험 시나리오별 데이터 분류 및 비교 분석

### 실험 환경
- **실험 유형**: Single Lane Change, Stop and Go
- **센서 구성**: 다중 IMU 센서 동시 설치
- **데이터 형식**: CSV 파일 (가속도, 각속도 등)
- **서버 환경**: 시놀로지 NAS

## 🏗️ 시스템 아키텍처

### 기술 스택
- **Frontend**: Plotly Dash
- **Backend**: Python (Dash 내장 Flask 서버)
- **Database**: SQLite
- **Visualization**: Plotly
- **File Monitoring**: Python watchdog

### 디렉토리 구조 (예시)
```
IMU_Data_Manager/
├── app.py              # Dash 메인 애플리케이션
├── database.py         # SQLite 연결 및 쿼리 함수
├── utils.py           # CSV 파싱, 파일 모니터링 유틸리티
├── data/              # 실험 데이터 저장소
│   ├── 2024-06-30_SingleLaneChange/
│   │   ├── Test1/
│   │   │   ├── IMU_01.csv
│   │   │   ├── IMU_02.csv
│   │   │   └── metadata.json
│   │   └── Test2/
│   └── 2024-07-01_StopAndGo/
├── db/
│   └── imu_data.db    # SQLite 데이터베이스
└── requirements.txt   # Python 의존성 패키지
```

## 🎯 핵심 기능

### 1단계 (프로토타입) ✅ 완료
- [x] 단일 CSV 파일 업로드 및 기본 그래프 표시
- [x] 시간축 기반 IMU 데이터 시각화 (가속도, 각속도)

### 2단계 (기본 기능) ✅ 완료
- [x] SQLite 데이터베이스 연결 및 메타데이터 관리
- [x] 실험/테스트별 데이터 분류 및 선택 기능
- [x] 다중 파일 선택 및 비교 시각화

#### 2단계 구현 상세
- **데이터베이스 스키마**: experiments, tests, sensors 3개 테이블로 계층적 구조
- **자동 인덱싱**: metadata.json 파일을 스캔하여 자동으로 데이터베이스에 저장
- **인터랙티브 UI**: 실험 → 테스트 → 센서 순서로 계층적 선택
- **다중 센서 비교**: 여러 센서 데이터를 동시에 그래프로 표시
- **데이터 요약**: 각 센서별 통계 정보 (샘플 수, 지속 시간, 샘플링 레이트)

### 3단계 (고급 기능)
- [ ] 자동 파일 감지 및 인덱싱
- [ ] 다중 IMU 센서 데이터 동시 비교
- [ ] 인터랙티브 그래프 (줌, 범위 선택, 센서 on/off)

### 4단계 (최적화)
- [ ] 실시간 파일 모니터링
- [ ] 데이터 필터링 및 검색 기능
- [ ] 실험 결과 내보내기

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

## 🚀 개발 로드맵

### Phase 1: 기술 검증 (1주) ✅ 완료
- Plotly Dash 기본 환경 구축
- 샘플 CSV 데이터로 그래프 생성 테스트
- SQLite 연결 및 기본 CRUD 구현

### Phase 2: 프로토타입 개발 (1주) ✅ 완료
- 하드코딩된 단일 파일 시각화
- 기본 웹 인터페이스 구현
- 시놀로지 NAS 배포 테스트

### Phase 3: 핵심 기능 구현 (2-3주) ✅ 완료
- 데이터베이스 통합
- 파일 선택 및 비교 기능
- 자동 파일 감지 시스템

### Phase 4: 최적화 및 완성 (1-2주)
- 사용자 인터페이스 개선
- 성능 최적화
- 문서화 및 배포

## 💡 구현 전략

### 개발 원칙
1. **점진적 개발**: 한 번에 하나의 기능씩 구현
2. **최소 실행 가능 제품**: 완벽하지 않아도 동작하는 버전 우선
3. **지속적 테스트**: 매일 실제 데이터로 테스트
4. **사용자 피드백**: 연구실 동료들과 지속적 소통

### 성공 기준
- 1주일 내에 화면에서 그래프 확인 ✅
- 연구실 구성원들이 직관적으로 사용 가능 ✅
- 새로운 실험 데이터 추가 시 최소한의 작업으로 시각화 ✅

## 🛠️ 설치 및 실행

### 요구사항
- Python 3.8+
- 시놀로지 NAS (Docker 또는 Python Station)

### 설치
```bash
pip install dash plotly pandas sqlite3 watchdog
```

### 실행
```bash
python app.py
```

## 📝 사용법

1. 웹 브라우저에서 `http://localhost:8050` 접속
2. 실험 목록에서 원하는 실험 선택
3. 테스트 드롭다운에서 특정 테스트 선택
4. 센서 체크리스트에서 비교할 센서들 선택
5. 데이터 타입 선택 (가속도/각속도)
6. "데이터 로드" 버튼 클릭
7. 인터랙티브 그래프에서 데이터 분석
8. 하단의 데이터 요약 테이블 확인

## 🤝 기여 방법

연구실 내부 프로젝트로, 기능 요청이나 버그 리포트는 직접 소통을 통해 진행

## 📄 라이선스

연구실 내부 사용 목적