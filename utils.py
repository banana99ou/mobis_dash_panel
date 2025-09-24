import pandas as pd
import os
import json
from typing import Dict, List, Optional, Tuple
from database import db

def load_imu_data(file_path: str) -> pd.DataFrame:
    """IMU CSV 파일을 로드하고 전처리"""
    try:
        df = pd.read_csv(file_path)
        
        # 기본 컬럼 확인 및 정리
        required_columns = ['t_sec', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
        
        # 컬럼명 정규화 (대소문자, 공백 제거)
        df.columns = df.columns.str.strip().str.lower()
        
        # 필수 컬럼이 있는지 확인
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"경고: 필수 컬럼이 누락되었습니다: {missing_columns}")
        
        # 시간 컬럼이 숫자인지 확인
        if 't_sec' in df.columns:
            df['t_sec'] = pd.to_numeric(df['t_sec'], errors='coerce')
        
        return df
    
    except Exception as e:
        print(f"파일 로드 중 오류: {file_path} - {e}")
        return pd.DataFrame()

def get_experiment_data() -> List[Dict]:
    """데이터베이스에서 실험 목록 조회"""
    return db.get_experiments()

def get_test_data(experiment_id: int) -> List[Dict]:
    """특정 실험의 테스트 목록 조회"""
    return db.get_tests_by_experiment(experiment_id)

def get_sensor_data(test_id: int) -> List[Dict]:
    """특정 테스트의 센서 목록 조회"""
    return db.get_sensors_by_test(test_id)

def load_multiple_sensor_data(sensor_paths: List[str]) -> Dict[str, pd.DataFrame]:
    """여러 센서 데이터를 동시에 로드"""
    sensor_data = {}
    
    for path in sensor_paths:
        if os.path.exists(path):
            # Extract sensor ID from filename (e.g., imu_console_001.csv -> imu_console_001)
            sensor_id = os.path.basename(path).replace('.csv', '')
            df = load_imu_data(path)
            if not df.empty:
                sensor_data[sensor_id] = df
    
    return sensor_data

