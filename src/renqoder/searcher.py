"""
Video file searcher module
Provides fast video file search using Everything or OS fallback
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional


class VideoSearcher:
    """Video file searcher with Everything integration"""
    
    # Common video extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
        '.webm', '.m4v', '.ts', '.m2ts', '.vob', '.3gp'
    }
    
    def __init__(self):
        self.everything_available = self.check_everything_available()
    
    def check_everything_available(self) -> bool:
        """Check if es.exe is available"""
        try:
            # Check if es.exe is in PATH
            creationflags = 0x08000000 if os.name == 'nt' else 0
            result = subprocess.run(
                ['es.exe', '-n', '0'],  # Just check if it runs
                capture_output=True,
                timeout=2,
                creationflags=creationflags
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try common installation paths
            common_paths = [
                r'C:\Program Files\Everything\es.exe',
                r'C:\Program Files (x86)\Everything\es.exe',
                Path.home() / 'scoop' / 'apps' / 'everything' / 'current' / 'es.exe',
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    return True
            
            return False
        except Exception:
            return False
    
    def get_everything_status(self) -> Dict[str, any]:
        """Get Everything detection status info (similar to HardwareDetector)"""
        if self.everything_available:
            return {
                'installed': True,
                'status_text': '🔍 Everything 감지됨 (초고속 검색)',
                'color': '#76b900'  # Green
            }
        else:
            return {
                'installed': False,
                'status_text': '⚠️ Everything 미설치 (OS 검색 사용)',
                'color': '#FFAA00'  # Orange warning
            }
    
    def get_drives(self) -> List[str]:
        """Get available drives on Windows"""
        if os.name != 'nt':
            return ['/']
        
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f'{letter}:\\'
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    
    def search(self, drive: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Main search entry point
        
        Args:
            drive: Drive path (e.g., 'C:\\')
            filters: Dict with optional keys:
                - extension: str (e.g., 'mp4', 'mkv') or None for all
                - min_size: int (bytes)
                - max_size: int (bytes)
        
        Returns:
            List of dicts with keys: name, path, size, extension, modified
        """
        if filters is None:
            filters = {}
        
        if self.everything_available:
            return self.search_everything(drive, filters)
        else:
            return self.search_os(drive, filters)
    
    def search_everything(self, drive: str, filters: Dict) -> List[Dict]:
        """Search using Everything (es.exe)"""
        try:
            # Build Everything command with options
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            # Build extension filter
            ext_filter = filters.get('extension', '')
            if ext_filter:
                # Single extension
                ext_query = f'ext:{ext_filter}'
            else:
                # All video extensions
                ext_list = ';'.join(e.lstrip('.') for e in self.VIDEO_EXTENSIONS)
                ext_query = f'ext:{ext_list}'
            
            # Build size filters
            size_parts = []
            min_size = filters.get('min_size')
            if min_size:
                size_parts.append(f'size:>={min_size}')
            
            max_size = filters.get('max_size')
            if max_size:
                size_parts.append(f'size:<={max_size}')
            
            # Combine query parts
            query_parts = [ext_query]
            if size_parts:
                query_parts.extend(size_parts)
            
            query = ' '.join(query_parts)
            
            # Build command with -path option for drive filtering
            cmd = ['es.exe']
            
            # Add path filter if drive is specified
            if drive:
                cmd.extend(['-path', drive])
            
            # Add search query
            cmd.append(query)
            
            # Add column options for output (no CSV export, use stdout)
            cmd.extend([
                '-size',
                '-dm'
            ])
            
            result = subprocess.run(
                cmd,
                check=True,
                timeout=30,
                creationflags=creationflags,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Parse stdout output
            results = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Everything output format with -size -dm:
                    # <size> <date> <time> <full_path>
                    # Example: 1234567 2024-01-15 14:30 C:\Videos\movie.mp4
                    
                    parts = line.split(None, 3)  # Split on whitespace, max 4 parts
                    if len(parts) < 4:
                        continue
                    
                    size_str, date_str, time_str, file_path = parts
                    
                    # Parse size
                    try:
                        size = int(size_str.replace(',', ''))
                    except ValueError:
                        continue
                    
                    # Build path object
                    p = Path(file_path)
                    
                    results.append({
                        'name': p.name,
                        'path': str(p),
                        'size': size,
                        'extension': p.suffix.lower(),
                        'modified': f'{date_str} {time_str}'
                    })
                    
                except Exception:
                    continue
            
            return results
        
        except subprocess.CalledProcessError as e:
            # Fallback to OS search
            return self.search_os(drive, filters)
        except Exception:
            # Fallback to OS search
            return self.search_os(drive, filters)
    
    def search_os(self, drive: str, filters: Dict) -> List[Dict]:
        """Fallback search using os.walk"""
        results = []
        ext_filter = filters.get('extension', '').lower()
        min_size = filters.get('min_size', 0)
        max_size = filters.get('max_size', float('inf'))
        
        try:
            for root, dirs, files in os.walk(drive):
                for file in files:
                    try:
                        path = Path(root) / file
                        ext = path.suffix.lower()
                        
                        # Extension filter
                        if ext_filter:
                            if ext != f'.{ext_filter}':
                                continue
                        else:
                            if ext not in self.VIDEO_EXTENSIONS:
                                continue
                        
                        # Get file info
                        stat = path.stat()
                        size = stat.st_size
                        
                        # Size filter
                        if size < min_size or size > max_size:
                            continue
                        
                        results.append({
                            'name': path.name,
                            'path': str(path),
                            'size': size,
                            'extension': ext,
                            'modified': stat.st_mtime
                        })
                    except (PermissionError, OSError):
                        continue
        except Exception as e:
            print(f"OS search error: {e}")
        
        return results


if __name__ == "__main__":
    # Test code
    print("=== Video Searcher Test ===")
    
    searcher = VideoSearcher()
    status = searcher.get_everything_status()
    
    print(f"Everything Status: {status['status_text']}")
    print(f"Available Drives: {searcher.get_drives()}")
