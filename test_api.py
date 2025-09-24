#!/usr/bin/env python3
"""
API 테스트 스크립트
Mobis Dashboard API의 기능을 테스트합니다.
"""

import requests
import json
import sys
from typing import Dict, List

class APITester:
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """API 상태 확인"""
        print("🔍 Testing API health...")
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API is running: {data['message']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_search_all(self) -> List[Dict]:
        """모든 테스트 검색"""
        print("\n🔍 Testing search all tests...")
        try:
            response = self.session.get(f"{self.base_url}/api/search/tests")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} tests")
                for test in data['data']:
                    print(f"   - Test {test['id']}: {test.get('test_id', test['test_name'])} ({test.get('subject', 'Unknown')}) - {test.get('project', 'Unknown')} - {test['scenario']}")
                return data['data']
            else:
                print(f"❌ Search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def test_search_by_subject(self, subject: str) -> List[Dict]:
        """주제별 검색"""
        print(f"\n🔍 Testing search by subject: '{subject}'...")
        try:
            response = self.session.get(f"{self.base_url}/api/search/tests", 
                                      params={'subject': subject})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} tests for subject '{subject}'")
                for test in data['data']:
                    print(f"   - Test {test['id']}: {test.get('test_id', test['test_name'])} ({test.get('subject', 'Unknown')})")
                return data['data']
            else:
                print(f"❌ Subject search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Subject search error: {e}")
            return []
    
    def test_search_by_sensor(self, sensor_id: str) -> List[Dict]:
        """센서 ID별 검색"""
        print(f"\n🔍 Testing search by sensor_id: '{sensor_id}'...")
        try:
            response = self.session.get(f"{self.base_url}/api/search/tests", 
                                      params={'sensor_id': sensor_id})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} tests with sensor '{sensor_id}'")
                for test in data['data']:
                    print(f"   - Test {test['id']}: {test.get('test_id', test['test_name'])} ({test.get('subject', 'Unknown')})")
                return data['data']
            else:
                print(f"❌ Sensor search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Sensor search error: {e}")
            return []
    
    def test_search_by_scenario(self, scenario: str) -> List[Dict]:
        """시나리오별 검색"""
        print(f"\n🔍 Testing search by scenario: '{scenario}'...")
        try:
            response = self.session.get(f"{self.base_url}/api/search/tests", 
                                      params={'scenario': scenario})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} tests for scenario '{scenario}'")
                for test in data['data']:
                    print(f"   - Test {test['id']}: {test.get('test_id', test['test_name'])} ({test.get('subject', 'Unknown')})")
                return data['data']
            else:
                print(f"❌ Scenario search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Scenario search error: {e}")
            return []
    
    def test_search_combined(self, **kwargs) -> List[Dict]:
        """복합 검색"""
        print(f"\n🔍 Testing combined search: {kwargs}...")
        try:
            response = self.session.get(f"{self.base_url}/api/search/tests", 
                                      params=kwargs)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} tests for combined search")
                for test in data['data']:
                    print(f"   - Test {test['id']}: {test.get('test_id', test['test_name'])} ({test.get('subject', 'Unknown')}) - {test.get('project', 'Unknown')} - {test['scenario']}")
                return data['data']
            else:
                print(f"❌ Combined search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Combined search error: {e}")
            return []
    
    def test_get_test_paths(self, test_id: int) -> Dict:
        """테스트 파일 경로 조회"""
        print(f"\n🔍 Testing get test paths for test_id: {test_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/tests/{test_id}/paths")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved paths for test {test_id}")
                print(f"   - Test: {data['data'].get('test_id', data['data']['test_name'])}")
                print(f"   - Subject: {data['data'].get('subject', 'Unknown')}")
                print(f"   - Project: {data['data'].get('project', 'Unknown')}")
                print(f"   - Duration: {data['data'].get('duration_sec', 0):.1f}초")
                print(f"   - Experiment path: {data['data']['experiment_path']}")
                print(f"   - Metadata path: {data['data']['metadata_path']}")
                print(f"   - Sensor files: {len(data['data']['sensor_files'])}")
                for sensor in data['data']['sensor_files']:
                    print(f"     * {sensor['sensor_id']} ({sensor.get('sensor_type', 'unknown')} - {sensor['position']}, {sensor.get('sample_rate_hz', 0):.1f}Hz): {sensor['file_path']}")
                return data['data']
            elif response.status_code == 404:
                print(f"❌ Test {test_id} not found")
                return {}
            else:
                print(f"❌ Get paths failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Get paths error: {e}")
            return {}
    
    def test_get_test_sensors(self, test_id: int) -> List[Dict]:
        """테스트 센서 정보 조회"""
        print(f"\n🔍 Testing get test sensors for test_id: {test_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/tests/{test_id}/sensors")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {data['count']} sensors for test {test_id}")
                for sensor in data['data']:
                    print(f"   - {sensor['sensor_id']} ({sensor.get('sensor_type', 'unknown')} - {sensor['position']}, {sensor.get('sample_rate_hz', 0):.1f}Hz): {sensor['file_name']}")
                return data['data']
            elif response.status_code == 404:
                print(f"❌ Test {test_id} not found")
                return []
            else:
                print(f"❌ Get sensors failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Get sensors error: {e}")
            return []
    
    def run_full_test(self):
        """전체 테스트 실행"""
        print("🚀 Starting Mobis Dashboard API Test")
        print("=" * 50)
        
        # 1. Health check
        if not self.test_health():
            print("❌ API is not running. Please start the server first.")
            return False
        
        # 2. Search all tests
        all_tests = self.test_search_all()
        if not all_tests:
            print("❌ No tests found. Please check your data.")
            return False
        
        # 3. Test individual search criteria
        if all_tests:
            first_test = all_tests[0]
            subject = first_test.get('subject', '')
            scenario = first_test.get('scenario', '')
            
            if subject:
                self.test_search_by_subject(subject)
            
            if scenario:
                self.test_search_by_scenario(scenario)
            
            # Test sensor search
            self.test_search_by_sensor('imu_console_001')
            
            # Test combined search
            if subject and scenario:
                self.test_search_combined(subject=subject, scenario=scenario)
        
        # 4. Test path retrieval
        if all_tests:
            first_test_id = all_tests[0]['id']
            self.test_get_test_paths(first_test_id)
            self.test_get_test_sensors(first_test_id)
        
        print("\n" + "=" * 50)
        print("✅ API test completed!")
        return True

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8050"
    
    print(f"Testing API at: {base_url}")
    
    tester = APITester(base_url)
    success = tester.run_full_test()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
