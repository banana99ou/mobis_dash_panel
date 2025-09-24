import sqlite3
import json
import os
import unicodedata
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
            conn.commit()

    def reset_tables(self):
        """테이블 데이터만 초기화 (테이블 구조는 유지)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 외래 키 제약 조건 비활성화
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # 테이블 데이터 삭제 (테이블 구조는 유지)
            cursor.execute('DELETE FROM data_quality')
            cursor.execute('DELETE FROM sensors')
            cursor.execute('DELETE FROM tests')
            cursor.execute('DELETE FROM experiments')
            
            # AUTOINCREMENT 카운터 리셋
            cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("data_quality", "sensors", "tests", "experiments")')
            
            # 외래 키 제약 조건 재활성화
            cursor.execute('PRAGMA foreign_keys = ON')
            
            conn.commit()
            print("테이블 데이터 초기화 완료")

    def drop_and_recreate_tables(self):
        """테이블을 완전히 삭제하고 재생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 외래 키 제약 조건 비활성화
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # 기존 테이블 삭제
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

    def search_tests(self, subject: str = None, sensor_id: str = None, 
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
                query += ' AND (' + ' OR '.join(conditions) + ')'
            
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

# 전역 데이터베이스 인스턴스
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'imu_data.db'))
db = IMUDatabase(db_path=DB_PATH)
