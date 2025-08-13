#!/usr/bin/env python3
"""
Export cleanup job for Surveillance AI backend.
Removes old export files and ZIP downloads to prevent disk space issues.
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger("cleanup")

class ExportCleaner:
    """Handles cleanup of old export files and downloads."""
    
    def __init__(self, results_dir: str = "./results", max_age_hours: int = 24):
        """
        Initialize cleanup with configurable settings.
        
        Args:
            results_dir: Base results directory
            max_age_hours: Files older than this are deleted (default: 24 hours)
        """
        self.results_dir = results_dir
        self.downloads_dir = os.path.join(results_dir, "downloads")
        self.previews_dir = os.path.join(results_dir, "previews")
        self.max_age_hours = max_age_hours
        self.max_age_seconds = max_age_hours * 3600
        
        # Ensure directories exist
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.previews_dir, exist_ok=True)
    
    def get_old_files(self, directory: str, extensions: List[str] = None) -> List[str]:
        """
        Get list of files older than max_age_hours.
        
        Args:
            directory: Directory to scan
            extensions: List of file extensions to include (e.g., ['.zip', '.mp4'])
        
        Returns:
            List of file paths to delete
        """
        if not os.path.exists(directory):
            return []
        
        old_files = []
        current_time = time.time()
        cutoff_time = current_time - self.max_age_seconds
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            # Filter by extensions if specified
            if extensions:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in extensions:
                    continue
            
            # Check file age
            try:
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    old_files.append(file_path)
            except OSError as e:
                logger.warning(f"Could not check file {file_path}: {e}")
        
        return old_files
    
    def cleanup_downloads(self) -> int:
        """Clean up old ZIP downloads."""
        logger.info(f"Cleaning up downloads older than {self.max_age_hours} hours...")
        
        old_files = self.get_old_files(self.downloads_dir, ['.zip'])
        deleted_count = 0
        
        for file_path in old_files:
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"Deleted {file_path} ({file_size} bytes)")
            except OSError as e:
                logger.error(f"Could not delete {file_path}: {e}")
        
        logger.info(f"Cleanup complete: {deleted_count} download files deleted")
        return deleted_count
    
    def cleanup_previews(self) -> int:
        """Clean up old preview clips."""
        logger.info(f"Cleaning up previews older than {self.max_age_hours} hours...")
        
        old_files = self.get_old_files(self.previews_dir, ['.mp4', '.avi', '.mov'])
        deleted_count = 0
        
        for file_path in old_files:
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"Deleted {file_path} ({file_size} bytes)")
            except OSError as e:
                logger.error(f"Could not delete {file_path}: {e}")
        
        logger.info(f"Cleanup complete: {deleted_count} preview files deleted")
        return deleted_count
    
    def cleanup_all(self) -> dict:
        """Run complete cleanup and return summary."""
        logger.info("Starting export cleanup job...")
        start_time = datetime.now()
        
        downloads_deleted = self.cleanup_downloads()
        previews_deleted = self.cleanup_previews()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "downloads_deleted": downloads_deleted,
            "previews_deleted": previews_deleted,
            "total_deleted": downloads_deleted + previews_deleted
        }
        
        logger.info(f"Cleanup job completed: {summary['total_deleted']} files deleted in {duration:.2f}s")
        return summary

def main():
    """Main cleanup function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old export files")
    parser.add_argument("--results-dir", default="./results", help="Results directory path")
    parser.add_argument("--max-age-hours", type=int, default=24, help="Maximum file age in hours")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    
    args = parser.parse_args()
    
    cleaner = ExportCleaner(
        results_dir=args.results_dir,
        max_age_hours=args.max_age_hours
    )
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be deleted")
        
        old_downloads = cleaner.get_old_files(cleaner.downloads_dir, ['.zip'])
        old_previews = cleaner.get_old_files(cleaner.previews_dir, ['.mp4', '.avi', '.mov'])
        
        logger.info(f"Would delete {len(old_downloads)} download files:")
        for file_path in old_downloads:
            logger.info(f"  - {file_path}")
        
        logger.info(f"Would delete {len(old_previews)} preview files:")
        for file_path in old_previews:
            logger.info(f"  - {file_path}")
        
        logger.info(f"Total: {len(old_downloads) + len(old_previews)} files would be deleted")
    else:
        summary = cleaner.cleanup_all()
        logger.info(f"Cleanup summary: {summary}")

if __name__ == "__main__":
    main()
