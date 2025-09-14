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
                    test_name TEXT NOT NULL,
                    subject TEXT,
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
                    position TEXT,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
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
            cursor.execute('DELETE FROM sensors')
            cursor.execute('DELETE FROM tests')
            cursor.execute('DELETE FROM experiments')
            
            # AUTOINCREMENT 카운터 리셋
            cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("sensors", "tests", "experiments")')
            
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
            experiment_info = metadata['experiment']
            sensors_info = metadata['sensors']
            # file_path 기준으로 기존 테스트 row와 센서 row를 무조건 삭제
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM tests WHERE file_path = ?', (metadata_path,))
                test_row = cursor.fetchone()
                if test_row:
                    test_id = test_row[0]
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
        except Exception as e:
            print(f"메타데이터 파일 처리 중 오류: {metadata_path} - {e}")

    def _save_experiment(self, experiment_info: Dict) -> int:
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

    def _save_test(self, experiment_id: int, experiment_info: Dict, metadata_path: str) -> int:
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

    def _save_sensor(self, test_id: int, sensor_info: Dict, metadata_path: str):
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

    def get_experiments(self) -> List[Dict]:
        """모든 실험 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, date, scenario, description, created_at
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
                SELECT id, test_name, subject, imu_count, created_at
                FROM tests
                WHERE experiment_id = ?
                ORDER BY test_name
            ''', (experiment_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_sensors_by_test(self, test_id: int) -> List[Dict]:
        """특정 테스트의 센서 목록 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sensor_id, position, file_name, file_path
                FROM sensors
                WHERE test_id = ?
                ORDER BY sensor_id
            ''', (test_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_test_details(self, test_id: int) -> Optional[Dict]:
        """테스트 상세 정보 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.test_name, t.subject, t.imu_count, t.created_at,
                       e.date, e.scenario
                FROM tests t
                JOIN experiments e ON t.experiment_id = e.id
                WHERE t.id = ?
            ''', (test_id,))
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None

# 전역 데이터베이스 인스턴스
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db', 'imu_data.db'))
db = IMUDatabase(db_path=DB_PATH)
