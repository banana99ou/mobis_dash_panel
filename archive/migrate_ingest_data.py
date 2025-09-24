#!/usr/bin/env python3
"""
Ingest Data Migration Script: Convert ingest folder to new naming convention
Migrates data from ingest folder to standardized format following FILENAME_CONVENTION.md
"""

import os
import json
import shutil
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

class IngestDataMigrator:
    def __init__(self, ingest_path: str = "data/ingest", target_path: str = "data/motion_sickness", backup_path: str = "data_backup"):
        self.ingest_path = Path(ingest_path)
        self.target_path = Path(target_path)
        self.backup_path = Path(backup_path)
        self.migration_log = []
        
        # File types to exclude
        self.exclude_extensions = {'.avi', '.mp4', '.mov', '.zip', '.rar', '.7z'}
        
    def log(self, message: str):
        """Log migration actions"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def create_backup(self):
        """Create backup of ingest folder"""
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        
        self.log(f"Creating backup at {self.backup_path}")
        shutil.copytree(self.ingest_path, self.backup_path / "ingest")
        self.log("Backup created successfully")
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on extension"""
        return file_path.suffix.lower() in self.exclude_extensions
    
    def parse_legacy_directory_name(self, dir_name: str) -> Dict[str, Any]:
        """Parse legacy directory name: 0811 Test01 sub02 이서윤 SLC"""
        # Extract date (0811)
        date_match = re.match(r'(\d{4})', dir_name)
        date = date_match.group(1) if date_match else None
        
        # Extract test number (Test01)
        test_match = re.search(r'Test(\d+)', dir_name)
        test_num = int(test_match.group(1)) if test_match else 1
        
        # Extract subject number (sub02)
        subject_num_match = re.search(r'sub(\d+)', dir_name)
        subject_num = int(subject_num_match.group(1)) if subject_num_match else 1
        
        # Extract subject name (이서윤)
        subject_match = re.search(r'sub\d+\s+([^S]+?)\s+S', dir_name)
        subject = subject_match.group(1).strip() if subject_match else "Unknown"
        
        # Extract scenario (SLC, S&G, LW)
        scenario_match = re.search(r'(SLC|S&G|LW)', dir_name)
        scenario = scenario_match.group(1) if scenario_match else "unknown"
        
        return {
            'date': date,
            'test_number': test_num,
            'subject_number': subject_num,
            'subject': subject,
            'scenario': scenario
        }
    
    def parse_recording_directory_name(self, dir_name: str) -> Dict[str, Any]:
        """Parse recording directory name: recording_20250804_113600_ND"""
        # Extract date from timestamp (20250804)
        date_match = re.search(r'(\d{8})', dir_name)
        date = date_match.group(1) if date_match else None
        
        # Extract time (113600)
        time_match = re.search(r'(\d{6})', dir_name)
        time = time_match.group(1) if time_match else None
        
        # Extract identifier (ND)
        id_match = re.search(r'_([A-Z0-9]+)$', dir_name)
        identifier = id_match.group(1) if id_match else "Unknown"
        
        return {
            'date': date,
            'time': time,
            'identifier': identifier,
            'test_number': 1,
            'subject': identifier,
            'scenario': 'recording'
        }
    
    def map_sensor_filename(self, filename: str) -> Dict[str, str]:
        """Map sensor filename to new naming convention"""
        filename_lower = filename.lower()
        
        # Map sensor types and positions
        if 'centc' in filename_lower:
            return {
                'sensor_type': 'imu',
                'position': 'console',
                'description': 'Center console IMU'
            }
        elif 'headr' in filename_lower:
            return {
                'sensor_type': 'imu', 
                'position': 'headrest',
                'description': 'Headrest IMU'
            }
        elif 'realsense' in filename_lower:
            return {
                'sensor_type': 'imu',
                'position': 'realsense',
                'description': 'RealSense depth camera IMU'
            }
        else:
            # Default mapping for unknown sensors
            return {
                'sensor_type': 'imu',
                'position': 'unknown',
                'description': f'Unknown sensor: {filename}'
            }
    
    def calculate_file_metrics(self, csv_file_path: Path) -> Tuple[float, float, int]:
        """Calculate duration, sample rate, and data points from CSV file"""
        try:
            # Read first few rows to get sample rate
            df_sample = pd.read_csv(csv_file_path, nrows=100)
            if len(df_sample) < 2:
                return 0.0, 0.0, 0
            
            # Calculate sample rate from time differences
            time_diffs = df_sample['t_sec'].diff().dropna()
            avg_sample_rate = 1.0 / time_diffs.mean() if time_diffs.mean() > 0 else 0.0
            
            # Read full file to get duration and data points
            df_full = pd.read_csv(csv_file_path)
            duration = df_full['t_sec'].iloc[-1] - df_full['t_sec'].iloc[0] if len(df_full) > 1 else 0.0
            data_points = len(df_full)
            
            return duration, avg_sample_rate, data_points
        except Exception as e:
            self.log(f"Error calculating metrics for {csv_file_path}: {e}")
            return 0.0, 0.0, 0
    
    def generate_new_structure_info(self, parsed_info: Dict, is_recording: bool = False) -> Dict[str, Any]:
        """Generate new structure information"""
        if is_recording:
            # For recording format
            if parsed_info['date']:
                formatted_date = f"{parsed_info['date'][:4]}-{parsed_info['date'][4:6]}-{parsed_info['date'][6:]}"
            else:
                formatted_date = "2024-08-04"  # Default fallback
            
            scenario = "recording"
            test_id = f"test_{parsed_info['test_number']:03d}_{parsed_info['identifier']}"
        else:
            # For legacy format
            if parsed_info['date']:
                formatted_date = f"2024-{parsed_info['date'][:2]}-{parsed_info['date'][2:]}"
            else:
                formatted_date = "2024-08-11"  # Default fallback
            
            # Convert scenario to lowercase with underscores
            scenario_map = {
                'SLC': 'single_lane_change',
                'S&G': 'stop_and_go', 
                'LW': 'lane_weaving'
            }
            scenario = scenario_map.get(parsed_info['scenario'], 'unknown')
            test_id = f"test_{parsed_info['test_number']:03d}_{parsed_info['subject']}"
        
        return {
            'date': formatted_date,
            'scenario': scenario,
            'test_id': test_id,
            'test_number': parsed_info['test_number'],
            'subject': parsed_info['subject']
        }
    
    def create_metadata(self, new_structure_info: Dict, csv_files: List[Path], parsed_info: Dict) -> Dict:
        """Create metadata.json for new structure"""
        # Calculate total duration from all CSV files
        total_duration = 0.0
        sensors = []
        
        for i, csv_file in enumerate(csv_files):
            duration, sample_rate, data_points = self.calculate_file_metrics(csv_file)
            total_duration = max(total_duration, duration)
            
            # Map sensor filename to new convention
            sensor_map = self.map_sensor_filename(csv_file.name)
            new_filename = f"{sensor_map['sensor_type']}_{sensor_map['position']}_{i+1:03d}.csv"
            
            sensor_info = {
                "file": new_filename,
                "type": sensor_map['sensor_type'],
                "position": sensor_map['position'],
                "sequence": i + 1,
                "sample_rate_hz": round(sample_rate, 1),
                "data_points": data_points,
                "channels": ["t_sec", "ax", "ay", "az", "gx", "gy", "gz"],
                "description": sensor_map['description']
            }
            sensors.append(sensor_info)
        
        metadata = {
            "project": "motion_sickness",
            "experiment": {
                "id": f"{new_structure_info['date']}_{new_structure_info['scenario']}",
                "date": new_structure_info['date'],
                "scenario": new_structure_info['scenario'],
                "description": f"{new_structure_info['scenario']} experiment for motion sickness study"
            },
            "test": {
                "id": new_structure_info['test_id'],
                "sequence": new_structure_info['test_number'],
                "subject": new_structure_info['subject'],
                "subject_id": f"S{new_structure_info['test_number']:03d}",
                "duration_sec": round(total_duration, 1),
                "notes": f"Migrated from ingest folder"
            },
            "sensors": sensors,
            "data_quality": {
                "completeness": 1.0,
                "anomalies": 0,
                "notes": "Data migrated from ingest folder"
            },
            "migration_info": {
                "migrated_at": datetime.now().isoformat(),
                "source_format": "legacy_ingest" if not parsed_info.get('identifier') else "recording_ingest",
                "original_directory": str(csv_files[0].parent.name) if csv_files else "unknown"
            }
        }
        
        return metadata
    
    def scan_ingest_folder(self) -> List[Dict]:
        """Scan ingest folder and identify directories to migrate"""
        migration_candidates = []
        
        self.log("Scanning ingest folder...")
        
        for item in self.ingest_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if directory contains CSV files
                csv_files = [f for f in item.iterdir() 
                           if f.is_file() and f.suffix.lower() == '.csv' and not self.should_exclude_file(f)]
                
                if csv_files:
                    # Determine if this is legacy or recording format
                    if item.name.startswith('recording_'):
                        parsed_info = self.parse_recording_directory_name(item.name)
                        is_recording = True
                    else:
                        parsed_info = self.parse_legacy_directory_name(item.name)
                        is_recording = False
                    
                    migration_candidates.append({
                        'source_dir': item,
                        'csv_files': csv_files,
                        'parsed_info': parsed_info,
                        'is_recording': is_recording
                    })
                    
                    self.log(f"Found migration candidate: {item.name} ({len(csv_files)} CSV files)")
                else:
                    self.log(f"Skipping directory (no CSV files): {item.name}")
        
        return migration_candidates
    
    def generate_migration_plan(self, candidates: List[Dict]) -> List[Dict]:
        """Generate detailed migration plan"""
        migration_plan = []
        
        self.log("Generating migration plan...")
        
        for candidate in candidates:
            # Generate new structure info
            new_structure_info = self.generate_new_structure_info(
                candidate['parsed_info'], 
                candidate['is_recording']
            )
            
            # Create target paths
            target_experiment_path = self.target_path / f"{new_structure_info['date']}_{new_structure_info['scenario']}"
            target_test_path = target_experiment_path / new_structure_info['test_id']
            
            # Create metadata
            metadata = self.create_metadata(
                new_structure_info, 
                candidate['csv_files'], 
                candidate['parsed_info']
            )
            
            # Create file mappings
            file_mappings = []
            for i, csv_file in enumerate(candidate['csv_files']):
                sensor_map = self.map_sensor_filename(csv_file.name)
                new_filename = f"{sensor_map['sensor_type']}_{sensor_map['position']}_{i+1:03d}.csv"
                new_file_path = target_test_path / new_filename
                
                file_mappings.append({
                    'source_file': csv_file,
                    'target_file': new_file_path,
                    'old_name': csv_file.name,
                    'new_name': new_filename,
                    'sensor_info': sensor_map
                })
            
            migration_plan.append({
                'source_dir': candidate['source_dir'],
                'target_path': target_test_path,
                'target_experiment_path': target_experiment_path,
                'new_structure_info': new_structure_info,
                'metadata': metadata,
                'file_mappings': file_mappings,
                'is_recording': candidate['is_recording']
            })
        
        return migration_plan
    
    def execute_migration(self, migration_plan: List[Dict]):
        """Execute the migration plan"""
        self.log("Executing migration...")
        
        for plan in migration_plan:
            # Create target directory structure
            plan['target_path'].mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {plan['target_path']}")
            
            # Copy and rename CSV files
            for file_mapping in plan['file_mappings']:
                source_file = file_mapping['source_file']
                target_file = file_mapping['target_file']
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    self.log(f"Copied: {source_file.name} -> {target_file.name}")
                else:
                    self.log(f"Warning: Source file not found: {source_file}")
            
            # Write metadata.json
            metadata_file = plan['target_path'] / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(plan['metadata'], f, indent=2, ensure_ascii=False)
            self.log(f"Created metadata: {metadata_file}")
    
    def validate_migration(self, migration_plan: List[Dict]) -> bool:
        """Validate the migration was successful"""
        self.log("Validating migration...")
        
        all_valid = True
        
        for plan in migration_plan:
            target_path = plan['target_path']
            
            # Check directory exists
            if not target_path.exists():
                self.log(f"Error: Directory not created: {target_path}")
                all_valid = False
                continue
            
            # Check metadata file exists
            metadata_file = target_path / 'metadata.json'
            if not metadata_file.exists():
                self.log(f"Error: Metadata file not created: {metadata_file}")
                all_valid = False
                continue
            
            # Check all files copied
            for file_mapping in plan['file_mappings']:
                target_file = file_mapping['target_file']
                if not target_file.exists():
                    self.log(f"Error: File not copied: {target_file}")
                    all_valid = False
                else:
                    # Check file size
                    source_size = file_mapping['source_file'].stat().st_size
                    target_size = target_file.stat().st_size
                    if source_size != target_size:
                        self.log(f"Warning: File size mismatch: {target_file}")
        
        if all_valid:
            self.log("Migration validation successful!")
        else:
            self.log("Migration validation failed!")
        
        return all_valid
    
    def save_migration_log(self):
        """Save migration log to file"""
        log_file = Path("ingest_migration_log.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.migration_log))
        self.log(f"Migration log saved to: {log_file}")
    
    def run_migration(self, create_backup: bool = True, dry_run: bool = False):
        """Run the complete migration process"""
        try:
            # Step 1: Create backup
            if create_backup:
                self.create_backup()
            
            # Step 2: Scan ingest folder
            candidates = self.scan_ingest_folder()
            if not candidates:
                self.log("No data found to migrate")
                return False
            
            # Step 3: Generate migration plan
            migration_plan = self.generate_migration_plan(candidates)
            
            if dry_run:
                self.log("DRY RUN - Migration plan generated:")
                for plan in migration_plan:
                    self.log(f"  {plan['source_dir'].name} -> {plan['target_path']}")
                    for mapping in plan['file_mappings']:
                        self.log(f"    {mapping['old_name']} -> {mapping['new_name']}")
                return True
            
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
    print("Ingest Data Migration Script")
    print("=" * 50)
    print("This will migrate data from ingest folder to new naming convention")
    print("Excluding: .avi, .mp4, .mov, .zip, .rar, .7z files")
    print()
    
    # Ask for confirmation
    response = input("Continue with migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Ask for dry run
    dry_run_response = input("Perform dry run first? (Y/n): ")
    dry_run = dry_run_response.lower() != 'n'
    
    # Create migrator and run
    migrator = IngestDataMigrator()
    success = migrator.run_migration(dry_run=dry_run)
    
    if success:
        if dry_run:
            print("\n✅ Dry run completed successfully!")
            print("Review the plan above and run again without dry run to execute.")
        else:
            print("\n✅ Migration completed successfully!")
            print("Check ingest_migration_log.txt for details.")
    else:
        print("\n❌ Migration failed!")
        print("Check ingest_migration_log.txt for details.")
        print("Original data is backed up in data_backup/")

if __name__ == "__main__":
    main()
