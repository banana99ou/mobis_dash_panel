#!/usr/bin/env python3
"""
Legacy Ingest Migration Script: Migrate only legacy format data first
Migrates data from legacy format directories in ingest folder to standardized format
"""

import os
import json
import shutil
import re
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

class LegacyIngestMigrator:
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
        """Create backup of target motion_sickness folder (the important database structure)"""
        backup_target_path = self.backup_path / "motion_sickness"
        
        # Remove existing backup if it exists
        if backup_target_path.exists():
            shutil.rmtree(backup_target_path)
        
        # Create backup directory if it doesn't exist
        self.backup_path.mkdir(exist_ok=True)
        
        # Only backup if target directory exists
        if self.target_path.exists():
            self.log(f"Creating backup of existing motion_sickness folder at {backup_target_path}")
            shutil.copytree(self.target_path, backup_target_path)
            self.log("Backup created successfully")
        else:
            self.log("No existing motion_sickness folder to backup")
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on extension"""
        return file_path.suffix.lower() in self.exclude_extensions
    
    def is_legacy_format(self, dir_name: str) -> bool:
        """Check if directory is legacy format (not recording format)"""
        return not dir_name.startswith('recording_')
    
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
        
        # Extract subject name (이서윤) - handle different scenario formats
        # Try pattern with space before scenario first (S&G, SLC)
        subject_match = re.search(r'sub\d+\s+([^S]+?)\s+S[^a-zA-Z]', dir_name)
        if not subject_match:
            # Try pattern for LW (no space before scenario)
            subject_match = re.search(r'sub\d+\s+([^S]+?)(?=LW)', dir_name)
        if not subject_match:
            # Try pattern without space before scenario (S&G, SLC)
            subject_match = re.search(r'sub\d+\s+([^S]+?)(?=\s+S)', dir_name)
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
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if len(rows) < 2:
                return 0.0, 0.0, 0
            
            # Calculate sample rate from first 100 rows
            sample_rows = rows[:100]
            time_diffs = []
            for i in range(1, len(sample_rows)):
                try:
                    t1 = float(sample_rows[i-1]['t_sec'])
                    t2 = float(sample_rows[i]['t_sec'])
                    time_diffs.append(t2 - t1)
                except (ValueError, KeyError):
                    continue
            
            avg_sample_rate = 1.0 / (sum(time_diffs) / len(time_diffs)) if time_diffs else 0.0
            
            # Calculate duration from full file
            try:
                start_time = float(rows[0]['t_sec'])
                end_time = float(rows[-1]['t_sec'])
                duration = end_time - start_time
            except (ValueError, KeyError):
                duration = 0.0
            
            data_points = len(rows)
            
            return duration, avg_sample_rate, data_points
        except Exception as e:
            self.log(f"Error calculating metrics for {csv_file_path}: {e}")
            return 0.0, 0.0, 0
    
    def generate_new_structure_info(self, parsed_info: Dict) -> Dict[str, Any]:
        """Generate new structure information for legacy format"""
        # Convert date format (0811 -> 2024-08-11)
        if parsed_info['date']:
            formatted_date = f"2024-{parsed_info['date'][:2]}-{parsed_info['date'][2:]}"
        else:
            formatted_date = "2024-08-11"  # Default fallback
        
        # Convert scenario to lowercase with underscores
        scenario_map = {
            'SLC': 'single_lane_change',
            'S&G': 'stop_and_go', 
            'LW': 'long_wave'
        }
        scenario = scenario_map.get(parsed_info['scenario'], 'unknown')
        test_id = f"test_{parsed_info['test_number']:03d}_sub{parsed_info['subject_number']:02d}_{parsed_info['subject']}"
        
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
                "subject_id": f"S{parsed_info['subject_number']:03d}",
                "duration_sec": round(total_duration, 1),
                "notes": f"Migrated from legacy ingest format"
            },
            "sensors": sensors,
            "data_quality": {
                "completeness": 1.0,
                "anomalies": 0,
                "notes": "Data migrated from legacy ingest folder"
            },
            "migration_info": {
                "migrated_at": datetime.now().isoformat(),
                "source_format": "legacy_ingest",
                "original_directory": str(csv_files[0].parent.name) if csv_files else "unknown"
            }
        }
        
        return metadata
    
    def scan_legacy_directories(self) -> List[Dict]:
        """Scan ingest folder and identify legacy format directories to migrate"""
        migration_candidates = []
        
        self.log("Scanning ingest folder for legacy format directories...")
        
        for item in self.ingest_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and self.is_legacy_format(item.name):
                # Check if directory contains CSV files (directly or in resampled/ subdirectory)
                csv_files = []
                
                # Look for CSV files directly in the directory
                direct_csv_files = [f for f in item.iterdir() 
                                  if f.is_file() and f.suffix.lower() == '.csv' and not self.should_exclude_file(f)]
                csv_files.extend(direct_csv_files)
                
                # Look for CSV files in resampled/ subdirectory
                resampled_dir = item / "resampled"
                if resampled_dir.exists() and resampled_dir.is_dir():
                    resampled_csv_files = [f for f in resampled_dir.iterdir() 
                                         if f.is_file() and f.suffix.lower() == '.csv' and not self.should_exclude_file(f)]
                    csv_files.extend(resampled_csv_files)
                
                if csv_files:
                    parsed_info = self.parse_legacy_directory_name(item.name)
                    
                    migration_candidates.append({
                        'source_dir': item,
                        'csv_files': csv_files,
                        'parsed_info': parsed_info
                    })
                    
                    self.log(f"Found legacy migration candidate: {item.name} ({len(csv_files)} CSV files)")
                else:
                    self.log(f"Skipping legacy directory (no CSV files): {item.name}")
            elif item.is_dir() and not item.name.startswith('.') and not self.is_legacy_format(item.name):
                self.log(f"Skipping recording format directory (will be handled later): {item.name}")
        
        return migration_candidates
    
    def generate_migration_plan(self, candidates: List[Dict]) -> List[Dict]:
        """Generate detailed migration plan"""
        migration_plan = []
        
        self.log("Generating migration plan...")
        
        for candidate in candidates:
            # Generate new structure info
            new_structure_info = self.generate_new_structure_info(candidate['parsed_info'])
            
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
                'file_mappings': file_mappings
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
        log_file = Path("legacy_ingest_migration_log.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.migration_log))
        self.log(f"Migration log saved to: {log_file}")
    
    def run_migration(self, create_backup: bool = True, dry_run: bool = False):
        """Run the complete migration process"""
        try:
            # Step 1: Create backup
            if create_backup:
                self.create_backup()
            
            # Step 2: Scan for legacy directories
            candidates = self.scan_legacy_directories()
            if not candidates:
                self.log("No legacy format data found to migrate")
                return False
            
            # Step 3: Generate migration plan
            migration_plan = self.generate_migration_plan(candidates)
            
            if dry_run:
                self.log("DRY RUN - Legacy format migration plan:")
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
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Legacy Ingest Migration Script')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry run mode (preview only, no actual migration)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup of existing motion_sickness folder')
    parser.add_argument('--ingest-path', default='data/ingest',
                       help='Path to ingest folder (default: data/ingest)')
    parser.add_argument('--target-path', default='data/motion_sickness',
                       help='Path to target motion_sickness folder (default: data/motion_sickness)')
    parser.add_argument('--backup-path', default='data_backup',
                       help='Path to backup folder (default: data_backup)')
    
    args = parser.parse_args()
    
    print("Legacy Ingest Migration Script")
    print("=" * 50)
    print("This will migrate ONLY legacy format data from ingest folder")
    print("Recording format directories will be skipped for now")
    print("Excluding: .avi, .mp4, .mov, .zip, .rar, .7z files")
    print()
    
    if args.dry_run:
        print("Running in DRY RUN mode...")
    else:
        print("Running in EXECUTION mode...")
    
    # Create migrator and run
    migrator = LegacyIngestMigrator(
        ingest_path=args.ingest_path,
        target_path=args.target_path,
        backup_path=args.backup_path
    )
    
    success = migrator.run_migration(
        create_backup=not args.no_backup,
        dry_run=args.dry_run
    )
    
    if success:
        if args.dry_run:
            print("\n✅ Dry run completed successfully!")
            print("Review the plan above and run without --dry-run to execute.")
        else:
            print("\n✅ Legacy format migration completed successfully!")
            print("Check legacy_ingest_migration_log.txt for details.")
    else:
        print("\n❌ Migration failed!")
        print("Check legacy_ingest_migration_log.txt for details.")
        if not args.no_backup:
            print("Original motion_sickness data is backed up in data_backup/")

if __name__ == "__main__":
    main()
