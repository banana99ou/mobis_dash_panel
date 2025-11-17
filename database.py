import sqlite3
import json
import os
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional

class IMUDatabase:
    def __init__(self, db_path: str = 'db/imu_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Experiments 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT,
                    experiment_id TEXT,
                    date TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Tests 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id INTEGER,
                    test_id TEXT,
                    test_name TEXT NOT NULL,
                    sequence INTEGER,
                    subject TEXT,
                    subject_id TEXT,
                    duration_sec REAL,
                    notes TEXT,
                    file_path TEXT NOT NULL,
                    imu_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_hash TEXT,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
                )
            ''')
            # Sensors 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT,
                    position TEXT,
                    sequence INTEGER,
                    sample_rate_hz REAL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES tests(id)
                )
            ''')
            # Data Quality 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_quality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER,
                    completeness REAL,
                    anomalies INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES tests(id)
                )
            ''')
            
            # Optimization Strategies 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_number INTEGER NOT NULL UNIQUE,
                    strategy_name TEXT NOT NULL,
                    description TEXT,
                    requires_subject INTEGER NOT NULL DEFAULT 0,
                    requires_scenario INTEGER NOT NULL DEFAULT 0,
                    requires_sensor_setting INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sensor Settings Lookup 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_setting_code TEXT NOT NULL UNIQUE,
                    description TEXT,
                    sensor_components TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Optimization Parameters 테이블 생성
            # Note: subject_id, scenario, sensor_setting_id are removed - use junction tables instead
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER NOT NULL,
                    parameter_type TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_hash TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES optimization_strategies(id)
                )
            ''')
            
            # Many-to-many junction tables for explicit listing
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_parameter_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    subject_id TEXT NOT NULL,
                    subject_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parameter_id) REFERENCES optimization_parameters(id) ON DELETE CASCADE,
                    UNIQUE(parameter_id, subject_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_parameter_scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    scenario TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parameter_id) REFERENCES optimization_parameters(id) ON DELETE CASCADE,
                    UNIQUE(parameter_id, scenario)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_parameter_sensor_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    sensor_setting_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parameter_id) REFERENCES optimization_parameters(id) ON DELETE CASCADE,
                    FOREIGN KEY (sensor_setting_id) REFERENCES sensor_settings(id),
                    UNIQUE(parameter_id, sensor_setting_id)
                )
            ''')
            
            # Optimization Results 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    model_name TEXT NOT NULL,
                    result_file_path TEXT NOT NULL,
                    result_file_name TEXT NOT NULL,
                    file_hash TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parameter_id) REFERENCES optimization_parameters(id),
                    UNIQUE(parameter_id, model_name)
                )
            ''')
            
            # Optimization Visualizations 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_visualizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_id INTEGER NOT NULL,
                    visualization_type TEXT NOT NULL,
                    model_name TEXT,
                    graph_file_path TEXT NOT NULL,
                    graph_file_name TEXT NOT NULL,
                    file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parameter_id) REFERENCES optimization_parameters(id)
                )
            ''')
            
            # 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_params_strategy ON optimization_parameters(strategy_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_params_data_type ON optimization_parameters(data_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_results_param ON optimization_results(parameter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_visualizations_param ON optimization_visualizations(parameter_id)')
            
            # Junction table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_subjects_param ON optimization_parameter_subjects(parameter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_subjects_subject ON optimization_parameter_subjects(subject_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_scenarios_param ON optimization_parameter_scenarios(parameter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_scenarios_scenario ON optimization_parameter_scenarios(scenario)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_sensors_param ON optimization_parameter_sensor_settings(parameter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_param_sensors_setting ON optimization_parameter_sensor_settings(sensor_setting_id)')
            
            conn.commit()
            
            # Lookup 테이블 초기화 (데이터가 없을 때만)
            self._seed_lookup_tables()

    def reset_tables(self):
        """테이블 데이터만 초기화 (테이블 구조는 유지)
        주의: 최적화 테이블은 삭제하지 않음 (scan_and_index_data는 test/experiment 데이터만 처리)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 외래 키 제약 조건 비활성화
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # 테이블 데이터 삭제 (테이블 구조는 유지)
            # 주의: optimization 테이블은 삭제하지 않음 - scan_and_index_optimization_data()에서 별도 관리
            cursor.execute('DELETE FROM data_quality')
            cursor.execute('DELETE FROM sensors')
            cursor.execute('DELETE FROM tests')
            cursor.execute('DELETE FROM experiments')
            # Lookup 테이블은 유지 (optimization_strategies, sensor_settings)
            # Optimization 테이블도 유지 (optimization_parameters, optimization_results, optimization_visualizations, junction tables)
            
            # AUTOINCREMENT 카운터 리셋 (최적화 테이블 제외)
            cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("data_quality", "sensors", "tests", "experiments")')
            
            # 외래 키 제약 조건 재활성화
            cursor.execute('PRAGMA foreign_keys = ON')
            
            conn.commit()
            print("테이블 데이터 초기화 완료 (최적화 테이블은 유지됨)")

    def drop_and_recreate_tables(self):
        """테이블을 완전히 삭제하고 재생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 외래 키 제약 조건 비활성화
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # 기존 테이블 삭제
            cursor.execute('DROP TABLE IF EXISTS optimization_visualizations')
            cursor.execute('DROP TABLE IF EXISTS optimization_results')
            cursor.execute('DROP TABLE IF EXISTS optimization_parameter_sensor_settings')
            cursor.execute('DROP TABLE IF EXISTS optimization_parameter_scenarios')
            cursor.execute('DROP TABLE IF EXISTS optimization_parameter_subjects')
            cursor.execute('DROP TABLE IF EXISTS optimization_parameters')
            cursor.execute('DROP TABLE IF EXISTS sensor_settings')
            cursor.execute('DROP TABLE IF EXISTS optimization_strategies')
            cursor.execute('DROP TABLE IF EXISTS data_quality')
            cursor.execute('DROP TABLE IF EXISTS sensors')
            cursor.execute('DROP TABLE IF EXISTS tests')
            cursor.execute('DROP TABLE IF EXISTS experiments')
            
            # 외래 키 제약 조건 재활성화
            cursor.execute('PRAGMA foreign_keys = ON')
            
            conn.commit()
            print("테이블 삭제 완료")
        
        # 테이블 재생성
        self.init_database()
        print("테이블 재생성 완료")

    def scan_and_index_data(self, data_root: str = 'data'):
        """data 폴더 전체를 스캔하여 metadata.json을 DB에 인덱싱 (삭제된 데이터도 제거)"""
        print("데이터베이스 동기화 시작...")
        
        # 1. 현재 파일 시스템에서 모든 metadata.json 파일 경로 수집
        current_files = set()
        for root, dirs, files in os.walk(data_root):
            for file in files:
                if file == 'metadata.json':
                    metadata_path = os.path.join(root, file)
                    # Normalize path to NFC for cross-platform compatibility
                    normalized_path = unicodedata.normalize('NFC', metadata_path)
                    current_files.add(normalized_path)
        
        # 2. DB에서 현재 저장된 모든 metadata.json 파일 경로 수집
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM tests')
            db_files = {unicodedata.normalize('NFC', row[0]) for row in cursor.fetchall()}
        
        # 3. 삭제된 파일들 확인
        deleted_files = db_files - current_files
        if deleted_files:
            print(f"삭제된 파일들 감지: {len(deleted_files)}개")
            for deleted_file in deleted_files:
                print(f"  - {deleted_file}")
        
        # 4. 테이블 데이터 초기화 (삭제된 데이터 제거를 위해)
        self.reset_tables()
        
        # 5. 현재 파일들로 DB 재구성
        for metadata_path in current_files:
            self._process_metadata_file(metadata_path)
        
        print(f"데이터베이스 동기화 완료: {len(current_files)}개 파일 처리")

    def _process_metadata_file(self, metadata_path: str):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Check if this is new format or old format
            if 'project' in metadata and 'test' in metadata:
                # New format
                self._process_new_metadata(metadata, metadata_path)
            else:
                # Old format - backward compatibility
                self._process_old_metadata(metadata, metadata_path)
                
        except Exception as e:
            print(f"메타데이터 파일 처리 중 오류: {metadata_path} - {e}")
    
    def _process_new_metadata(self, metadata: Dict, metadata_path: str):
        """Process new metadata format"""
        experiment_info = metadata['experiment']
        test_info = metadata['test']
        sensors_info = metadata['sensors']
        data_quality_info = metadata.get('data_quality', {})
        
        # file_path 기준으로 기존 테스트 row와 센서 row를 무조건 삭제
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tests WHERE file_path = ?', (metadata_path,))
            test_row = cursor.fetchone()
            if test_row:
                test_id = test_row[0]
                cursor.execute('DELETE FROM data_quality WHERE test_id = ?', (test_id,))
                cursor.execute('DELETE FROM sensors WHERE test_id = ?', (test_id,))
                cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            conn.commit()
        
        # 실험 정보 저장 또는 업데이트
        experiment_id = self._save_experiment_new(metadata.get('project'), experiment_info)
        # subject_id 정규화
        if test_info.get('subject_id'):
            test_info['subject_id'] = self._normalize_subject_id(test_info['subject_id'])
        
        # 테스트 정보 저장
        test_id = self._save_test_new(experiment_id, test_info, metadata_path)
        # 센서 정보 저장
        for sensor in sensors_info:
            self._save_sensor_new(test_id, sensor, metadata_path)
        # 데이터 품질 정보 저장
        self._save_data_quality(test_id, data_quality_info)
    
    def _process_old_metadata(self, metadata: Dict, metadata_path: str):
        """Process old metadata format for backward compatibility"""
        experiment_info = metadata['experiment']
        sensors_info = metadata['sensors']
        
        # file_path 기준으로 기존 테스트 row와 센서 row를 무조건 삭제
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tests WHERE file_path = ?', (metadata_path,))
            test_row = cursor.fetchone()
            if test_row:
                test_id = test_row[0]
                cursor.execute('DELETE FROM data_quality WHERE test_id = ?', (test_id,))
                cursor.execute('DELETE FROM sensors WHERE test_id = ?', (test_id,))
                cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            conn.commit()
        
        # 실험 정보 저장 또는 업데이트
        experiment_id = self._save_experiment(experiment_info)
        # 테스트 정보 저장
        test_id = self._save_test(experiment_id, experiment_info, metadata_path)
        # 센서 정보 저장
        for sensor in sensors_info:
            self._save_sensor(test_id, sensor, metadata_path)

    def _save_experiment_new(self, project: str, experiment_info: Dict) -> int:
        """Save experiment with new metadata format"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM experiments 
                WHERE project = ? AND experiment_id = ? AND date = ? AND scenario = ?
            ''', (project, experiment_info.get('id'), experiment_info['date'], experiment_info['scenario']))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute('''
                    INSERT INTO experiments (project, experiment_id, date, scenario, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    project,
                    experiment_info.get('id'),
                    experiment_info['date'],
                    experiment_info['scenario'],
                    experiment_info.get('description', f"{experiment_info['scenario']} 실험")
                ))
                conn.commit()
                return cursor.lastrowid

    def _save_experiment(self, experiment_info: Dict) -> int:
        """Save experiment with old metadata format (backward compatibility)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM experiments 
                WHERE date = ? AND scenario = ?
            ''', (experiment_info['date'], experiment_info['scenario']))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute('''
                    INSERT INTO experiments (date, scenario, description)
                    VALUES (?, ?, ?)
                ''', (
                    experiment_info['date'],
                    experiment_info['scenario'],
                    f"{experiment_info['scenario']} 실험"
                ))
                conn.commit()
                return cursor.lastrowid

    def _save_test_new(self, experiment_id: int, test_info: Dict, metadata_path: str) -> int:
        """Save test with new metadata format"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM tests 
                WHERE experiment_id = ? AND test_id = ?
            ''', (experiment_id, test_info['id']))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute('''
                    INSERT INTO tests (experiment_id, test_id, test_name, sequence, subject, subject_id, duration_sec, notes, file_path, imu_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    experiment_id,
                    test_info['id'],
                    test_info['id'],  # Use test_id as test_name for display
                    test_info.get('sequence'),
                    test_info.get('subject'),
                    test_info.get('subject_id'),
                    test_info.get('duration_sec'),
                    test_info.get('notes', ''),
                    metadata_path,
                    0
                ))
                conn.commit()
                return cursor.lastrowid

    def _save_test(self, experiment_id: int, experiment_info: Dict, metadata_path: str) -> int:
        """Save test with old metadata format (backward compatibility)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM tests 
                WHERE experiment_id = ? AND test_name = ?
            ''', (experiment_id, experiment_info['test_name']))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute('''
                    INSERT INTO tests (experiment_id, test_name, file_path, imu_count)
                    VALUES (?, ?, ?, ?)
                ''', (
                    experiment_id,
                    experiment_info['test_name'],
                    metadata_path,
                    0
                ))
                conn.commit()
                return cursor.lastrowid

    def _save_sensor_new(self, test_id: int, sensor_info: Dict, metadata_path: str):
        """Save sensor with new metadata format"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metadata_dir = os.path.dirname(metadata_path)
            sensor_file_path = os.path.join(metadata_dir, sensor_info['file'])
            
            # Use file name as sensor_id for new format
            sensor_id = sensor_info['file'].replace('.csv', '')
            
            cursor.execute('''
                SELECT id FROM sensors 
                WHERE test_id = ? AND sensor_id = ?
            ''', (test_id, sensor_id))
            result = cursor.fetchone()
            if result:
                cursor.execute('''
                    UPDATE sensors 
                    SET sensor_type = ?, position = ?, sequence = ?, sample_rate_hz = ?, file_name = ?, file_path = ?
                    WHERE test_id = ? AND sensor_id = ?
                ''', (
                    sensor_info.get('type', ''),
                    sensor_info.get('position', ''),
                    sensor_info.get('sequence'),
                    sensor_info.get('sample_rate_hz'),
                    sensor_info['file'],
                    sensor_file_path,
                    test_id,
                    sensor_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO sensors 
                    (test_id, sensor_id, sensor_type, position, sequence, sample_rate_hz, file_name, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    sensor_id,
                    sensor_info.get('type', ''),
                    sensor_info.get('position', ''),
                    sensor_info.get('sequence'),
                    sensor_info.get('sample_rate_hz'),
                    sensor_info['file'],
                    sensor_file_path
                ))
            cursor.execute('''
                UPDATE tests 
                SET imu_count = (
                    SELECT COUNT(*) FROM sensors WHERE test_id = ?
                )
                WHERE id = ?
            ''', (test_id, test_id))
            conn.commit()

    def _save_sensor(self, test_id: int, sensor_info: Dict, metadata_path: str):
        """Save sensor with old metadata format (backward compatibility)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metadata_dir = os.path.dirname(metadata_path)
            sensor_file_path = os.path.join(metadata_dir, sensor_info['file'])
            cursor.execute('''
                SELECT id FROM sensors 
                WHERE test_id = ? AND sensor_id = ?
            ''', (test_id, sensor_info['id']))
            result = cursor.fetchone()
            if result:
                cursor.execute('''
                    UPDATE sensors 
                    SET position = ?, file_name = ?, file_path = ?
                    WHERE test_id = ? AND sensor_id = ?
                ''', (
                    sensor_info.get('position', ''),
                    sensor_info['file'],
                    sensor_file_path,
                    test_id,
                    sensor_info['id']
                ))
            else:
                cursor.execute('''
                    INSERT INTO sensors 
                    (test_id, sensor_id, position, file_name, file_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    sensor_info['id'],
                    sensor_info.get('position', ''),
                    sensor_info['file'],
                    sensor_file_path
                ))
            cursor.execute('''
                UPDATE tests 
                SET imu_count = (
                    SELECT COUNT(*) FROM sensors WHERE test_id = ?
                )
                WHERE id = ?
            ''', (test_id, test_id))
            conn.commit()

    def _save_data_quality(self, test_id: int, data_quality_info: Dict):
        """Save data quality information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO data_quality (test_id, completeness, anomalies, notes)
                VALUES (?, ?, ?, ?)
            ''', (
                test_id,
                data_quality_info.get('completeness', 1.0),
                data_quality_info.get('anomalies', 0),
                data_quality_info.get('notes', '')
            ))
            conn.commit()

    def get_experiments(self) -> List[Dict]:
        """모든 실험 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, project, experiment_id, date, scenario, description, created_at
                FROM experiments
                ORDER BY date DESC, created_at DESC
            ''')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_tests_by_experiment(self, experiment_id: int) -> List[Dict]:
        """특정 실험의 테스트 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, test_id, test_name, sequence, subject, subject_id, duration_sec, notes, imu_count, created_at
                FROM tests
                WHERE experiment_id = ?
                ORDER BY sequence, test_name
            ''', (experiment_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_sensors_by_test(self, test_id: int) -> List[Dict]:
        """특정 테스트의 센서 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sensor_id, sensor_type, position, sequence, sample_rate_hz, file_name, file_path
                FROM sensors
                WHERE test_id = ?
                ORDER BY sequence, sensor_id
            ''', (test_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_test_details(self, test_id: int) -> Optional[Dict]:
        """테스트 상세 정보 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.test_id, t.test_name, t.sequence, t.subject, t.subject_id, t.duration_sec, t.notes, t.imu_count, t.created_at,
                       e.project, e.experiment_id, e.date, e.scenario, e.description
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                WHERE t.id = ?
            ''', (test_id,))
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None

    def search_tests(self, subject: str = None, subject_id: str = None, sensor_id: str = None, 
                    scenario: str = None, date: str = None, project: str = None) -> List[Dict]:
        """테스트 검색 (OR 조건으로 필터링)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 기본 쿼리
            query = '''
                SELECT DISTINCT t.id, t.test_id, t.test_name, t.sequence, t.subject, t.subject_id, t.duration_sec, t.notes, t.imu_count, t.created_at,
                       e.project, e.experiment_id, e.date, e.scenario, e.description
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                LEFT JOIN sensors s ON t.id = s.test_id
                WHERE 1=1
            '''
            params = []
            
            # 조건별 WHERE 절 추가 (OR 조건)
            conditions = []
            if subject:
                conditions.append('t.subject LIKE ?')
                params.append(f'%{subject}%')
            if subject_id:
                conditions.append('t.subject_id LIKE ?')
                params.append(f'%{subject_id}%')
            if sensor_id:
                conditions.append('s.sensor_id LIKE ?')
                params.append(f'%{sensor_id}%')
            if scenario:
                conditions.append('e.scenario LIKE ?')
                params.append(f'%{scenario}%')
            if date:
                conditions.append('e.date = ?')
                params.append(date)
            if project:
                conditions.append('e.project LIKE ?')
                params.append(f'%{project}%')
            
            if conditions:
                query += ' AND ' + ' AND '.join(conditions)
            
            query += ' ORDER BY e.date DESC, t.sequence, t.test_name'
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_test_paths(self, test_id: int) -> Optional[Dict]:
        """테스트의 모든 파일 경로 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 테스트 기본 정보 조회
            cursor.execute('''
                SELECT t.id, t.test_id, t.test_name, t.sequence, t.subject, t.subject_id, t.duration_sec, t.file_path, 
                       e.project, e.experiment_id, e.date, e.scenario, e.description
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                WHERE t.id = ?
            ''', (test_id,))
            test_result = cursor.fetchone()
            
            if not test_result:
                return None
            
            # 센서 파일들 조회
            cursor.execute('''
                SELECT sensor_id, sensor_type, position, sequence, sample_rate_hz, file_path
                FROM sensors
                WHERE test_id = ?
                ORDER BY sequence, sensor_id
            ''', (test_id,))
            sensor_results = cursor.fetchall()
            
            # 메타데이터 파일 경로에서 실험 폴더 경로 추출
            metadata_path = test_result[7]
            experiment_path = os.path.dirname(metadata_path)
            
            return {
                'test_id': test_result[0],
                'test_id_str': test_result[1],
                'test_name': test_result[2],
                'sequence': test_result[3],
                'subject': test_result[4],
                'subject_id': test_result[5],
                'duration_sec': test_result[6],
                'project': test_result[8],
                'experiment_id': test_result[9],
                'experiment_date': test_result[10],
                'scenario': test_result[11],
                'description': test_result[12],
                'experiment_path': experiment_path,
                'metadata_path': metadata_path,
                'sensor_files': [
                    {
                        'sensor_id': row[0],
                        'sensor_type': row[1],
                        'position': row[2],
                        'sequence': row[3],
                        'sample_rate_hz': row[4],
                        'file_path': row[5]
                    }
                    for row in sensor_results
                ]
            }

    def _seed_lookup_tables(self):
        """Lookup 테이블 초기 데이터 삽입 (이미 데이터가 있으면 스킵)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Optimization Strategies 초기화
            cursor.execute('SELECT COUNT(*) FROM optimization_strategies')
            if cursor.fetchone()[0] == 0:
                strategies = [
                    (0, 'BySubjectScenarioSensor', '피험자별 + 시나리오별 + 센서 세팅별 최적화', 1, 1, 1),
                    (1, 'BySubject', '피험자별 최적화 (모든 시나리오 통합)', 1, 0, 0),
                    (2, 'BySubjectScenario', '피험자별 + 시나리오별 최적화', 1, 1, 0),
                    (3, 'ByScenario', '시나리오별 최적화 (모든 피험자 통합)', 0, 1, 0),
                    (4, 'Universal', '범용 최적화 (모든 피험자 + 모든 시나리오)', 0, 0, 0)
                ]
                cursor.executemany('''
                    INSERT INTO optimization_strategies 
                    (strategy_number, strategy_name, description, requires_subject, requires_scenario, requires_sensor_setting)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', strategies)
                print("Optimization strategies seeded")
            
            # Sensor Settings 초기화
            cursor.execute('SELECT COUNT(*) FROM sensor_settings')
            if cursor.fetchone()[0] == 0:
                sensor_settings = [
                    ('H-IMU_N-VV', 'Head IMU, No VV', '["H-IMU", "N-VV"]'),
                    ('H-IMU_T-VV', 'Head IMU, Tablet VV', '["H-IMU", "T-VV"]'),
                    ('H-IMU_C-VV', 'Head IMU, Car VV', '["H-IMU", "C-VV"]'),
                    ('V-IMU_N-VV', 'Vertical IMU, No VV', '["V-IMU", "N-VV"]'),
                    ('V-IMU_T-VV', 'Vertical IMU, Tablet VV', '["V-IMU", "T-VV"]'),
                    ('V-IMU_C-VV', 'Vertical IMU, Car VV', '["V-IMU", "C-VV"]'),
                    ('S-IMU_N-VV', 'S-IMU (Realsense), No VV', '["S-IMU", "N-VV"]'),
                    ('S-IMU_T-VV', 'S-IMU (Realsense), Tablet VV', '["S-IMU", "T-VV"]'),
                    ('S-IMU_C-VV', 'S-IMU (Realsense), Car VV', '["S-IMU", "C-VV"]')
                ]
                cursor.executemany('''
                    INSERT INTO sensor_settings (sensor_setting_code, description, sensor_components)
                    VALUES (?, ?, ?)
                ''', sensor_settings)
                print("Sensor settings seeded")
            
            conn.commit()

    def reset_optimization_tables(self):
        """최적화 테이블 데이터만 초기화 (ID 카운터도 리셋)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            cursor.execute('DELETE FROM optimization_visualizations')
            cursor.execute('DELETE FROM optimization_results')
            cursor.execute('DELETE FROM optimization_parameter_sensor_settings')
            cursor.execute('DELETE FROM optimization_parameter_scenarios')
            cursor.execute('DELETE FROM optimization_parameter_subjects')
            cursor.execute('DELETE FROM optimization_parameters')
            
            # ID 카운터 리셋
            cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("optimization_visualizations", "optimization_results", "optimization_parameter_sensor_settings", "optimization_parameter_scenarios", "optimization_parameter_subjects", "optimization_parameters")')
            
            cursor.execute('PRAGMA foreign_keys = ON')
            conn.commit()
            print("최적화 테이블 데이터 초기화 완료 (ID 카운터 리셋)")

    def scan_and_index_optimization_data(self, data_root: str = 'data/motion_sickness/optimization', reset_first: bool = False):
        """최적화 데이터 파일 스캔 및 인덱싱
        
        Args:
            data_root: 데이터 루트 경로 (기본값: data/motion_sickness/optimization)
            reset_first: True면 스캔 전에 기존 데이터 삭제 및 ID 카운터 리셋
        """
        if reset_first:
            self.reset_optimization_tables()
        
        print("최적화 데이터 인덱싱 시작...")
        
        if not os.path.exists(data_root):
            print(f"경로가 존재하지 않습니다: {data_root}")
            return
        
        # 현재 구조: Driving/Parameter, Driving/Results, Driving/Graph
        # 또는: Driving+Rest/Parameter, Driving+Rest/Results, Driving+Rest/Graph
        data_type_map = {
            'Driving': '주행',
            'Driving+Rest': '주행+휴식'
        }
        
        for data_type_folder, data_type in data_type_map.items():
            data_type_path = os.path.join(data_root, data_type_folder)
            if not os.path.exists(data_type_path):
                continue
                
            print(f"\n[{data_type}] 데이터 스캔 중...")
            
            # 파라미터 파일 스캔 (Parameter 폴더)
            param_path = os.path.join(data_type_path, 'Parameter')
            if os.path.exists(param_path):
                print(f"[scan parameter] param_path: {param_path} | {data_type}")
                self._scan_parameter_files(param_path, data_type)
            
            # 결과 파일 스캔 (Results 폴더)
            result_path = os.path.join(data_type_path, 'Results')
            if os.path.exists(result_path):
                self._scan_result_files(result_path, data_type)
            
            # 시각화 파일 스캔 (Graph 폴더)
            graph_path = os.path.join(data_type_path, 'Graph')
            if os.path.exists(graph_path):
                self._scan_visualization_files(graph_path, data_type)
        
        print("\n최적화 데이터 인덱싱 완료")

    def _scan_parameter_files(self, param_path: str, data_type: str):
        """파라미터 파일 (.m) 스캔 및 인덱싱 (hierarchical structure, metadata from folder path)"""
        print(f"  파라미터 파일 스캔: {param_path}")
        
        count = 0
        m_count = 0
        for root, dirs, files in os.walk(param_path):
            for file in files:
                if file.endswith('.m'):
                    m_count += 1
                    file_path = os.path.join(root, file)
                    
                    # 폴더 경로에서 전략 번호 추출
                    strategy_number = self._extract_strategy_from_path(file_path, param_path)
                    if strategy_number is None:
                        print(f"[scan parameter] strategy number is None file_path: {file_path}")
                        continue
                    
                    # 폴더 경로에서 정보 추출 (hierarchical structure)
                    parsed = self._parse_parameter_file_from_path(file_path, param_path, strategy_number, file)
                    if parsed:
                        self._save_optimization_parameter(
                            strategy_number=strategy_number,
                            subject_id=parsed.get('subject_id'),
                            scenario=parsed.get('scenario'),
                            sensor_setting_code=parsed.get('sensor_setting'),
                            parameter_type=parsed.get('parameter_type'),
                            data_type=data_type,
                            file_path=file_path,
                            file_name=file
                        )
                        count += 1
                    else:
                        print(f"[scan parameter] parsed is None strategy number: {strategy_number}")
                        continue
        
        print(f"    파라미터 파일 {count}개 인덱싱 완료")
        print(f'm_count: {m_count}')

    def _extract_strategy_from_path(self, file_path: str, base_path: str) -> Optional[int]:
        """경로에서 전략 번호 추출
        
        Args:
            file_path: 전체 파일 경로
            base_path: 기준 경로 (Parameter, Results, Graph)
        
        Returns:
            전략 번호 (0-4) 또는 None
        """
        # base_path 이후의 경로 부분 추출
        rel_path = os.path.relpath(file_path, base_path)
        path_parts = Path(rel_path).parts
        
        # Strategy 폴더 찾기
        for part in path_parts:
            if 'Strategy0' in part or 'strategy0' in part.lower():
                return 0
            elif 'Strategy1' in part or 'strategy1' in part.lower():
                return 1
            elif 'Strategy2' in part or 'strategy2' in part.lower():
                return 2
            elif 'Strategy3' in part or 'strategy3' in part.lower():
                return 3
            elif 'Strategy4' in part or 'strategy4' in part.lower() or 'Universal' in part:
                return 4
        
        return None

    def _parse_parameter_file_from_path(self, file_path: str, base_path: str, strategy_number: int, filename: str) -> Optional[Dict]:
        """폴더 경로에서 파라미터 파일 정보 추출 (hierarchical structure)
        
        구조 예시:
        - Parameter/Strategy0_BySubjectScenarioSensor/[scenario_subject]/[sensor_setting]/[file].m
        - Parameter/Strategy1_BySubject/[subject]/[file].m
        - Parameter/Strategy2_BySubjectScenario/[scenario_subject]/[file].m
        - Parameter/Strategy3_ByScenario/[scenario]/[file].m
        - Parameter/Strategy4_Universal/[file].m
        """
        # base_path 이후의 경로 부분 추출
        rel_path = os.path.relpath(file_path, base_path)
        path_parts = list(Path(rel_path).parts)
        
        # 파일명 제거
        if path_parts and path_parts[-1] == filename:
            path_parts = path_parts[:-1]
        
        # Strategy 폴더 제거
        path_parts = [p for p in path_parts if not p.startswith('Strategy')]
        
        # parameter_type 추출 (파일명에서)
        if 'fullopt' in filename:
            parameter_type = 'fullopt'
        elif '3opt' in filename:
            parameter_type = '3opt'
        else:
            parameter_type = 'fullopt'  # 기본값
        
        # Strategy 0: scenario_subject/sensor_setting/file.m
        if strategy_number == 0:
            if len(path_parts) >= 2:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                sensor_setting = path_parts[1]    # e.g., "H-IMU_N-VV"
                # Strip .tmp suffix if present (some directories have .tmp suffix)
                if sensor_setting.endswith('.tmp'):
                    sensor_setting = sensor_setting[:-4]
                
                if '_' in scenario_subject:
                    scenario, subject_id_raw = scenario_subject.split('_', 1)
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'sensor_setting': sensor_setting,
                        'parameter_type': parameter_type
                    }
        
        # Strategy 1: subject/file.m
        elif strategy_number == 1:
            if path_parts:
                subject_id_raw = path_parts[0]  # e.g., "sub03"
                subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': None,
                    'subject_id': subject_id,
                    'sensor_setting': None,
                    'parameter_type': parameter_type
                }
        
        # Strategy 2: scenario_subject/file.m
        elif strategy_number == 2:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                if '_' in scenario_subject:
                    scenario, subject_id_raw = scenario_subject.split('_', 1)
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'sensor_setting': None,
                        'parameter_type': parameter_type
                    }
        
        # Strategy 3: scenario/file.m
        elif strategy_number == 3:
            if path_parts:
                scenario = path_parts[0]  # e.g., "lw"
                return {
                    'scenario': scenario,
                    'subject_id': None,
                    'sensor_setting': None,
                    'parameter_type': parameter_type
                }
        
        # Strategy 4: file.m (universal)
        elif strategy_number == 4:
            return {
                'scenario': None,
                'subject_id': None,
                'sensor_setting': None,
                'parameter_type': parameter_type
            }
        
        return None

    def _parse_parameter_file_from_filename(self, filename: str, strategy_number: int) -> Optional[Dict]:
        """파라미터 파일명에서 정보 추출 (flat structure, no folder hierarchy)
        
        예상 파일명 형식:
        - Strategy0_sub_001_lw_H-IMU_N-VV_주행_fullopt.m
        - Strategy1_sub_001_주행_fullopt.m
        - Strategy2_sub_001_lw_주행_fullopt.m
        - Strategy3_lw_주행_fullopt.m
        - Strategy4_주행_fullopt.m 또는 universal_주행_fullopt.m
        """
        # 파일명에서 parameter_type 추출
        if 'fullopt' in filename:
            parameter_type = 'fullopt'
        elif '3opt' in filename:
            parameter_type = '3opt'
        else:
            parameter_type = 'fullopt'  # 기본값
        
        # 파일명을 언더스코어로 분리
        parts = filename.replace('.m', '').split('_')
        
        # Strategy 0: Strategy0_sub_001_lw_H-IMU_N-VV_주행_fullopt
        if strategy_number == 0:
            # Strategy0 제거 후: sub_001, lw, H-IMU, N-VV, 주행, fullopt
            # 또는: Strategy0, sub_001, lw, H-IMU, N-VV, 주행, fullopt
            try:
                # Strategy0 제거
                parts_clean = [p for p in parts if not p.startswith('Strategy') and p != '']
                # sub_001, lw, H-IMU, N-VV 형식 찾기
                if len(parts_clean) >= 4:
                    # sub_001 찾기
                    subject_idx = None
                    for i, p in enumerate(parts_clean):
                        if p.startswith('sub'):
                            subject_idx = i
                            break
                    
                    if subject_idx is not None and subject_idx + 1 < len(parts_clean):
                        subject_id_raw = parts_clean[subject_idx]
                        if subject_idx + 1 < len(parts_clean):
                            scenario = parts_clean[subject_idx + 1]  # lw, slc, s&g
                        else:
                            scenario = None
                        
                        # Sensor setting 찾기 (H-IMU, N-VV 같은 형식)
                        sensor_parts = []
                        for i in range(subject_idx + 2, len(parts_clean)):
                            if parts_clean[i] in ['주행', '주행+휴식', 'fullopt', '3opt']:
                                break
                            sensor_parts.append(parts_clean[i])
                        
                        sensor_setting = '-'.join(sensor_parts) if sensor_parts else None
                        subject_id = self._normalize_subject_id(subject_id_raw)
                        
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'sensor_setting': sensor_setting,
                        'parameter_type': parameter_type
                    }
            except:
                pass
        
        # Strategy 1: Strategy1_sub_001_주행_fullopt
        elif strategy_number == 1:
            try:
                parts_clean = [p for p in parts if not p.startswith('Strategy') and p not in ['주행', '주행+휴식', 'fullopt', '3opt'] and p != '']
                if parts_clean:
                    subject_id_raw = parts_clean[0]  # sub_001
                    subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': None,
                    'subject_id': subject_id,
                    'sensor_setting': None,
                    'parameter_type': parameter_type
                }
            except:
                pass
        
        # Strategy 2: Strategy2_sub_001_lw_주행_fullopt
        elif strategy_number == 2:
            try:
                parts_clean = [p for p in parts if not p.startswith('Strategy') and p not in ['주행', '주행+휴식', 'fullopt', '3opt'] and p != '']
                if len(parts_clean) >= 2:
                    subject_id_raw = parts_clean[0]  # sub_001
                    scenario = parts_clean[1]  # lw
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'sensor_setting': None,
                        'parameter_type': parameter_type
                    }
            except:
                pass
        
        # Strategy 3: Strategy3_lw_주행_fullopt
        elif strategy_number == 3:
            try:
                parts_clean = [p for p in parts if not p.startswith('Strategy') and p not in ['주행', '주행+휴식', 'fullopt', '3opt'] and p != '']
                if parts_clean:
                    scenario = parts_clean[0]  # lw
                return {
                    'scenario': scenario,
                    'subject_id': None,
                    'sensor_setting': None,
                    'parameter_type': parameter_type
                }
            except:
                pass
        
        # Strategy 4: Strategy4_주행_fullopt 또는 universal_주행_fullopt
        elif strategy_number == 4:
            return {
                'scenario': None,
                'subject_id': None,
                'sensor_setting': None,
                'parameter_type': parameter_type
            }
        
        return None

    def _normalize_subject_id(self, subject_id: str) -> Optional[str]:
        """subject_id를 표준 형식(sub_001, sub_002 등)으로 정규화
        
        Args:
            subject_id: 다양한 형식의 subject_id (예: 'sub01', 'sub02', 'S001', 'sub_001')
        
        Returns:
            정규화된 subject_id (예: 'sub_001', 'sub_002') 또는 None (매핑 실패 시)
        """
        if not subject_id:
            return None
        
        # 이미 표준 형식인지 확인 (sub_001, sub_002 등)
        if subject_id.startswith('sub_'):
            # 숫자 부분 추출하여 검증
            num_part = subject_id[4:]
            if num_part.isdigit():
                # 001 형식으로 정규화
                num_padded = num_part.zfill(3)
                return f'sub_{num_padded}'
        
        # S001, S002 형식을 sub_001, sub_002로 변환
        if subject_id.startswith('S'):
            try:
                num_str = ''.join(filter(str.isdigit, subject_id[1:]))
                if num_str:
                    num_padded = num_str.zfill(3)
                    return f'sub_{num_padded}'
            except:
                pass
        
        # sub01, sub02 형식을 sub_001, sub_002로 변환
        if subject_id.startswith('sub'):
            try:
                # 'sub' 이후의 숫자 추출
                num = subject_id[3:]
                # 숫자만 추출 (sub01 -> 01, sub_01 -> 01)
                num_str = ''.join(filter(str.isdigit, num))
                if num_str:
                    # 01 -> 001 포맷
                    num_padded = num_str.zfill(3)
                    return f'sub_{num_padded}'
            except:
                pass
        
        # OP1, OP2 형식 처리 (특별한 경우)
        if subject_id.startswith('OP'):
            try:
                num_str = ''.join(filter(str.isdigit, subject_id[2:]))
                if num_str:
                    num_padded = num_str.zfill(3)
                    return f'sub_{num_padded}'
            except:
                pass
        
        # 매핑을 찾기 위해 tests 테이블에서 조회
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # test_id에 subject_id가 포함된 경우 찾기
            # 예: test_001_sub01_이경주 -> subject_id 찾기
            cursor.execute('''
                SELECT DISTINCT subject_id
                FROM tests
                WHERE (test_id LIKE ? OR test_id LIKE ?) AND subject_id IS NOT NULL
                LIMIT 1
            ''', (f'%{subject_id}%', f'%sub{subject_id[3:]}%' if subject_id.startswith('sub') else f'%{subject_id}%'))
            result = cursor.fetchone()
            if result:
                # 찾은 subject_id를 표준 형식으로 변환
                found_id = result[0]
                return self._normalize_subject_id(found_id)
        
        # 매핑 실패 시 원본 반환 (하지만 경고)
        print(f"Warning: Could not normalize subject_id '{subject_id}', using as-is")
        return subject_id

    def _get_subject_name(self, subject_id: str) -> Optional[str]:
        """Get subject name from tests table by subject_id
        
        Args:
            subject_id: Normalized subject_id (e.g., 'sub_001')
        
        Returns:
            Subject name if found, None otherwise
        """
        if not subject_id:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Normalize subject_id first
            normalized_id = self._normalize_subject_id(subject_id)
            cursor.execute('''
                SELECT DISTINCT subject
                FROM tests
                WHERE subject_id = ? AND subject IS NOT NULL
                LIMIT 1
            ''', (normalized_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
        return None

    def _get_all_subjects_for_scenario(self, scenario: str, data_type: str) -> List[str]:
        """특정 시나리오에 대한 모든 피험자 목록 조회 (raw data의 subject_id 사용)"""
        # Try to get from tests table first (if available)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 시나리오 정규화 (lw -> long_wave, slc -> single_lane_change, s&g -> stop_and_go)
            scenario_patterns = {
                'lw': ['long_wave', 'longwave'],
                'slc': ['single_lane_change', 'single_lane'],
                's&g': ['stop_and_go', 'stop_and_go']
            }
            
            scenario_variants = scenario_patterns.get(scenario.lower(), [scenario])
            placeholders = ','.join(['?'] * len(scenario_variants))
            
            cursor.execute(f'''
                SELECT DISTINCT t.subject_id
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                WHERE t.subject_id IS NOT NULL
                  AND (e.scenario IN ({placeholders}) OR e.scenario LIKE ?)
                ORDER BY t.subject_id
            ''', tuple(scenario_variants) + (f'%{scenario}%',))
            db_subjects = [row[0] for row in cursor.fetchall() if row[0]]
            if db_subjects:
                return db_subjects
        
        # Fallback: return empty list (don't guess)
        return []
    
    def _get_all_scenarios_for_subject(self, subject_id: str, data_type: str) -> List[str]:
        """특정 피험자에 대한 모든 시나리오 목록 조회 (raw data 기준)"""
        # subject_id를 정규화 (sub01 -> S001)
        normalized_subject_id = self._normalize_subject_id(subject_id)
        
        # Try tests table first
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 정규화된 subject_id와 원본 모두 검색
            cursor.execute('''
                SELECT DISTINCT e.scenario
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                WHERE (t.subject_id = ? OR t.subject_id = ?) AND e.scenario IS NOT NULL
                ORDER BY e.scenario
            ''', (subject_id, normalized_subject_id))
            scenarios = [row[0] for row in cursor.fetchall()]
            
            if scenarios:
                # Normalize scenario names (long_wave -> lw, single_lane_change -> slc, stop_and_go -> s&g)
                normalized = set()
                for s in scenarios:
                    if 'long_wave' in s.lower() or s == 'lw':
                        normalized.add('lw')
                    elif 'single_lane' in s.lower() or s == 'slc':
                        normalized.add('slc')
                    elif 'stop_and_go' in s.lower() or 's&g' in s.lower() or s == 's&g':
                        normalized.add('s&g')
                return sorted(list(normalized)) if normalized else sorted(scenarios)
        
        # Fallback: return empty list
        return []
    
    def _get_all_subjects(self) -> List[str]:
        """모든 피험자 목록 조회 (raw data의 subject_id 사용)"""
        # Try tests table first
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT subject_id
                FROM tests
                WHERE subject_id IS NOT NULL
                ORDER BY subject_id
            ''')
            db_subjects = [row[0] for row in cursor.fetchall()]
            if db_subjects:
                return db_subjects
        
        # Fallback: return empty list (don't guess)
        return []
    
    def _get_all_scenarios(self) -> List[str]:
        """모든 시나리오 목록 조회 (정규화)"""
        # Try tests table first
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT scenario FROM experiments WHERE scenario IS NOT NULL')
            scenarios = [row[0] for row in cursor.fetchall()]
            
            if scenarios:
                # Normalize to lw, slc, s&g
                normalized = set()
                for s in scenarios:
                    if 'long_wave' in s.lower() or s == 'lw':
                        normalized.add('lw')
                    elif 'single_lane' in s.lower() or s == 'slc':
                        normalized.add('slc')
                    elif 'stop_and_go' in s.lower() or 's&g' in s.lower() or s == 's&g':
                        normalized.add('s&g')
                return sorted(list(normalized)) if normalized else sorted(scenarios)
        
        # Fallback: return standard scenarios
        return ['lw', 's&g', 'slc']
    
    def _get_all_sensor_settings(self) -> List[int]:
        """모든 센서 설정 ID 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM sensor_settings ORDER BY id')
            return [row[0] for row in cursor.fetchall()]

    def _save_optimization_parameter(self, strategy_number: int, subject_id: Optional[str], 
                                   scenario: Optional[str], sensor_setting_code: Optional[str],
                                   parameter_type: str, data_type: str, file_path: str, file_name: str):
        """최적화 파라미터 저장 (junction tables 사용)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Strategy ID 조회
            cursor.execute('SELECT id FROM optimization_strategies WHERE strategy_number = ?', (strategy_number,))
            strategy_result = cursor.fetchone()
            if not strategy_result:
                return
            strategy_id = strategy_result[0]
            
            # 기존 파라미터 확인 (file_path 기준)
            cursor.execute('''
                SELECT id FROM optimization_parameters 
                WHERE strategy_id = ? AND parameter_type = ? AND data_type = ? AND file_path = ?
            ''', (strategy_id, parameter_type, data_type, file_path))
            existing = cursor.fetchone()
            
            if existing:
                parameter_id = existing[0]
                # 업데이트
                cursor.execute('''
                    UPDATE optimization_parameters 
                    SET file_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (file_name, parameter_id))
                # Junction tables는 삭제 후 재생성 (변경사항 반영)
                cursor.execute('DELETE FROM optimization_parameter_subjects WHERE parameter_id = ?', (parameter_id,))
                cursor.execute('DELETE FROM optimization_parameter_scenarios WHERE parameter_id = ?', (parameter_id,))
                cursor.execute('DELETE FROM optimization_parameter_sensor_settings WHERE parameter_id = ?', (parameter_id,))
            else:
                # 삽입
                cursor.execute('''
                    INSERT INTO optimization_parameters 
                    (strategy_id, parameter_type, data_type, file_path, file_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (strategy_id, parameter_type, data_type, file_path, file_name))
                conn.commit()
                parameter_id = cursor.lastrowid
            
            # Junction tables에 데이터 저장
            # Strategy 0: 1 subject, 1 scenario, 1 sensor_setting
            if strategy_number == 0:
                if subject_id:
                    # Get subject_name from tests table
                    subject_name = self._get_subject_name(subject_id)
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_subjects (parameter_id, subject_id, subject_name) VALUES (?, ?, ?)', 
                                 (parameter_id, subject_id, subject_name))
                if scenario:
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_scenarios (parameter_id, scenario) VALUES (?, ?)', (parameter_id, scenario))
                if sensor_setting_code:
                    cursor.execute('SELECT id FROM sensor_settings WHERE sensor_setting_code = ?', (sensor_setting_code,))
                    sensor_result = cursor.fetchone()
                    if sensor_result:
                        cursor.execute('INSERT OR IGNORE INTO optimization_parameter_sensor_settings (parameter_id, sensor_setting_id) VALUES (?, ?)', (parameter_id, sensor_result[0]))
            
            # Strategy 1: 1 subject, ALL scenarios, no sensor_setting
            elif strategy_number == 1:
                if subject_id:
                    subject_name = self._get_subject_name(subject_id)
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_subjects (parameter_id, subject_id, subject_name) VALUES (?, ?, ?)', 
                                 (parameter_id, subject_id, subject_name))
                    # 모든 시나리오 추가
                    scenarios = self._get_all_scenarios_for_subject(subject_id, data_type)
                    for s in scenarios:
                        cursor.execute('INSERT OR IGNORE INTO optimization_parameter_scenarios (parameter_id, scenario) VALUES (?, ?)', (parameter_id, s))
            
            # Strategy 2: 1 subject, 1 scenario, no sensor_setting
            elif strategy_number == 2:
                if subject_id:
                    subject_name = self._get_subject_name(subject_id)
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_subjects (parameter_id, subject_id, subject_name) VALUES (?, ?, ?)', 
                                 (parameter_id, subject_id, subject_name))
                if scenario:
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_scenarios (parameter_id, scenario) VALUES (?, ?)', (parameter_id, scenario))
            
            # Strategy 3: ALL subjects, 1 scenario, no sensor_setting
            elif strategy_number == 3:
                if scenario:
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_scenarios (parameter_id, scenario) VALUES (?, ?)', (parameter_id, scenario))
                    # 모든 피험자 추가
                    subjects = self._get_all_subjects_for_scenario(scenario, data_type)
                    for s in subjects:
                        subject_name = self._get_subject_name(s)
                        cursor.execute('INSERT OR IGNORE INTO optimization_parameter_subjects (parameter_id, subject_id, subject_name) VALUES (?, ?, ?)', 
                                     (parameter_id, s, subject_name))
            
            # Strategy 4: ALL subjects, ALL scenarios, no sensor_setting
            elif strategy_number == 4:
                # 모든 피험자 추가
                subjects = self._get_all_subjects()
                for s in subjects:
                    subject_name = self._get_subject_name(s)
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_subjects (parameter_id, subject_id, subject_name) VALUES (?, ?, ?)', 
                                 (parameter_id, s, subject_name))
                # 모든 시나리오 추가
                scenarios = self._get_all_scenarios()
                for s in scenarios:
                    cursor.execute('INSERT OR IGNORE INTO optimization_parameter_scenarios (parameter_id, scenario) VALUES (?, ?)', (parameter_id, s))
            
            conn.commit()
            return parameter_id

    def _scan_result_files(self, result_path: str, data_type: str):
        """결과 파일 (.mat) 스캔 및 인덱싱 (hierarchical structure, metadata from folder path)"""
        print(f"  결과 파일 스캔: {result_path}")
        
        count = 0
        mat_count = 0
        for root, dirs, files in os.walk(result_path):
            for file in files:
                if file.endswith('.mat'):
                    mat_count += 1
                    file_path = os.path.join(root, file)
                    
                    # 폴더 경로에서 전략 번호 추출
                    strategy_number = self._extract_strategy_from_path(file_path, result_path)
                    if strategy_number is None:
                        print(f"[scan results] strategy number is None file_path: {file_path}")
                        continue
                    
                    # 폴더 경로에서 정보 추출 (hierarchical structure)
                    parsed = self._parse_result_file_from_path(file_path, result_path, strategy_number, file)
                    if parsed:
                        # 파라미터 찾기
                        # Strategy 0은 sensor_setting 필요, Strategy 1-4는 sensor_setting 무시
                        sensor_setting_code = parsed.get('sensor_setting') if strategy_number == 0 else None
                        parameter_id = self._find_parameter_id(
                            strategy_number=strategy_number,
                            subject_id=parsed.get('subject_id'),
                            scenario=parsed.get('scenario'),
                            sensor_setting_code=sensor_setting_code,
                            parameter_type=parsed.get('parameter_type'),
                            data_type=data_type
                        )
                        
                        if parameter_id:
                            self._save_optimization_result(
                                parameter_id=parameter_id,
                                model_name=parsed.get('model_name'),
                                result_file_path=file_path,
                                result_file_name=file
                            )
                            count += 1
                        else:
                            print(f"[scan results] param id not found: {parsed} | {file_path}")
                            continue
                    else:
                        print(f"[scan results] parsed not found: {file_path}")
                        continue
        
        print(f"    결과 파일 {count}개 인덱싱 완료")
        print(f'mat_count: {mat_count}')

    def _parse_result_file_from_path(self, file_path: str, base_path: str, strategy_number: int, filename: str) -> Optional[Dict]:
        """폴더 경로에서 결과 파일 정보 추출 (hierarchical structure)
        
        구조 예시:
        - Results/Strategy0_BySubjectScenarioSensor/[scenario_subject]/[sensor_setting]/[model]_[type].mat
        - Results/Strategy1_BySubject/[scenario_subject]/[sensor_setting]/[model]_[type].mat
        - Results/Strategy2_BySubjectScenario/[scenario_subject]/[model]_[type].mat
        - Results/Strategy3_ByScenario/[scenario]/[model]_[type].mat
        - Results/Strategy4_Universal/[model]_[type].mat
        """
        # base_path 이후의 경로 부분 추출
        rel_path = os.path.relpath(file_path, base_path)
        path_parts = list(Path(rel_path).parts)
        
        # 파일명 제거
        if path_parts and path_parts[-1] == filename:
            path_parts = path_parts[:-1]
        
        # Strategy 폴더 제거
        path_parts = [p for p in path_parts if not p.startswith('Strategy')]
        
        # 파일명에서 모델명과 parameter_type 추출
        model_name = None
        for model in ['MSIbase', 'OmanAP', 'OmanBP', 'OmanHILL']:
            if model in filename:
                model_name = model
                break
        
        if not model_name:
            return None
        
        if 'fullopt' in filename:
            parameter_type = 'fullopt'
        elif '3opt' in filename:
            parameter_type = '3opt'
        else:
            parameter_type = 'fullopt'
        
        # Strategy 0: scenario_subject/sensor_setting/file.mat
        if strategy_number == 0:
            if len(path_parts) >= 2:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                sensor_setting = path_parts[1]    # e.g., "H-IMU_N-VV"
                # Strip .tmp suffix if present (some directories have .tmp suffix)
                if sensor_setting.endswith('.tmp'):
                    sensor_setting = sensor_setting[:-4]
                
                if '_' in scenario_subject:
                    scenario, subject_id_raw = scenario_subject.split('_', 1)
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'sensor_setting': sensor_setting,
                        'model_name': model_name,
                        'parameter_type': parameter_type
                    }
        
        # Strategy 1: scenario_subject/sensor_setting/file.mat
        elif strategy_number == 1:
            if len(path_parts) >= 2:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                sensor_setting = path_parts[1]    # e.g., "H-IMU_N-VV"
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': scenario,
                    'subject_id': subject_id,
                    'sensor_setting': sensor_setting,  # Results have sensor_setting
                    'model_name': model_name,
                    'parameter_type': parameter_type
                }
        
        # Strategy 2: scenario_subject/file.mat
        elif strategy_number == 2:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': scenario,
                    'subject_id': subject_id,
                    'sensor_setting': None,
                    'model_name': model_name,
                    'parameter_type': parameter_type
                }
        
        # Strategy 3: scenario/file.mat
        elif strategy_number == 3:
            if path_parts:
                scenario_subject = path_parts[0]
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                return {
                    'scenario': scenario,
                    'subject_id': None,
                    'sensor_setting': None,
                    'model_name': model_name,
                    'parameter_type': parameter_type
                }
        
        # Strategy 4: file.mat (universal)
        elif strategy_number == 4:
            return {
                'scenario': None,
                'subject_id': None,
                'sensor_setting': None,
                'model_name': model_name,
                'parameter_type': parameter_type
            }
        
        return None

    def _parse_result_file_from_filename(self, filename: str, strategy_number: int) -> Optional[Dict]:
        """결과 파일명에서 정보 추출 (flat structure, no folder hierarchy)
        
        예상 파일명 형식:
        - MSIbase_Strategy0_sub_001_lw_H-IMU_N-VV_주행_fullopt.mat
        - OmanAP_Strategy1_sub_001_주행_fullopt.mat
        """
        # 파일명에서 모델명과 parameter_type 추출
        model_name = None
        for model in ['MSIbase', 'OmanAP', 'OmanBP', 'OmanHILL']:
            if model in filename:
                model_name = model
                break
        
        if not model_name:
            return None
        
        if 'fullopt' in filename:
            parameter_type = 'fullopt'
        elif '3opt' in filename:
            parameter_type = '3opt'
        else:
            parameter_type = 'fullopt'
        
        # 파일명을 언더스코어로 분리
        parts = filename.replace('.mat', '').split('_')
        
        # 모델명 제거 (예: MSIbase_Strategy0_sub_001_lw_H-IMU_N-VV_주행_fullopt)
        parts_clean = [p for p in parts if p != model_name and p != '']
        
        # Strategy 0: Strategy0_sub_001_lw_H-IMU_N-VV_주행_fullopt
        if strategy_number == 0:
            try:
                parts_clean = [p for p in parts_clean if not p.startswith('Strategy')]
                # sub_001, lw, H-IMU, N-VV 형식 찾기
                subject_idx = None
                for i, p in enumerate(parts_clean):
                    if p.startswith('sub'):
                        subject_idx = i
                        break
                
                if subject_idx is not None and subject_idx + 1 < len(parts_clean):
                    subject_id_raw = parts_clean[subject_idx]
                    scenario = parts_clean[subject_idx + 1]  # lw, slc, s&g
                    
                    # Sensor setting 찾기
                    sensor_parts = []
                    for i in range(subject_idx + 2, len(parts_clean)):
                        if parts_clean[i] in ['주행', '주행+휴식', 'fullopt', '3opt']:
                            break
                        sensor_parts.append(parts_clean[i])
                    
                    sensor_setting = '-'.join(sensor_parts) if sensor_parts else None
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    
                return {
                    'scenario': scenario,
                    'subject_id': subject_id,
                    'sensor_setting': sensor_setting,
                    'model_name': model_name,
                    'parameter_type': parameter_type
                }
            except:
                pass
        
        # Strategy 1-4: Strategy1_sub_001_주행_fullopt 또는 Strategy3_lw_주행_fullopt
        else:
            try:
                parts_clean = [p for p in parts_clean if not p.startswith('Strategy') and p not in ['주행', '주행+휴식', 'fullopt', '3opt'] and p != '']
                
                if strategy_number == 1:
                    # Strategy1: sub_001
                    if parts_clean:
                        subject_id_raw = parts_clean[0]
                        subject_id = self._normalize_subject_id(subject_id_raw)
                        return {
                            'scenario': None,
                            'subject_id': subject_id,
                            'sensor_setting': None,
                            'model_name': model_name,
                            'parameter_type': parameter_type
                        }
                elif strategy_number == 2:
                    # Strategy2: sub_001, lw
                    if len(parts_clean) >= 2:
                        subject_id_raw = parts_clean[0]
                        scenario = parts_clean[1]
                        subject_id = self._normalize_subject_id(subject_id_raw)
                        return {
                            'scenario': scenario,
                            'subject_id': subject_id,
                            'sensor_setting': None,
                            'model_name': model_name,
                            'parameter_type': parameter_type
                        }
                elif strategy_number == 3:
                    # Strategy3: lw
                    if parts_clean:
                        scenario = parts_clean[0]
                        return {
                            'scenario': scenario,
                            'subject_id': None,
                            'sensor_setting': None,
                            'model_name': model_name,
                            'parameter_type': parameter_type
                        }
                elif strategy_number == 4:
                    # Strategy4: universal
                    return {
                        'scenario': None,
                        'subject_id': None,
                        'sensor_setting': None,
                        'model_name': model_name,
                        'parameter_type': parameter_type
                    }
            except:
                pass
        
        return None

    def _find_parameter_id(self, strategy_number: int, subject_id: Optional[str], 
                          scenario: Optional[str], sensor_setting_code: Optional[str],
                          parameter_type: str, data_type: str) -> Optional[int]:
        """
        Find the parameter ID from the database using the provided criteria.

        Args:
            strategy_number (int): Optimization strategy number (0-4).
            subject_id (Optional[str]): Subject identifier (can be None depending on strategy).
            scenario (Optional[str]): Scenario name or code (can be None depending on strategy).
            sensor_setting_code (Optional[str]): Sensor setting code (used for strategy 0).
            parameter_type (str): Type of parameter (e.g., 'fullopt', '3opt').
            data_type (str): Data type (e.g., '주행', '주행+휴식').

        Returns:
            Optional[int]: The matching optimization parameter ID, or None if not found.

        Notes:
            - Uses different matching criteria depending on the strategy_number.
            - Joins with subjects, scenarios, and sensor_settings junction tables as appropriate for each strategy.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM optimization_strategies WHERE strategy_number = ?', (strategy_number,))
            strategy_result = cursor.fetchone()
            if not strategy_result:
                return None
            strategy_id = strategy_result[0]
            
            # 기본 파라미터 조회
            query = '''
                SELECT DISTINCT op.id
                FROM optimization_parameters op
                WHERE op.strategy_id = ? AND op.parameter_type = ? AND op.data_type = ?
            '''
            params = [strategy_id, parameter_type, data_type]
            
            # Strategy 0: exact match on subject, scenario, sensor_setting
            if strategy_number == 0:
                if subject_id:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_subjects ops
                            WHERE ops.parameter_id = op.id AND ops.subject_id = ?
                        )
                    '''
                    params.append(subject_id)
                
                if scenario:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_scenarios opsc
                            WHERE opsc.parameter_id = op.id AND opsc.scenario = ?
                        )
                    '''
                    params.append(scenario)
                
                if sensor_setting_code:
                    cursor.execute('SELECT id FROM sensor_settings WHERE sensor_setting_code = ?', (sensor_setting_code,))
                    sensor_result = cursor.fetchone()
                    if sensor_result:
                        query += '''
                            AND EXISTS (
                                SELECT 1 FROM optimization_parameter_sensor_settings opss
                                WHERE opss.parameter_id = op.id AND opss.sensor_setting_id = ?
                            )
                        '''
                        params.append(sensor_result[0])
            
            # Strategy 1: match on subject (scenario is in junction table)
            elif strategy_number == 1:
                if subject_id:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_subjects ops
                            WHERE ops.parameter_id = op.id AND ops.subject_id = ?
                        )
                    '''
                    params.append(subject_id)
            
            # Strategy 2: match on subject and scenario
            elif strategy_number == 2:
                if subject_id:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_subjects ops
                            WHERE ops.parameter_id = op.id AND ops.subject_id = ?
                        )
                    '''
                    params.append(subject_id)
                
                if scenario:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_scenarios opsc
                            WHERE opsc.parameter_id = op.id AND opsc.scenario = ?
                        )
                    '''
                    params.append(scenario)
            
            # Strategy 3: match on scenario (subject is in junction table)
            elif strategy_number == 3:
                if scenario:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_scenarios opsc
                            WHERE opsc.parameter_id = op.id AND opsc.scenario = ?
                        )
                    '''
                    params.append(scenario)
            
            # Strategy 4: universal - always match (no filtering needed)
            # But if searching by specific criteria, we can still filter
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None

    def _save_optimization_result(self, parameter_id: int, model_name: str, 
                                 result_file_path: str, result_file_name: str):
        """최적화 결과 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 기존 결과 확인
            cursor.execute('''
                SELECT id FROM optimization_results 
                WHERE parameter_id = ? AND model_name = ?
            ''', (parameter_id, model_name))
            existing = cursor.fetchone()
            
            if existing:
                # 업데이트
                cursor.execute('''
                    UPDATE optimization_results 
                    SET result_file_path = ?, result_file_name = ?
                    WHERE id = ?
                ''', (result_file_path, result_file_name, existing[0]))
            else:
                # 삽입
                cursor.execute('''
                    INSERT INTO optimization_results 
                    (parameter_id, model_name, result_file_path, result_file_name)
                    VALUES (?, ?, ?, ?)
                ''', (parameter_id, model_name, result_file_path, result_file_name))
            
            conn.commit()

    def _scan_visualization_files(self, graph_path: str, data_type: str):
        """시각화 파일 (.png) 스캔 및 인덱싱 (hierarchical structure, metadata from folder path)"""
        print(f"  시각화 파일 스캔: {graph_path}")
        
        count = 0
        png_count = 0
        for root, dirs, files in os.walk(graph_path):
            for file in files:
                if file.endswith('.png'):
                    png_count += 1
                    file_path = os.path.join(root, file)
                    # print(file_path)
                    
                    # 폴더 경로에서 전략 번호 추출
                    strategy_number = self._extract_strategy_from_path(file_path, graph_path)
                    if strategy_number is None:
                        print("[scan visualization] strat == None")
                        continue
                    
                    # 폴더 경로에서 정보 추출 (hierarchical structure)
                    parsed = self._parse_visualization_file_from_path(file_path, graph_path, strategy_number, file)
                    # print(f'parsed: {parsed}')
                    if parsed:
                        # 파라미터 찾기 (시각화는 fullopt만, sensor_setting 무시)
                        parameter_id = self._find_parameter_id(
                            strategy_number=strategy_number,
                            subject_id=parsed.get('subject_id'),
                            scenario=parsed.get('scenario'),
                            sensor_setting_code=None,  # 그래프는 sensor_setting 구분 없음
                            parameter_type='fullopt',  # 그래프는 fullopt만
                            data_type=data_type
                        )
                        # print(f'param id: {parameter_id}')
                        if parameter_id:
                            self._save_optimization_visualization(
                                parameter_id=parameter_id,
                                visualization_type=parsed.get('visualization_type'),
                                model_name=parsed.get('model_name'),
                                graph_file_path=file_path,
                                graph_file_name=file
                            )
                            count += 1
                            # print(f'count up {count}')
                        else:
                            print(f'[scan visualization] param id not found: {parsed}')
                            continue
                    else:
                        print(f'[scan visualization]  parsed not found: {file_path}')
                        continue
        
        print(f"    시각화 파일 {count}개 인덱싱 완료")
        print(f'png_count: {png_count}')

    def _parse_visualization_file_from_path(self, file_path: str, base_path: str, strategy_number: int, filename: str) -> Optional[Dict]:
        """폴더 경로에서 시각화 파일 정보 추출 (hierarchical structure)
        
        구조 예시:
        - Graph/Strategy0_BySubjectScenarioSensor/[scenario_subject]/[file].png (no sensor_setting)
        - Graph/Strategy1_BySubject/[scenario_subject]/[file].png
        - Graph/Strategy2_BySubjectScenario/[scenario_subject]/[file].png
        - Graph/Strategy3_ByScenario/[scenario]/[file].png
        - Graph/Strategy4_Universal/[file].png
        """
        # base_path 이후의 경로 부분 추출
        rel_path = os.path.relpath(file_path, base_path)
        path_parts = list(Path(rel_path).parts)
        
        # 파일명 제거
        if path_parts and path_parts[-1] == filename:
            path_parts = path_parts[:-1]
        
        # Strategy 폴더 제거
        path_parts = [p for p in path_parts if not p.startswith('Strategy')]
        
        # 파일명에서 모델명 확인
        model_name = None
        for model in ['MSIbase', 'OmanAP', 'OmanBP', 'OmanHILL']:
            if model in filename:
                model_name = model
                break
        
        if model_name:
            visualization_type = 'model_specific'
        else:
            visualization_type = 'comparison'
            model_name = None
        
        # Strategy 0: scenario_subject/file.png (no sensor_setting for visualizations)
        if strategy_number == 0:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                if '_' in scenario_subject:
                    scenario, subject_id_raw = scenario_subject.split('_', 1)
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'visualization_type': visualization_type,
                        'model_name': model_name
                    }
        
        # Strategy 1: scenario_subject/file.png
        elif strategy_number == 1:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': scenario,
                    'subject_id': subject_id,
                    'visualization_type': visualization_type,
                    'model_name': model_name
                }
        
        # Strategy 2: scenario_subject/file.png
        elif strategy_number == 2:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                subject_id = self._normalize_subject_id(subject_id_raw)
                return {
                    'scenario': scenario,
                    'subject_id': subject_id,
                    'visualization_type': visualization_type,
                    'model_name': model_name
                }
        
        # Strategy 3: scenario/file.png
        elif strategy_number == 3:
            if path_parts:
                scenario_subject = path_parts[0]  # e.g., "slc_sub09"
                scenario, subject_id_raw = scenario_subject.split('_', 1)
                return {
                    'scenario': scenario,
                    'subject_id': None,
                    'visualization_type': visualization_type,
                    'model_name': model_name
                }
        
        # Strategy 4: file.png (universal)
        elif strategy_number == 4:
            return {
                'scenario': None,
                'subject_id': None,
                'visualization_type': visualization_type,
                'model_name': model_name
            }
        
        return None

    def _parse_visualization_file_from_filename(self, filename: str, strategy_number: int) -> Optional[Dict]:
        """시각화 파일명에서 정보 추출 (flat structure, no folder hierarchy)
        
        예상 파일명 형식:
        - comparison_Strategy0_sub_001_lw_주행_fullopt.png
        - model_specific_MSIbase_Strategy0_sub_001_lw_주행_fullopt.png
        """
        # 파일명에서 모델명 확인
        model_name = None
        for model in ['MSIbase', 'OmanAP', 'OmanBP', 'OmanHILL']:
            if model in filename:
                model_name = model
                break
        
        if model_name:
            visualization_type = 'model_specific'
        else:
            visualization_type = 'comparison'
            model_name = None
        
        # 파일명을 언더스코어로 분리
        parts = filename.replace('.png', '').split('_')
        
        # visualization_type 제거 (comparison, model_specific)
        parts_clean = [p for p in parts if p not in ['comparison', 'model', 'specific'] and p != model_name and p != '']
        
        # Strategy 제거
        parts_clean = [p for p in parts_clean if not p.startswith('Strategy')]
        
        # Strategy 0: comparison_Strategy0_sub_001_lw_주행_fullopt
        if strategy_number == 0:
            try:
                # sub_001, lw 찾기
                subject_idx = None
                for i, p in enumerate(parts_clean):
                    if p.startswith('sub'):
                        subject_idx = i
                        break
                
                if subject_idx is not None and subject_idx + 1 < len(parts_clean):
                    subject_id_raw = parts_clean[subject_idx]
                    scenario = parts_clean[subject_idx + 1]  # lw, slc, s&g
                    subject_id = self._normalize_subject_id(subject_id_raw)
                    return {
                        'scenario': scenario,
                        'subject_id': subject_id,
                        'visualization_type': visualization_type,
                        'model_name': model_name
                    }
            except:
                pass
        
        # Strategy 1-4: parsing similar to parameters
        else:
            try:
                parts_clean = [p for p in parts_clean if p not in ['주행', '주행+휴식', 'fullopt', '3opt'] and p != '']
                
                if strategy_number == 1:
                    # Strategy1: sub_001
                    if parts_clean:
                        subject_id_raw = parts_clean[0]
                        subject_id = self._normalize_subject_id(subject_id_raw)
                        return {
                            'scenario': None,
                            'subject_id': subject_id,
                            'visualization_type': visualization_type,
                            'model_name': model_name
                        }
                elif strategy_number == 2:
                    # Strategy2: sub_001, lw
                    if len(parts_clean) >= 2:
                        subject_id_raw = parts_clean[0]
                        scenario = parts_clean[1]
                        subject_id = self._normalize_subject_id(subject_id_raw)
                        return {
                            'scenario': scenario,
                            'subject_id': subject_id,
                            'visualization_type': visualization_type,
                            'model_name': model_name
                        }
                elif strategy_number == 3:
                    # Strategy3: lw
                    if parts_clean:
                        scenario = parts_clean[0]
                        return {
                            'scenario': scenario,
                            'subject_id': None,
                            'visualization_type': visualization_type,
                            'model_name': model_name
                        }
                elif strategy_number == 4:
                    # Strategy4: universal
                    return {
                        'scenario': None,
                        'subject_id': None,
                        'visualization_type': visualization_type,
                        'model_name': model_name
                    }
            except:
                pass
        
        return None

    def _save_optimization_visualization(self, parameter_id: int, visualization_type: str,
                                        model_name: Optional[str], graph_file_path: str, graph_file_name: str):
        """최적화 시각화 저장"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 기존 시각화 확인
            query = '''
                SELECT id FROM optimization_visualizations 
                WHERE parameter_id = ? AND visualization_type = ?
            '''
            params = [parameter_id, visualization_type]
            
            if model_name:
                query += ' AND model_name = ?'
                params.append(model_name)
            else:
                query += ' AND model_name IS NULL'
            
            cursor.execute(query, params)
            existing = cursor.fetchone()
            
            if existing:
                # 업데이트
                cursor.execute('''
                    UPDATE optimization_visualizations 
                    SET graph_file_path = ?, graph_file_name = ?
                    WHERE id = ?
                ''', (graph_file_path, graph_file_name, existing[0]))
            else:
                # 삽입
                cursor.execute('''
                    INSERT INTO optimization_visualizations 
                    (parameter_id, visualization_type, model_name, graph_file_path, graph_file_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (parameter_id, visualization_type, model_name, graph_file_path, graph_file_name))
            
            conn.commit()

    def search_optimization_parameters(self, subject_id: Optional[str] = None, 
                                      subject: Optional[str] = None,
                                      scenario: Optional[str] = None, 
                                      sensor_setting_code: Optional[str] = None,
                                      strategy_number: Optional[int] = None,
                                      model_name: Optional[str] = None,
                                      parameter_type: Optional[str] = None,
                                      data_type: Optional[str] = None) -> List[Dict]:
        """최적화 파라미터 검색 (junction tables 사용)
        
        Args:
            subject_id: 피험자 ID (예: 'sub_001')
            subject: 피험자 이름 (예: '정현용')
            scenario: 시나리오 (예: 'lw', 'slc', 's&g')
            sensor_setting_code: 센서 설정 코드 (예: 'H-IMU_N-VV')
            strategy_number: 전략 번호 (0-4)
            model_name: 모델명 (예: 'MSIbase', 'OmanAP')
            parameter_type: 파라미터 타입 ('fullopt', '3opt')
            data_type: 데이터 타입 ('주행', '주행+휴식')
        
        Returns:
            파라미터 목록 (각 파라미터에 results와 visualizations 포함)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # subject_name으로 검색하는 경우, subject_id로 변환
            if subject and not subject_id:
                # tests 테이블에서 subject_name으로 subject_id 찾기
                cursor.execute('''
                    SELECT DISTINCT subject_id
                    FROM tests
                    WHERE subject = ? AND subject_id IS NOT NULL
                    LIMIT 1
                ''', (subject,))
                result = cursor.fetchone()
                if result:
                    subject_id = self._normalize_subject_id(result[0])
                else:
                    # subject_name으로 직접 검색 (junction table)
                    pass
            
            # subject_id 정규화
            if subject_id:
                subject_id = self._normalize_subject_id(subject_id)
            
            # 기본 쿼리: 파라미터 + 전략 정보
            query = '''
                SELECT DISTINCT op.id, op.strategy_id, op.parameter_type, op.data_type,
                       op.file_path, op.file_name, op.created_at, op.updated_at,
                       os.strategy_number, os.strategy_name, os.description
                FROM optimization_parameters op
                JOIN optimization_strategies os ON op.strategy_id = os.id
                WHERE 1=1
            '''
            params = []
            
            # 필터 조건 추가
            if strategy_number is not None:
                query += ' AND os.strategy_number = ?'
                params.append(strategy_number)
            
            if parameter_type:
                query += ' AND op.parameter_type = ?'
                params.append(parameter_type)
            
            if data_type:
                query += ' AND op.data_type = ?'
                params.append(data_type)
            
            # Junction tables를 통한 필터링
            if subject_id:
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM optimization_parameter_subjects ops
                        WHERE ops.parameter_id = op.id AND ops.subject_id = ?
                    )
                '''
                params.append(subject_id)
            elif subject:
                # subject_name으로 검색 (junction table의 subject_name 사용)
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM optimization_parameter_subjects ops
                        WHERE ops.parameter_id = op.id AND ops.subject_name = ?
                    )
                '''
                params.append(subject)
            
            if scenario:
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM optimization_parameter_scenarios opsc
                        WHERE opsc.parameter_id = op.id AND opsc.scenario = ?
                    )
                '''
                params.append(scenario)
            
            if sensor_setting_code:
                cursor.execute('SELECT id FROM sensor_settings WHERE sensor_setting_code = ?', (sensor_setting_code,))
                sensor_result = cursor.fetchone()
                if sensor_result:
                    query += '''
                        AND EXISTS (
                            SELECT 1 FROM optimization_parameter_sensor_settings opss
                            WHERE opss.parameter_id = op.id AND opss.sensor_setting_id = ?
                        )
                    '''
                    params.append(sensor_result[0])
            
            # 모델명 필터링 (결과 테이블과 조인)
            if model_name:
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM optimization_results or_res
                        WHERE or_res.parameter_id = op.id AND or_res.model_name = ?
                    )
                '''
                params.append(model_name)
            
            query += ' ORDER BY op.id'
            
            cursor.execute(query, params)
            parameter_rows = cursor.fetchall()
            
            # 각 파라미터에 대해 상세 정보 조회
            results = []
            for row in parameter_rows:
                param_id = row[0]
                param_dict = {
                    'id': param_id,
                    'strategy_id': row[1],
                    'parameter_type': row[2],
                    'data_type': row[3],
                    'file_path': row[4],
                    'file_name': row[5],
                    'created_at': row[6],
                    'updated_at': row[7],
                    'strategy': {
                        'number': row[8],
                        'name': row[9],
                        'description': row[10]
                    },
                    'subjects': [],
                    'scenarios': [],
                    'sensor_settings': [],
                    'results': [],
                    'visualizations': []
                }
                
                # Junction tables에서 subjects, scenarios, sensor_settings 조회
                cursor.execute('''
                    SELECT subject_id, subject_name FROM optimization_parameter_subjects
                    WHERE parameter_id = ?
                    ORDER BY subject_id
                ''', (param_id,))
                param_dict['subjects'] = [
                    {'id': row[0], 'name': row[1]} 
                    for row in cursor.fetchall()
                ]
                
                cursor.execute('''
                    SELECT scenario FROM optimization_parameter_scenarios
                    WHERE parameter_id = ?
                    ORDER BY scenario
                ''', (param_id,))
                param_dict['scenarios'] = [row[0] for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT ss.sensor_setting_code, ss.description
                    FROM optimization_parameter_sensor_settings opss
                    JOIN sensor_settings ss ON opss.sensor_setting_id = ss.id
                    WHERE opss.parameter_id = ?
                    ORDER BY ss.sensor_setting_code
                ''', (param_id,))
                param_dict['sensor_settings'] = [
                    {'code': row[0], 'description': row[1]}
                    for row in cursor.fetchall()
                ]
                
                # 결과 파일 조회
                cursor.execute('''
                    SELECT id, model_name, result_file_path, result_file_name, created_at
                    FROM optimization_results
                    WHERE parameter_id = ?
                    ORDER BY model_name
                ''', (param_id,))
                param_dict['results'] = [
                    {
                        'id': row[0],
                        'model_name': row[1],
                        'file_path': row[2],
                        'file_name': row[3],
                        'created_at': row[4]
                    }
                    for row in cursor.fetchall()
                ]
                
                # 시각화 파일 조회
                cursor.execute('''
                    SELECT id, visualization_type, model_name, graph_file_path, graph_file_name, created_at
                    FROM optimization_visualizations
                    WHERE parameter_id = ?
                    ORDER BY visualization_type, model_name
                ''', (param_id,))
                param_dict['visualizations'] = [
                    {
                        'id': row[0],
                        'type': row[1],
                        'model_name': row[2],
                        'file_path': row[3],
                        'file_name': row[4],
                        'created_at': row[5]
                    }
                    for row in cursor.fetchall()
                ]
                
                results.append(param_dict)
            
            return results

    def get_optimization_parameter_detail(self, parameter_id: int) -> Optional[Dict]:
        """최적화 파라미터 상세 정보 조회
        
        Args:
            parameter_id: 파라미터 ID
        
        Returns:
            파라미터 상세 정보 (모든 관련 데이터 포함), 없으면 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 파라미터 기본 정보 조회
            cursor.execute('''
                SELECT op.id, op.strategy_id, op.parameter_type, op.data_type,
                       op.file_path, op.file_name, op.file_hash, op.metadata,
                       op.created_at, op.updated_at,
                       os.strategy_number, os.strategy_name, os.description
                FROM optimization_parameters op
                JOIN optimization_strategies os ON op.strategy_id = os.id
                WHERE op.id = ?
            ''', (parameter_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            param_dict = {
                'id': row[0],
                'strategy_id': row[1],
                'parameter_type': row[2],
                'data_type': row[3],
                'file_path': row[4],
                'file_name': row[5],
                'file_hash': row[6],
                'metadata': row[7],
                'created_at': row[8],
                'updated_at': row[9],
                'strategy': {
                    'number': row[10],
                    'name': row[11],
                    'description': row[12]
                },
                'subjects': [],
                'scenarios': [],
                'sensor_settings': [],
                'results': [],
                'visualizations': []
            }
            
            # Junction tables에서 subjects, scenarios, sensor_settings 조회
            cursor.execute('''
                SELECT subject_id, subject_name FROM optimization_parameter_subjects
                WHERE parameter_id = ?
                ORDER BY subject_id
            ''', (parameter_id,))
            param_dict['subjects'] = [
                {'id': row[0], 'name': row[1]} 
                for row in cursor.fetchall()
            ]
            
            cursor.execute('''
                SELECT scenario FROM optimization_parameter_scenarios
                WHERE parameter_id = ?
                ORDER BY scenario
            ''', (parameter_id,))
            param_dict['scenarios'] = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT ss.id, ss.sensor_setting_code, ss.description, ss.sensor_components
                FROM optimization_parameter_sensor_settings opss
                JOIN sensor_settings ss ON opss.sensor_setting_id = ss.id
                WHERE opss.parameter_id = ?
                ORDER BY ss.sensor_setting_code
            ''', (parameter_id,))
            param_dict['sensor_settings'] = [
                {
                    'id': row[0],
                    'code': row[1],
                    'description': row[2],
                    'components': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # 결과 파일 조회
            cursor.execute('''
                SELECT id, model_name, result_file_path, result_file_name, file_hash, metadata, created_at
                FROM optimization_results
                WHERE parameter_id = ?
                ORDER BY model_name
            ''', (parameter_id,))
            param_dict['results'] = [
                {
                    'id': row[0],
                    'model_name': row[1],
                    'file_path': row[2],
                    'file_name': row[3],
                    'file_hash': row[4],
                    'metadata': row[5],
                    'created_at': row[6]
                }
                for row in cursor.fetchall()
            ]
            
            # 시각화 파일 조회
            cursor.execute('''
                SELECT id, visualization_type, model_name, graph_file_path, graph_file_name, file_hash, created_at
                FROM optimization_visualizations
                WHERE parameter_id = ?
                ORDER BY visualization_type, model_name
            ''', (parameter_id,))
            param_dict['visualizations'] = [
                {
                    'id': row[0],
                    'type': row[1],
                    'model_name': row[2],
                    'file_path': row[3],
                    'file_name': row[4],
                    'file_hash': row[5],
                    'created_at': row[6]
                }
                for row in cursor.fetchall()
            ]
            
            return param_dict

# 전역 데이터베이스 인스턴스
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'imu_data.db'))
db = IMUDatabase(db_path=DB_PATH)