def create_comparison_figure(sensor_data: Dict[str, pd.DataFrame], 
                           data_type: str = 'acceleration') -> Dict:
    """다중 센서 데이터 비교 그래프 생성"""
    
    if data_type == 'acceleration':
        columns = ['ax', 'ay', 'az']
        title = '가속도 비교'
        y_title = '가속도 (m/s²)'
        axis_labels = {'ax': 'X축', 'ay': 'Y축', 'az': 'Z축'}
    else:  # gyroscope
        columns = ['gx', 'gy', 'gz']
        title = '각속도 비교'
        y_title = '각속도 (rad/s)'
        axis_labels = {'gx': 'X축', 'gy': 'Y축', 'gz': 'Z축'}
    
    # 센서별 고유 색상 정의
    sensor_colors = [
        '#1f77b4',  # 파란색
        '#ff7f0e',  # 주황색
        '#2ca02c',  # 초록색
        '#d62728',  # 빨간색
        '#9467bd',  # 보라색
        '#8c564b',  # 갈색
        '#e377c2',  # 분홍색
        '#7f7f7f',  # 회색
        '#bcbd22',  # 올리브색
        '#17becf'   # 청록색
    ]
    
    # 축별 선 스타일 정의
    axis_styles = {
        'ax': {'dash': 'solid', 'width': 2.5},      # X축: 실선, 굵게
        'ay': {'dash': 'dash', 'width': 2.0},       # Y축: 점선, 중간
        'az': {'dash': 'dot', 'width': 1.5},        # Z축: 점선, 얇게
        'gx': {'dash': 'solid', 'width': 2.5},      # X축: 실선, 굵게
        'gy': {'dash': 'dash', 'width': 2.0},       # Y축: 점선, 중간
        'gz': {'dash': 'dot', 'width': 1.5}         # Z축: 점선, 얇게
    }
    
    traces = []
    sensor_ids = list(sensor_data.keys())
    
    for i, (sensor_id, df) in enumerate(sensor_data.items()):
        if not df.empty and 't_sec' in df.columns:
            # 센서별 색상 선택 (색상이 부족하면 반복)
            color = sensor_colors[i % len(sensor_colors)]
            
            for col in columns:
                if col in df.columns:
                    traces.append({
                        'x': df['t_sec'].tolist(),
                        'y': df[col].tolist(),
                        'mode': 'lines',
                        'name': f'{sensor_id} - {axis_labels[col]}',
                        'line': {
                            'color': color,
                            'width': axis_styles[col]['width'],
                            'dash': axis_styles[col]['dash']
                        },
                        'legendgroup': sensor_id,
                        'showlegend': True
                    })
    
    return {
        'data': traces,
        'layout': {
            'title': {
                'text': title,
                'font': {'size': 18, 'color': '#2c3e50'}
            },
            'xaxis': {
                'title': '시간 (s)',
                'titlefont': {'size': 14},
                'tickfont': {'size': 12},
                'gridcolor': '#e1e5e9',
                'zeroline': False
            },
            'yaxis': {
                'title': y_title,
                'titlefont': {'size': 14},
                'tickfont': {'size': 12},
                'gridcolor': '#e1e5e9',
                'zeroline': False
            },
            'hovermode': 'x unified',
            'showlegend': True,
            'legend': {
                'font': {'size': 12},
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': '#ddd',
                'borderwidth': 1
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'height': 500,
            'margin': {'l': 60, 'r': 30, 't': 60, 'b': 60}
        }
    }

def get_data_summary(df: pd.DataFrame) -> Dict:
    """데이터 요약 정보 생성"""
    if df.empty:
        return {}
    
    summary = {
        'total_samples': len(df),
        'duration_seconds': 0,
        'sampling_rate': 0
    }
    
    if 't_sec' in df.columns:
        time_range = df['t_sec'].max() - df['t_sec'].min()
        summary['duration_seconds'] = round(time_range, 2)
        
        if time_range > 0:
            summary['sampling_rate'] = round(len(df) / time_range, 1)
    
    # 가속도 통계
    for axis in ['ax', 'ay', 'az']:
        if axis in df.columns:
            summary[f'{axis}_mean'] = round(df[axis].mean(), 3)
            summary[f'{axis}_std'] = round(df[axis].std(), 3)
            summary[f'{axis}_min'] = round(df[axis].min(), 3)
            summary[f'{axis}_max'] = round(df[axis].max(), 3)
    
    # 각속도 통계
    for axis in ['gx', 'gy', 'gz']:
        if axis in df.columns:
            summary[f'{axis}_mean'] = round(df[axis].mean(), 3)
            summary[f'{axis}_std'] = round(df[axis].std(), 3)
            summary[f'{axis}_min'] = round(df[axis].min(), 3)
            summary[f'{axis}_max'] = round(df[axis].max(), 3)
    
    return summary

def get_experiment_options() -> List[Dict]:
    """Dash 드롭다운용 실험 옵션 생성"""
    experiments = get_experiment_data()
    return [
        {'label': f"{exp.get('project', 'Unknown')} - {exp['date']} - {exp['scenario']}", 'value': exp['id']}
        for exp in experiments
    ]

def get_test_options(experiment_id: int) -> List[Dict]:
    """Dash 드롭다운용 테스트 옵션 생성"""
    tests = get_test_data(experiment_id)
    return [
        {'label': f"{test.get('test_id', test['test_name'])} - {test.get('subject', 'Unknown')} ({test['imu_count']}개 센서, {test.get('duration_sec', 0):.1f}초)", 'value': test['id']}
        for test in tests
    ]

def get_sensor_options(test_id: int) -> List[Dict]:
    """Dash 드롭다운용 센서 옵션 생성"""
    sensors = get_sensor_data(test_id)
    return [
        {'label': f"{sensor['sensor_id']} ({sensor.get('sensor_type', 'unknown')} - {sensor['position']}, {sensor.get('sample_rate_hz', 0):.1f}Hz)", 'value': sensor['id']}
        for sensor in sensors
    ]
