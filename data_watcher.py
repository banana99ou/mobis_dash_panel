import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from database import IMUDatabase

class DataEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.db = IMUDatabase()
        self._reindex_timer = None
        self._reindex_optimization_timer = None
        self._reindex_lock = threading.Lock()
        self._reindex_optimization_lock = threading.Lock()
        self._last_reindex_time = 0
        self._last_reindex_optimization_time = 0
        self._debounce_seconds = 2  # 2초 디바운싱

    def _schedule_reindex(self):
        """디바운싱을 적용한 재인덱싱 스케줄링"""
        current_time = time.time()
        
        # 마지막 재인덱싱 후 디바운싱 시간이 지나지 않았으면 스케줄링
        if current_time - self._last_reindex_time < self._debounce_seconds:
            if self._reindex_timer:
                self._reindex_timer.cancel()
            
            self._reindex_timer = threading.Timer(
                self._debounce_seconds - (current_time - self._last_reindex_time),
                self._perform_reindex
            )
            self._reindex_timer.start()
        else:
            # 즉시 재인덱싱 수행
            self._perform_reindex()

    def _perform_reindex(self):
        """실제 재인덱싱 수행 (스레드 안전)"""
        with self._reindex_lock:
            self._last_reindex_time = time.time()
            self._reset_and_reindex()
    
    def _schedule_optimization_reindex(self):
        """최적화 데이터 재인덱싱 스케줄링 (디바운싱)"""
        current_time = time.time()
        
        if current_time - self._last_reindex_optimization_time < self._debounce_seconds:
            if self._reindex_optimization_timer:
                self._reindex_optimization_timer.cancel()
            
            self._reindex_optimization_timer = threading.Timer(
                self._debounce_seconds - (current_time - self._last_reindex_optimization_time),
                self._perform_optimization_reindex
            )
            self._reindex_optimization_timer.start()
        else:
            self._perform_optimization_reindex()
    
    def _perform_optimization_reindex(self):
        """최적화 데이터 재인덱싱 수행 (스레드 안전)"""
        with self._reindex_optimization_lock:
            self._last_reindex_optimization_time = time.time()
            self._reindex_optimization_data()
    
    def _reset_and_reindex(self, max_retries=5, wait_seconds=2):
        import sqlite3
        for attempt in range(max_retries):
            try:
                print(f"데이터 재인덱싱 시작 (시도 {attempt+1}/{max_retries})...")
                
                # 테이블 데이터만 초기화 (DB 파일 삭제 대신)
                self.db.reset_tables()
                
                # 메타데이터 인덱싱
                self.db.scan_and_index_data()
                print("메타데이터 인덱싱 완료!")
                break  # 성공 시 반복문 탈출
                
            except sqlite3.OperationalError as e:
                print(f"DB 초기화 실패 (시도 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"{wait_seconds}초 후 재시도...")
                    time.sleep(wait_seconds)
                else:
                    print("최대 재시도 횟수 초과. 테이블 재생성을 시도합니다.")
                    try:
                        # 마지막 시도로 테이블 완전 재생성
                        self.db.drop_and_recreate_tables()
                        self.db.scan_and_index_data()
                        print("테이블 재생성 후 인덱싱 완료!")
                        break
                    except Exception as final_e:
                        print(f"최종 실패: {final_e}")
            except Exception as e:
                print(f"초기화 중 알 수 없는 오류: {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_seconds)
                else:
                    print("최대 재시도 횟수 초과. 오류 발생.")
                    break
    
    def _reindex_optimization_data(self, max_retries=5, wait_seconds=2):
        """최적화 데이터 재인덱싱 (전체 스캔, reset_first=False로 증분 업데이트)"""
        import sqlite3
        for attempt in range(max_retries):
            try:
                print(f"최적화 데이터 재인덱싱 시작 (시도 {attempt+1}/{max_retries})...")
                
                # reset_first=False: 기존 데이터는 유지하고 새/변경된 파일만 추가/업데이트
                # _save_optimization_parameter 등에서 이미 UPSERT 로직이 있음
                self.db.scan_and_index_optimization_data(reset_first=False)
                print("최적화 데이터 인덱싱 완료!")
                break
                
            except sqlite3.OperationalError as e:
                print(f"최적화 데이터 인덱싱 실패 (시도 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"{wait_seconds}초 후 재시도...")
                    time.sleep(wait_seconds)
                else:
                    print("최적화 데이터 인덱싱 최대 재시도 횟수 초과")
            except Exception as e:
                print(f"최적화 데이터 인덱싱 중 알 수 없는 오류: {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_seconds)
                else:
                    print("최적화 데이터 인덱싱 최대 재시도 횟수 초과")
                    break
    
    def _is_optimization_file(self, file_path):
        """파일이 최적화 관련 파일인지 확인
        
        현재 구조: data/motion_sickness/optimization/Driving/Parameter|Results|Graph/...
        또는: data/motion_sickness/optimization/Driving+Rest/Parameter|Results|Graph/...
        """
        optimization_extensions = ['.m', '.mat', '.png']
        
        # 확장자 확인
        if any(file_path.endswith(ext) for ext in optimization_extensions):
            # 경로에 optimization 폴더가 있는지 확인
            if 'optimization' in file_path:
                # Parameter, Results, Graph 폴더 중 하나가 경로에 있는지 확인
                path_lower = file_path.lower()
                if 'parameter' in path_lower or 'results' in path_lower or 'graph' in path_lower:
                    return True
            # 또는 파일명에 Strategy가 있는지 확인 (파일명 기반, 하위 호환성)
            if 'Strategy' in os.path.basename(file_path) or 'strategy' in os.path.basename(file_path).lower():
                return True
        return False

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # 메타데이터 파일 처리
        if file_path.endswith('metadata.json'):
            print(f"새 메타데이터 파일 감지: {file_path}")
            self._schedule_reindex()
        # 최적화 파일 처리
        elif self._is_optimization_file(file_path):
            print(f"새 최적화 파일 감지: {file_path}")
            self._schedule_optimization_reindex()

    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # 메타데이터 파일 처리
        if file_path.endswith('metadata.json'):
            print(f"메타데이터 파일 수정 감지: {file_path}")
            self._schedule_reindex()
        # 최적화 파일 처리
        elif self._is_optimization_file(file_path):
            print(f"최적화 파일 수정 감지: {file_path}")
            self._schedule_optimization_reindex()

    def on_deleted(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # 메타데이터 파일 처리
        if file_path.endswith('metadata.json'):
            print(f"메타데이터 파일 삭제 감지: {file_path}")
            self._schedule_reindex()
        # 최적화 파일 처리
        elif self._is_optimization_file(file_path):
            print(f"최적화 파일 삭제 감지: {file_path}")
            self._schedule_optimization_reindex()

def watch_data_directory(path="./data"):
    event_handler = DataEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"[Watcher] {path} 디렉토리 감시 시작...")
    print(f"[Watcher] metadata.json 파일 변경 시 자동 재인덱싱 (디바운싱: {event_handler._debounce_seconds}초)")
    print(f"[Watcher] 최적화 파일 (.m, .mat, .png) 변경 시 자동 재인덱싱 (디바운싱: {event_handler._debounce_seconds}초)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Watcher] 감시 중단...")
        if event_handler._reindex_timer:
            event_handler._reindex_timer.cancel()
        if event_handler._reindex_optimization_timer:
            event_handler._reindex_optimization_timer.cancel()
        observer.stop()
    observer.join()
    print("[Watcher] 감시 종료")

if __name__ == "__main__":
    watch_data_directory() 