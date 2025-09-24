#!/usr/bin/env python3
"""
Data Migration Script: Current to New Naming Convention
Migrates existing data structure to the new standardized format
"""

import os
import json
import shutil
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

class DataMigrator:
    def __init__(self, source_path: str = "data", backup_path: str = "data_backup"):
        self.source_path = Path(source_path)
        self.backup_path = Path(backup_path)
        self.migration_log = []
        
    def log(self, message: str):
        """Log migration actions"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def create_backup(self):
        """Create backup of current data structure"""
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        
        self.log(f"Creating backup at {self.backup_path}")
        shutil.copytree(self.source_path, self.backup_path)
        self.log("Backup created successfully")
    
    def parse_test_directory(self, test_dir_name: str) -> Dict[str, Any]:
        """Parse test directory name: 0630_test1_Single Lane Change_최지웅"""
        # Extract date (0630)
        date_match = re.match(r'(\d{4})', test_dir_name)
        date = date_match.group(1) if date_match else None
        
        # Extract test number (test1)
        test_match = re.search(r'test(\d+)', test_dir_name)
        test_num = int(test_match.group(1)) if test_match else None
        
        # Extract scenario (Single Lane Change) - everything between test number and last underscore
        scenario_match = re.search(r'test\d+_(.+?)_[^_]+$', test_dir_name)
        scenario = scenario_match.group(1) if scenario_match else None
        
        # Extract subject name (최지웅) - everything after the last underscore
        subject_match = re.search(r'_([^_]+)$', test_dir_name)
        subject = subject_match.group(1) if subject_match else None
        
        return {
            'date': date,
            'test_number': test_num,
            'scenario': scenario,
            'subject': subject
        }
    
    def translate_position(self, korean_position: str) -> str:
        """Translate Korean position to English"""
        position_map = {
            '콘솔': 'console',
            '조수석후방': 'passenger_rear',
            '대시보드': 'dashboard',
            '지붕': 'roof'
        }
        return position_map.get(korean_position, korean_position.lower())
    
    def calculate_duration_and_sample_rate(self, csv_file_path: str) -> Tuple[float, float]:
        """Calculate duration and sample rate from CSV file"""
        try:
            # Read first few rows to get sample rate
            df_sample = pd.read_csv(csv_file_path, nrows=100)
            if len(df_sample) < 2:
                return 0.0, 0.0
            
            # Calculate sample rate from time differences
            time_diffs = df_sample['t_sec'].diff().dropna()
            avg_sample_rate = 1.0 / time_diffs.mean() if time_diffs.mean() > 0 else 0.0
            
            # Read full file to get duration
            df_full = pd.read_csv(csv_file_path)
            duration = df_full['t_sec'].iloc[-1] - df_full['t_sec'].iloc[0] if len(df_full) > 1 else 0.0
            
            return duration, avg_sample_rate
        except Exception as e:
            self.log(f"Error calculating duration for {csv_file_path}: {e}")
            return 0.0, 0.0
    
    def generate_new_structure_info(self, test_info: Dict, metadata: Dict) -> Dict[str, Any]:
        """Generate new structure information"""
        # Convert date format (0630 -> 2024-06-30)
        if test_info['date']:
            formatted_date = f"2024-{test_info['date'][:2]}-{test_info['date'][2:]}"
        else:
            formatted_date = metadata.get('experiment', {}).get('date', '2024-06-30')
        
        # Convert scenario to lowercase with underscores
        scenario = test_info.get('scenario', 'single_lane_change')
        formatted_scenario = scenario.lower().replace(' ', '_')
        
        # Generate test ID
        test_num = test_info.get('test_number', 1)
        subject = test_info.get('subject', 'unknown')
        test_id = f"test_{test_num:03d}_{subject}"
        
        return {
            'date': formatted_date,
            'scenario': formatted_scenario,
            'test_id': test_id,
            'test_number': test_num,
            'subject': subject
        }
    
    def transform_metadata(self, old_metadata: Dict, new_structure_info: Dict, csv_files: List[str]) -> Dict:
        """Transform old metadata to new format"""
        new_metadata = {
            "project": "motion_sickness",
            "experiment": {
                "id": f"{new_structure_info['date']}_{new_structure_info['scenario']}",
                "date": new_structure_info['date'],
                "scenario": new_structure_info['scenario'],
                "description": f"{new_structure_info['scenario']} maneuver for motion sickness study"
            },
            "test": {
                "id": new_structure_info['test_id'],
                "sequence": new_structure_info['test_number'],
                "subject": new_structure_info['subject'],
                "subject_id": f"S{new_structure_info['test_number']:03d}",
                "duration_sec": 0.0,
                "notes": ""
            },
            "sensors": [],
            "data_quality": {
                "completeness": 1.0,
                "anomalies": 0,
                "notes": ""
            }
        }
        
        # Transform sensors and calculate duration
        total_duration = 0.0
        for i, sensor in enumerate(old_metadata.get('sensors', [])):
            # Find corresponding CSV file
            csv_file = None
            for csv_file_path in csv_files:
                if sensor['file'] in csv_file_path:
                    csv_file = csv_file_path
                    break
            
            # Calculate duration and sample rate
            duration, sample_rate = self.calculate_duration_and_sample_rate(csv_file) if csv_file else (0.0, 100.0)
            total_duration = max(total_duration, duration)
            
            new_sensor = {
                "file": f"imu_{self.translate_position(sensor['position'])}_{i+1:03d}.csv",
                "type": "imu",
                "position": self.translate_position(sensor['position']),
                "sequence": i + 1,
                "sample_rate_hz": round(sample_rate, 1),
                "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"]
            }
            new_metadata['sensors'].append(new_sensor)
        
        new_metadata['test']['duration_sec'] = round(total_duration, 1)
        return new_metadata
    
    def parse_current_structure(self) -> Dict[str, Any]:
        """Parse current directory structure and extract information"""
        structure = {}
        
        self.log("Parsing current directory structure...")
        
        for root, dirs, files in os.walk(self.source_path):
            if 'metadata.json' in files:
                # Extract information from directory path
                path_parts = Path(root).parts
                if len(path_parts) >= 3:
                    project = path_parts[-3]  # experiment_pilot
                    day = path_parts[-2]      # Day1
                    test_dir = path_parts[-1] # 0630_test1_Single Lane Change_최지웅
                    
                    # Parse test directory name
                    test_info = self.parse_test_directory(test_dir)
                    
                    # Read metadata
                    metadata_path = os.path.join(root, 'metadata.json')
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        self.log(f"Error reading metadata from {metadata_path}: {e}")
                        continue
                    
                    # Find CSV files
                    csv_files = [os.path.join(root, f) for f in files if f.endswith('.csv')]
                    
                    structure[root] = {
                        'project': project,
                        'day': day,
                        'test_info': test_info,
                        'metadata': metadata,
                        'files': files,
                        'csv_files': csv_files
                    }
                    
                    self.log(f"Parsed: {test_dir} -> {test_info}")
        
        return structure
    
    def generate_migration_plan(self, structure: Dict) -> List[Dict]:
        """Generate migration plan from parsed structure"""
        migration_plan = []
        
        self.log("Generating migration plan...")
        
        for old_path, info in structure.items():
            # Generate new structure info
            new_structure_info = self.generate_new_structure_info(info['test_info'], info['metadata'])
            
            # Create new paths
            new_project_path = self.source_path / "motion_sickness"
            new_experiment_path = new_project_path / f"{new_structure_info['date']}_{new_structure_info['scenario']}"
            new_test_path = new_experiment_path / new_structure_info['test_id']
            
            # Transform metadata
            new_metadata = self.transform_metadata(info['metadata'], new_structure_info, info['csv_files'])
            
            # Create file mappings
            file_mappings = []
            for i, sensor in enumerate(info['metadata'].get('sensors', [])):
                old_file = os.path.join(old_path, sensor['file'])
                new_filename = f"imu_{self.translate_position(sensor['position'])}_{i+1:03d}.csv"
                new_file = new_test_path / new_filename
                
                file_mappings.append({
                    'old_file': old_file,
                    'new_file': str(new_file),
                    'old_name': sensor['file'],
                    'new_name': new_filename
                })
            
            migration_plan.append({
                'old_path': old_path,
                'new_path': str(new_test_path),
                'new_structure_info': new_structure_info,
                'new_metadata': new_metadata,
                'file_mappings': file_mappings
            })
        
        return migration_plan
    
    def execute_migration(self, migration_plan: List[Dict]):
        """Execute the migration plan"""
        self.log("Executing migration...")
        
        for plan in migration_plan:
            # Create new directory structure
            new_path = Path(plan['new_path'])
            new_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {new_path}")
            
            # Copy and rename files
            for file_mapping in plan['file_mappings']:
                old_file = file_mapping['old_file']
                new_file = file_mapping['new_file']
                
                if os.path.exists(old_file):
                    shutil.copy2(old_file, new_file)
                    self.log(f"Copied: {old_file} -> {new_file}")
                else:
                    self.log(f"Warning: Source file not found: {old_file}")
            
            # Write new metadata
            metadata_file = new_path / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(plan['new_metadata'], f, indent=2, ensure_ascii=False)
            self.log(f"Created metadata: {metadata_file}")
    
    def validate_migration(self, migration_plan: List[Dict]) -> bool:
        """Validate the migration was successful"""
        self.log("Validating migration...")
        
        all_valid = True
        
        for plan in migration_plan:
            new_path = Path(plan['new_path'])
            
            # Check directory exists
            if not new_path.exists():
                self.log(f"Error: Directory not created: {new_path}")
                all_valid = False
                continue
            
            # Check metadata file exists
            metadata_file = new_path / 'metadata.json'
            if not metadata_file.exists():
                self.log(f"Error: Metadata file not created: {metadata_file}")
                all_valid = False
                continue
            
            # Check all files copied
            for file_mapping in plan['file_mappings']:
                new_file = Path(file_mapping['new_file'])
                if not new_file.exists():
                    self.log(f"Error: File not copied: {new_file}")
                    all_valid = False
                else:
                    # Check file size
                    old_size = os.path.getsize(file_mapping['old_file'])
                    new_size = os.path.getsize(new_file)
                    if old_size != new_size:
                        self.log(f"Warning: File size mismatch: {new_file}")
        
        if all_valid:
            self.log("Migration validation successful!")
        else:
            self.log("Migration validation failed!")
        
        return all_valid
    
    def save_migration_log(self):
        """Save migration log to file"""
        log_file = Path("migration_log.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.migration_log))
        self.log(f"Migration log saved to: {log_file}")
    
    def run_migration(self, create_backup: bool = True):
        """Run the complete migration process"""
        try:
            # Step 1: Create backup
            if create_backup:
                self.create_backup()
            
            # Step 2: Parse current structure
            structure = self.parse_current_structure()
            if not structure:
                self.log("No data found to migrate")
                return False
            
            # Step 3: Generate migration plan
            migration_plan = self.generate_migration_plan(structure)
            
            # Step 4: Execute migration
            self.execute_migration(migration_plan)
            
            # Step 5: Validate migration
            success = self.validate_migration(migration_plan)
            
            # Step 6: Save log
            self.save_migration_log()
            
            return success
            
        except Exception as e:
            self.log(f"Migration failed with error: {e}")
            return False

def main():
    """Main function to run migration"""
    print("Data Migration Script: Current to New Naming Convention")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("This will migrate your data structure. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Create migrator and run
    migrator = DataMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Check migration_log.txt for details.")
    else:
        print("\n❌ Migration failed!")
        print("Check migration_log.txt for details.")
        print("Original data is backed up in data_backup/")

if __name__ == "__main__":
    main()
