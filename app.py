import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
from database import db, IMUDatabase
import utils
import subprocess
import sys
import os
from flask import Flask, jsonify, request, send_from_directory, abort

# 테스트/실험 데이터 인덱싱 (최적화 테이블은 건드리지 않음)
db.scan_and_index_data()

# 최적화 데이터 인덱싱 (기존 데이터는 유지하고 새 파일만 추가)
db.scan_and_index_optimization_data(reset_first=False)

# 파일 감시 프로세스 실행 (중복 실행 방지)
def start_data_watcher():
    if sys.platform == "win32":
        python_cmd = "python"
    else:
        python_cmd = "python3"
    try:
        subprocess.Popen([python_cmd, "data_watcher.py"])  # 백그라운드 실행
        print("[Watcher] data_watcher.py 감시 프로세스 시작!")
    except Exception as e:
        print(f"[Watcher] 감시 프로세스 시작 실패: {e}")

start_data_watcher()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.server.config['JSON_AS_ASCII'] = False
app.server.json.ensure_ascii = False

# Flask API routes
@app.server.route('/api/search/tests', methods=['GET'])
def api_search_tests():
    """테스트 검색 API"""
    try:
        # 쿼리 파라미터 추출
        subject = request.args.get('subject')
        subject_id = request.args.get('subject_id')
        sensor_id = request.args.get('sensor_id')
        scenario = request.args.get('scenario')
        date = request.args.get('date')
        project = request.args.get('project')
        
        # 데이터베이스에서 검색
        results = db.search_tests(
            subject=subject,
            subject_id=subject_id,
            sensor_id=sensor_id,
            scenario=scenario,
            date=date,
            project=project
        )
        
        return jsonify({
            'status': 'success',
            'count': len(results),
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/tests/<int:test_id>/paths', methods=['GET'])
def api_get_test_paths(test_id):
    """테스트 파일 경로 조회 API"""
    try:
        result = db.get_test_paths(test_id)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': f'Test with ID {test_id} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/tests/<int:test_id>/sensors', methods=['GET'])
def api_get_test_sensors(test_id):
    """테스트 센서 정보 조회 API"""
    try:
        sensors = db.get_sensors_by_test(test_id)
        
        if not sensors:
            return jsonify({
                'status': 'error',
                'message': f'No sensors found for test ID {test_id}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'count': len(sensors),
            'data': sensors
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/health', methods=['GET'])
def api_health():
    """API 상태 확인"""
    return jsonify({
        'status': 'success',
        'message': 'API is running',
        'version': '1.0.0'
    })

@app.server.route('/api/optimization/parameters', methods=['GET'])
def api_search_optimization_parameters():
    """최적화 파라미터 검색 API"""
    try:
        # 쿼리 파라미터 추출
        subject_id = request.args.get('subject_id')
        subject = request.args.get('subject')  # subject name
        scenario = request.args.get('scenario')
        sensor = request.args.get('sensor')  # sensor_setting_code
        strategy = request.args.get('strategy')  # strategy_number (int)
        model = request.args.get('model')  # model_name
        parameter_type = request.args.get('parameter_type')  # 'fullopt' or '3opt'
        data_type = request.args.get('data_type')  # '주행' or '주행+휴식'
        
        # strategy를 int로 변환 (제공된 경우)
        strategy_number = None
        if strategy is not None:
            try:
                strategy_number = int(strategy)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid strategy number: {strategy}. Must be 0-4.'
                }), 400
        
        # 데이터베이스에서 검색
        results = db.search_optimization_parameters(
            subject_id=subject_id,
            subject=subject,
            scenario=scenario,
            sensor_setting_code=sensor,
            strategy_number=strategy_number,
            model_name=model,
            parameter_type=parameter_type,
            data_type=data_type
        )
        
        # 시각화 파일에 대한 웹 URL 생성
        workspace_root = os.path.abspath(os.path.dirname(__file__))
        for param in results:
            for viz in param['visualizations']:
                # 파일 경로를 웹 URL로 변환
                file_path = viz['file_path']
                # 경로 정규화
                file_path_norm = os.path.normpath(file_path)
                workspace_root_norm = os.path.normpath(workspace_root)
                
                # 절대 경로인 경우 워크스페이스 루트 기준으로 상대 경로 생성
                if os.path.isabs(file_path_norm):
                    if file_path_norm.startswith(workspace_root_norm):
                        relative_path = os.path.relpath(file_path_norm, workspace_root_norm)
                        # 경로 구분자를 URL 슬래시로 변환
                        relative_path = relative_path.replace(os.sep, '/')
                        viz['url'] = f'/api/optimization/files/{relative_path}'
                    else:
                        # 워크스페이스 밖의 경로는 처리하지 않음
                        viz['url'] = None
                else:
                    # 상대 경로인 경우 그대로 사용 (경로 구분자 정규화)
                    relative_path = file_path_norm.replace(os.sep, '/')
                    viz['url'] = f'/api/optimization/files/{relative_path}'
        
        return jsonify({
            'status': 'success',
            'count': len(results),
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/optimization/parameters/<int:parameter_id>', methods=['GET'])
def api_get_optimization_parameter_detail(parameter_id):
    """최적화 파라미터 상세 정보 조회 API"""
    try:
        result = db.get_optimization_parameter_detail(parameter_id)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': f'Parameter with ID {parameter_id} not found'
            }), 404
        
        # 시각화 파일에 대한 웹 URL 생성
        workspace_root = os.path.abspath(os.path.dirname(__file__))
        for viz in result['visualizations']:
            file_path = viz['file_path']
            # 경로 정규화
            file_path_norm = os.path.normpath(file_path)
            workspace_root_norm = os.path.normpath(workspace_root)
            
            # 절대 경로인 경우 워크스페이스 루트 기준으로 상대 경로 생성
            if os.path.isabs(file_path_norm):
                if file_path_norm.startswith(workspace_root_norm):
                    relative_path = os.path.relpath(file_path_norm, workspace_root_norm)
                    # 경로 구분자를 URL 슬래시로 변환
                    relative_path = relative_path.replace(os.sep, '/')
                    viz['url'] = f'/api/optimization/files/{relative_path}'
                else:
                    # 워크스페이스 밖의 경로는 처리하지 않음
                    viz['url'] = None
            else:
                # 상대 경로인 경우 그대로 사용 (경로 구분자 정규화)
                relative_path = file_path_norm.replace(os.sep, '/')
                viz['url'] = f'/api/optimization/files/{relative_path}'
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/optimization/files/<path:file_path>', methods=['GET'])
def api_serve_optimization_file(file_path):
    """최적화 파일 (PNG, MAT 등) 서빙"""
    try:
        workspace_root = os.path.abspath(os.path.dirname(__file__))
        
        # file_path가 이미 절대 경로인 경우 처리
        if os.path.isabs(file_path):
            # 절대 경로인 경우, 워크스페이스 루트 기준으로 정규화
            full_path = os.path.normpath(file_path)
        else:
            # 상대 경로인 경우 워크스페이스 루트 기준으로 조인
            full_path = os.path.normpath(os.path.join(workspace_root, file_path))
        
        # 보안: 워크스페이스 루트 밖으로 접근 방지
        workspace_root_norm = os.path.normpath(workspace_root)
        if not full_path.startswith(workspace_root_norm):
            abort(403)
        
        # 파일 존재 확인
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            abort(404)
        
        # 디렉토리와 파일명 분리
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        return send_from_directory(directory, filename)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.server.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_catch_all(path):
    """API 경로가 존재하지 않을 때 404 에러 반환"""
    return jsonify({
        'status': 'error',
        'message': f'API endpoint /api/{path} not found',
        'available_endpoints': [
            '/api/search/tests',
            '/api/tests/<id>/paths',
            '/api/tests/<id>/sensors',
            '/api/health',
            '/api/optimization/parameters',
            '/api/optimization/parameters/<id>',
            '/api/optimization/files/<path>'
        ]
    }), 404

# 비밀번호 설정 (실제 운영환경에서는 환경변수나 설정 파일에서 관리하는 것을 권장)
PASSWORD = "mobis1234"

def get_login_layout():
    """로그인 화면 레이아웃"""
    return html.Div([
        html.Div([
            html.H2("모비스 대시보드", style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
            html.Div([
                html.Label("비밀번호:", style={'display': 'block', 'marginBottom': '10px', 'fontWeight': 'bold', 'color': '#34495e'}),
                dcc.Input(
                    id='password-input',
                    type='password',
                    placeholder='비밀번호를 입력하세요',
                    style={
                        'width': '100%',
                        'padding': '12px',
                        'border': '2px solid #bdc3c7',
                        'borderRadius': '8px',
                        'fontSize': '16px',
                        'marginBottom': '20px'
                    }
                ),
                html.Button(
                    '로그인',
                    id='login-button',
                    n_clicks=0,
                    style={
                        'width': '107%',
                        'padding': '12px',
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '8px',
                        'fontSize': '16px',
                        'cursor': 'pointer',
                        'fontWeight': 'bold'
                    }
                ),
                html.Div(
                    id='login-error',
                    style={
                        'color': '#e74c3c',
                        'textAlign': 'center',
                        'marginTop': '10px',
                        'fontSize': '14px',
                        'minHeight': '20px'
                    }
                )
            ], style={'maxWidth': '400px', 'margin': '0 auto'})
        ], style={
            'position': 'absolute',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'backgroundColor': 'white',
            'padding': '40px',
            'borderRadius': '15px',
            'boxShadow': '0 10px 30px rgba(0,0,0,0.1)',
            'width': '90%',
            'maxWidth': '500px'
        })
    ], style={
        'height': '100vh',
        'backgroundColor': '#ecf0f1',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center'
    })

def get_sidebar_content(experiment_value=None, test_value=None, sensor_value=None, data_type_value='acceleration'):
    return html.Div([
        html.Button("≡", id="sidebar-toggle", style={'marginBottom': '10px', 'fontSize': '18px', 'background': 'none', 'border': 'none', 'cursor': 'pointer'}),
        html.Div([
            html.Div(id='info-panel', style={'marginBottom': '10px', 'fontSize': '12px'}),
            html.Label('실험 선택:', style={'fontWeight': 'bold', 'marginBottom': '3px', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='experiment-dropdown',
                options=[],
                value=experiment_value,
                placeholder='실험을 선택하세요',
                style={'marginBottom': '10px', 'fontSize': '12px'}
            ),
            html.Label('테스트 선택:', style={'fontWeight': 'bold', 'marginBottom': '3px', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='test-dropdown',
                options=utils.get_test_options(experiment_value) if experiment_value else [],
                value=test_value,
                placeholder='테스트를 선택하세요',
                style={'marginBottom': '10px', 'fontSize': '12px'}
            ),
            html.Label('센서 선택:', style={'fontWeight': 'bold', 'marginBottom': '3px', 'fontSize': '14px'}),
            dcc.Checklist(
                id='sensor-checklist',
                options=utils.get_sensor_options(test_value) if test_value else [],
                value=sensor_value if sensor_value is not None else [],
                style={'marginBottom': '10px', 'fontSize': '12px'}
            ),
            html.Label('데이터 타입:', style={'fontWeight': 'bold', 'marginBottom': '3px', 'fontSize': '14px'}),
            dcc.RadioItems(
                id='data-type-radio',
                options=[
                    {'label': '가속도', 'value': 'acceleration'},
                    {'label': '각속도', 'value': 'gyroscope'}
                ],
                value=data_type_value,
                style={'marginBottom': '10px', 'fontSize': '12px'}
            ),
            html.Button('데이터 로드', id='load-button', n_clicks=0,
                       style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                              'padding': '8px 16px', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '12px'}),
            html.Div(style={'marginTop': '10px', 'marginBottom': '10px', 'borderTop': '1px solid #ddd'}),
            html.Button('🔄 DB 새로고침', id='refresh-db-button', n_clicks=0,
                       style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                              'padding': '8px 16px', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '12px', 'width': '100%'}),
            html.Div(id='refresh-status', style={'marginTop': '5px', 'fontSize': '11px', 'color': '#666'}),
            html.Div(style={'marginTop': '10px', 'marginBottom': '10px', 'borderTop': '1px solid #ddd'}),
            html.Button('로그아웃', id='logout-button', n_clicks=0,
                       style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 
                              'padding': '8px 16px', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '12px', 'width': '100%'})
        ], id='sidebar-content')
    ])

def get_main_layout():
    """메인 대시보드 레이아웃"""
    return html.Div([
        dcc.Store(id='sidebar-collapsed', data=False),
        dcc.Store(id='summary-collapsed', data=False),
        dcc.Store(id='graph-height', data=400),
        dcc.Store(id='experiment-value', data=None),
        dcc.Store(id='test-value', data=None),
        dcc.Store(id='sensor-value', data=[]),
        dcc.Store(id='data-type-value', data='acceleration'),
        dcc.Store(id='summary-table-store', data=None),
        
        # 주기적 데이터 새로고침을 위한 Interval 컴포넌트 추가
        dcc.Interval(
            id='interval-component',
            interval=2*1000,  # 2초마다 새로고침
            n_intervals=0
        ),

        # 좌측 패널 (선택 + 정보)
        html.Div([
            get_sidebar_content(),
        ], id='sidebar', style={'width': '20%', 'minWidth': '180px', 'maxWidth': '260px', 'transition': 'width 0.3s', 'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '8px', 'height': '100vh', 'overflowY': 'auto', 'position': 'fixed', 'left': 0, 'top': 0, 'zIndex': 10}),

        # 메인 콘텐츠 (그래프 + 슬라이더)
        html.Div([
            html.Div([
                html.Div([
                    dcc.Slider(
                        id='graph-height-slider',
                        min=200, max=800, step=10, value=400,
                        marks={i: f"{i}px" for i in range(200, 801, 200)},
                        tooltip={"placement": "bottom", "always_visible": False},
                        updatemode='drag'
                    )
                ], style={'marginBottom': '10px'}),
            ], style={'width': '100%', 'marginLeft': '0', 'marginTop': '20px'}),
            dcc.Graph(id='imu-graph', style={'width': '100%', 'height': 400, 'transition': 'height 0.3s'}),
        ], id='main-content', style={'marginLeft': '20%', 'padding': '20px', 'transition': 'margin-left 0.3s'}),

        # 플로팅 데이터 요약 패널
        html.Div([
            html.Button("▼", id="summary-toggle", style={'position': 'absolute', 'top': 5, 'right': 5, 'background': 'none', 'border': 'none', 'cursor': 'pointer', 'fontSize': '16px'}),
            html.Div(id='summary-table', style={'fontSize': '11px', 'maxHeight': '320px', 'overflowY': 'auto', 'paddingTop': '25px'})
        ], id='summary-panel', style={'position': 'fixed', 'right': 30, 'bottom': 30, 'width': '260px', 'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '8px', 'border': '1px solid #e9ecef', 'zIndex': 20, 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}),

        # 로딩 상태
        dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="loading-output")
        )
    ], style={'padding': '0', 'fontFamily': 'Arial, sans-serif', 'height': '100vh', 'overflow': 'hidden', 'backgroundColor': '#f4f6fa'})

app.layout = html.Div([
    dcc.Store(id='login-status', data=False),
    html.Div(id='page-content')
])

# 페이지 콘텐츠를 동적으로 변경하는 콜백
@app.callback(
    Output('page-content', 'children'),
    Input('login-status', 'data')
)
def display_page(login_status):
    if login_status:
        return get_main_layout()
    else:
        return get_login_layout()

# 로그인 처리 콜백
@app.callback(
    Output('login-status', 'data'),
    Output('login-error', 'children'),
    Input('login-button', 'n_clicks'),
    State('password-input', 'value'),
    prevent_initial_call=True
)
def handle_login(login_clicks, password):
    if password == PASSWORD:
        return True, ""
    else:
        return False, "비밀번호가 올바르지 않습니다."

# 로그아웃 처리 콜백
@app.callback(
    Output('login-status', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(logout_clicks):
    return False

# 사이드바 동적 렌더링 콜백
@app.callback(
    Output('sidebar', 'style'),
    Output('sidebar', 'children'),
    Output('main-content', 'style'),
    Output('sidebar-collapsed', 'data'),
    Input('sidebar-toggle', 'n_clicks'),
    State('sidebar-collapsed', 'data'),
    State('experiment-value', 'data'),
    State('test-value', 'data'),
    State('sensor-value', 'data'),
    State('data-type-value', 'data'),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, collapsed, experiment_value, test_value, sensor_value, data_type_value):
    collapsed = not collapsed if n_clicks else collapsed
    if collapsed:
        sidebar_style = {
            'width': '32px', 'minWidth': '32px', 'maxWidth': '32px',
            'backgroundColor': '#f8f9fa', 'padding': '0',
            'borderRadius': '8px', 'height': '100vh', 'position': 'fixed',
            'left': 0, 'top': 0, 'zIndex': 10, 'overflow': 'hidden', 'display': 'flex', 'alignItems': 'flex-start', 'justifyContent': 'center'
        }
        sidebar_content = html.Button("≡", id="sidebar-toggle", style={'margin': '8px 0 0 0', 'fontSize': '18px', 'background': 'none', 'border': 'none', 'cursor': 'pointer'})
        main_style = {'marginLeft': '32px', 'padding': '20px', 'transition': 'margin-left 0.3s'}
    else:
        sidebar_style = {'width': '20%', 'minWidth': '180px', 'maxWidth': '260px', 'transition': 'width 0.3s', 'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '8px', 'height': '100vh', 'overflowY': 'auto', 'position': 'fixed', 'left': 0, 'top': 0, 'zIndex': 10}
        sidebar_content = get_sidebar_content(experiment_value, test_value, sensor_value, data_type_value)
        main_style = {'marginLeft': '20%', 'padding': '20px', 'transition': 'margin-left 0.3s'}
    return sidebar_style, sidebar_content, main_style, collapsed

# 선택값 변경 시 Store에 저장하는 콜백들 추가
@app.callback(
    Output('experiment-value', 'data'),
    Input('experiment-dropdown', 'value')
)
def store_experiment_value(value):
    return value

@app.callback(
    Output('test-value', 'data'),
    Input('test-dropdown', 'value')
)
def store_test_value(value):
    return value

@app.callback(
    Output('sensor-value', 'data'),
    Input('sensor-checklist', 'value')
)
def store_sensor_value(value):
    return value

@app.callback(
    Output('data-type-value', 'data'),
    Input('data-type-radio', 'value')
)
def store_data_type_value(value):
    return value

# 요약 패널 동적 렌더링 콜백
@app.callback(
    Output('summary-panel', 'style'),
    Output('summary-panel', 'children'),
    Output('summary-collapsed', 'data'),
    Input('summary-toggle', 'n_clicks'),
    State('summary-collapsed', 'data'),
    State('summary-table-store', 'data'),
    prevent_initial_call=True
)
def toggle_summary(n_clicks, collapsed, summary_table_data):
    collapsed = not collapsed if n_clicks else collapsed
    if collapsed:
        style = {
            'position': 'fixed', 'right': 30, 'bottom': 30,
            'width': '40px', 'height': '40px', 'backgroundColor': '#f8f9fa',
            'borderRadius': '20px', 'border': '1px solid #e9ecef', 'zIndex': 20,
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'
        }
        children = html.Button("▲", id="summary-toggle", style={'fontSize': '18px', 'background': 'none', 'border': 'none', 'cursor': 'pointer'})
    else:
        style = {'position': 'fixed', 'right': 30, 'bottom': 30, 'width': '260px', 'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '8px', 'border': '1px solid #e9ecef', 'zIndex': 20, 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'}
        children = html.Div([
            html.Button("▼", id="summary-toggle", style={'position': 'absolute', 'top': 5, 'right': 5, 'background': 'none', 'border': 'none', 'cursor': 'pointer', 'fontSize': '16px'}),
            html.Div(id='summary-table', children=summary_table_data, style={'fontSize': '11px', 'maxHeight': '320px', 'overflowY': 'auto', 'paddingTop': '25px'})
        ])
    return style, children, collapsed

# 그래프 높이 조절 콜백은 기존과 동일하게 유지
@app.callback(
    Output('imu-graph', 'style'),
    Input('graph-height-slider', 'value')
)
def update_graph_height(height):
    return {'width': '100%', 'height': f'{height}px', 'transition': 'height 0.3s'}

# 콜백: 실험 드롭다운 주기적 업데이트
@app.callback(
    Output('experiment-dropdown', 'options'),
    Input('interval-component', 'n_intervals')
)
def update_experiment_options(n_intervals):
    return utils.get_experiment_options()

# 콜백: 실험 선택 시 테스트 목록 업데이트
@app.callback(
    Output('test-dropdown', 'options'),
    Output('test-dropdown', 'value'),
    Input('experiment-dropdown', 'value')
)
def update_test_options(experiment_id):
    if experiment_id is None:
        return [], None
    test_options = utils.get_test_options(experiment_id)
    return test_options, None

# 콜백: 테스트 선택 시 센서 목록 업데이트
@app.callback(
    Output('sensor-checklist', 'options'),
    Output('sensor-checklist', 'value'),
    Input('test-dropdown', 'value')
)
def update_sensor_options(test_id):
    if test_id is None:
        return [], []
    sensor_options = utils.get_sensor_options(test_id)
    return sensor_options, []

# 콜백: 정보 패널 업데이트 (선택 패널에 통합)
@app.callback(
    Output('info-panel', 'children'),
    Input('experiment-dropdown', 'value'),
    Input('test-dropdown', 'value')
)
def update_info_panel(experiment_id, test_id):
    if experiment_id is None and test_id is None:
        return html.P("실험과 테스트를 선택하여 데이터를 확인하세요.")
    info_parts = []
    if experiment_id:
        experiments = utils.get_experiment_data()
        experiment = next((exp for exp in experiments if exp['id'] == experiment_id), None)
        if experiment:
            info_parts.append(html.P(f"📁 프로젝트: {experiment.get('project', 'Unknown')}"))
            info_parts.append(html.P(f"📅 실험 날짜: {experiment['date']}"))
            info_parts.append(html.P(f"🎯 시나리오: {experiment['scenario']}"))
            if experiment.get('description'):
                info_parts.append(html.P(f"📝 설명: {experiment['description']}"))
    if test_id:
        test_details = db.get_test_details(test_id)
        if test_details:
            info_parts.append(html.P(f"🧪 테스트: {test_details.get('test_id', test_details['test_name'])}"))
            info_parts.append(html.P(f"👤 피험자: {test_details.get('subject', 'Unknown')}"))
            info_parts.append(html.P(f"📊 센서 개수: {test_details['imu_count']}개"))
            if test_details.get('duration_sec'):
                info_parts.append(html.P(f"⏱️ 지속시간: {test_details['duration_sec']:.1f}초"))
    return html.Div(info_parts)

# 콜백: 데이터 로드 및 그래프/요약 업데이트
@app.callback(
    Output('imu-graph', 'figure'),
    Output('summary-table', 'children'),
    Output('summary-table-store', 'data'),
    Input('load-button', 'n_clicks'),
    State('test-dropdown', 'value'),
    State('sensor-checklist', 'value'),
    State('data-type-radio', 'value'),
    prevent_initial_call=True
)
def load_and_display_data(n_clicks, test_id, selected_sensors, data_type):
    if not test_id or not selected_sensors:
        empty_fig = {
            'data': [],
            'layout': {
                'title': '데이터를 선택하고 로드 버튼을 클릭하세요',
                'xaxis': {'title': '시간 (s)'},
                'yaxis': {'title': '값'},
                'annotations': [{
                    'text': '실험, 테스트, 센서를 선택한 후 데이터 로드 버튼을 클릭하세요',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 16}
                }]
            }
        }
        empty_msg = html.P("데이터를 선택하고 로드 버튼을 클릭하세요.")
        return empty_fig, empty_msg, empty_msg
    try:
        sensors = utils.get_sensor_data(test_id)
        selected_sensor_paths = []
        for sensor in sensors:
            if sensor['id'] in selected_sensors:
                selected_sensor_paths.append(sensor['file_path'])
        sensor_data = utils.load_multiple_sensor_data(selected_sensor_paths)
        if not sensor_data:
            fail_fig = {
                'data': [],
                'layout': {
                    'title': '데이터 로드 실패',
                    'annotations': [{
                        'text': '선택된 센서 데이터를 로드할 수 없습니다.',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'size': 16}
                    }]
                }
            }
            fail_msg = html.P("데이터 로드에 실패했습니다.")
            return fail_fig, fail_msg, fail_msg
        figure = utils.create_comparison_figure(sensor_data, data_type)
        summary_cards = []
        for sensor_id, df in sensor_data.items():
            summary = utils.get_data_summary(df)
            if summary:
                summary_cards.append(html.Div([
                    html.H4(f"센서 {sensor_id}", style={'margin': '0 0 6px 0', 'fontSize': '12px', 'color': '#2c3e50'}),
                    html.Div([
                        html.Div([
                            html.Span("샘플: ", style={'fontWeight': 'bold', 'fontSize': '10px'}),
                            html.Span(f"{summary['total_samples']:,}", style={'fontSize': '10px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span("시간: ", style={'fontWeight': 'bold', 'fontSize': '10px'}),
                            html.Span(f"{summary['duration_seconds']}초", style={'fontSize': '10px'})
                        ], style={'marginBottom': '3px'}),
                        html.Div([
                            html.Span("레이트: ", style={'fontWeight': 'bold', 'fontSize': '10px'}),
                            html.Span(f"{summary['sampling_rate']} Hz", style={'fontSize': '10px'})
                        ])
                    ], style={'fontSize': '10px'})
                ], style={
                    'border': '1px solid #ddd', 
                    'borderRadius': '4px', 
                    'padding': '8px', 
                    'backgroundColor': 'white',
                    'marginBottom': '8px',
                    'width': 'calc(100% - 18px)'
                }))
        summary_div = html.Div(summary_cards, style={'display': 'block'})
        return figure, summary_div, summary_div
    except Exception as e:
        print(f"데이터 로드 중 오류: {e}")
        error_fig = {
            'data': [],
            'layout': {
                'title': '오류 발생',
                'annotations': [{
                    'text': f'데이터 로드 중 오류가 발생했습니다: {str(e)}',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 16}
                }]
            }
        }
        error_msg = html.P(f"오류가 발생했습니다: {str(e)}")
        return error_fig, error_msg, error_msg

@app.callback(
    Output('refresh-status', 'children'),
    Input('refresh-db-button', 'n_clicks'),
    prevent_initial_call=True
)
def refresh_db(n_clicks):
    try:
        db.scan_and_index_data()
        return '✅ DB가 성공적으로 새로고침되었습니다.'
    except Exception as e:
        return f'❌ DB 새로고침 실패: {e}'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
