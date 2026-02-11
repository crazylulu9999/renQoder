"""
Video file searcher module
Provides fast video file search using Everything or OS fallback
"""

import subprocess
import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from metadata_utils import get_video_info


class VideoSearcher:
    """Video file searcher with Everything integration and metadata caching"""
    
    # Common video extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
        '.webm', '.m4v', '.ts', '.m2ts', '.vob', '.3gp'
    }
    
    def __init__(self):
        self.everything_available = self.check_everything_available()
        self.cache_file = Path.home() / '.renqoder_metadata_cache.json'
        self.metadata_cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Load metadata cache from file"""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def save_cache(self):
        """Save metadata cache to file"""
        try:
            self.cache_file.write_text(json.dumps(self.metadata_cache), encoding='utf-8')
        except Exception:
            pass

    def clear_cache(self):
        """Delete cache file and clear in-memory metadata"""
        self.metadata_cache = {}
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass

    def clear_cache_item(self, filepath: str) -> bool:
        """특정 파일의 캐시 정보만 삭제"""
        cache_key = self._get_cache_key(filepath)
        if cache_key in self.metadata_cache:
            del self.metadata_cache[cache_key]
            self.save_cache()
            return True
        return False

    def _get_cache_key(self, filepath: str) -> str:
        """Generate a privacy-preserving hash key for a file"""
        try:
            p = Path(filepath)
            stat = p.stat()
            # Combine path, size, and mtime for a unique hash
            # We hash the whole string so the original path is not readable in the JSON
            data = f"{str(p.absolute())}|{stat.st_size}|{stat.st_mtime}"
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        except Exception:
            return ""

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
    
    def get_drives_with_info(self) -> List[Dict]:
        """Get drives with detailed information (label, capacity, free space)"""
        if os.name != 'nt':
            return [{
                'letter': '/',
                'label': 'Root',
                'total': 0,
                'free': 0,
                'used': 0,
                'type': 'local'
            }]
        
        import ctypes
        drives_info = []
        
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f'{letter}:\\'
            if not os.path.exists(drive):
                continue
            
            try:
                # Get drive type
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                type_map = {
                    2: 'removable',  # Removable
                    3: 'local',      # Fixed
                    4: 'network',    # Network
                    5: 'cdrom',      # CD-ROM
                    6: 'ramdisk'     # RAM Disk
                }
                dtype = type_map.get(drive_type, 'unknown')
                
                # Get volume label
                volume_name_buffer = ctypes.create_unicode_buffer(261)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    drive, volume_name_buffer, 261, None, None, None, None, 0
                )
                label = volume_name_buffer.value or f"로컬 디스크"
                
                # Get disk usage
                usage = shutil.disk_usage(drive)
                
                drives_info.append({
                    'letter': drive,
                    'label': label,
                    'total': usage.total,
                    'free': usage.free,
                    'used': usage.used,
                    'type': dtype
                })
            except Exception:
                # Skip drives that can't be accessed
                continue
        
        return drives_info
    
    def search(self, drive: str) -> List[Dict]:
        """
        Search for all video files in a drive
        
        Args:
            drive: Drive path (e.g., 'C:\\')
        
        Returns:
            List of dicts with keys: name, path, size, extension, modified
        """
        if self.everything_available:
            return self.search_everything(drive)
        else:
            return self.search_os(drive)
    
    def search_everything(self, drive: str) -> List[Dict]:
        """Search using Everything (es.exe)"""
        try:
            # Build Everything command with options
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            # All video extensions
            ext_list = ';'.join(e.lstrip('.') for e in self.VIDEO_EXTENSIONS)
            ext_query = f'ext:{ext_list}'
            
            # Build command with -path option for drive filtering
            cmd = ['es.exe']
            
            # Add path filter if drive is specified
            if drive:
                cmd.extend(['-path', drive])
            
            # Add search query
            cmd.append(ext_query)
            
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
                    parts = line.split(None, 3)
                    if len(parts) < 4:
                        continue
                    
                    size_str, date_str, time_str, file_path = parts
                    
                    try:
                        size = int(size_str.replace(',', ''))
                    except ValueError:
                        continue
                    
                    p = Path(file_path)
                    results.append({
                        'name': p.name,
                        'path': str(p),
                        'size': size,
                        'extension': p.suffix.lower(),
                        'modified': f'{date_str} {time_str}',
                        'metadata_loaded': False  # Flag for UI to know if ffprobe has run
                    })
                    
                except Exception:
                    continue
            
            return results
        
        except subprocess.CalledProcessError:
            return self.search_os(drive)
        except Exception:
            return self.search_os(drive)
    
    def search_os(self, drive: str) -> List[Dict]:
        """Fallback search using os.walk"""
        results = []
        try:
            for root, dirs, files in os.walk(drive):
                for file in files:
                    try:
                        path = Path(root) / file
                        ext = path.suffix.lower()
                        
                        if ext not in self.VIDEO_EXTENSIONS:
                            continue
                        
                        stat = path.stat()
                        results.append({
                            'name': path.name,
                            'path': str(path),
                            'size': stat.st_size,
                            'extension': ext,
                            'modified': stat.st_mtime,
                            'metadata_loaded': False
                        })
                    except (PermissionError, OSError):
                        continue
        except Exception as e:
            print(f"OS search error: {e}")
        
        return results

    def extract_metadata(self, filepath: str, fast_only=False, progress_callback=None) -> Dict:
        """Extract detailed metadata using ffprobe, with persistent caching"""
        # 1. Check cache first
        cache_key = self._get_cache_key(filepath)
        if cache_key and cache_key in self.metadata_cache:
            cached_data = self.metadata_cache[cache_key]
            # 만약 이미 무효한 파일로 마킹되었다면 즉시 반환
            if cached_data.get('invalid'):
                return cached_data
            
            # 만약 이미 재생 시간이 유효하게 있거나, 1단계(빠른 스캔) 요청이라면 캐시 정보 사용
            if cached_data.get('duration', 0) > 0 or fast_only:
                return cached_data
            
            # 만약 재생 시간이 0인데 2단계(정밀 분석) 요청이 온 경우라면 
            # 캐시를 무시하고 아래에서 ffprobe + ffmpeg 정밀 스캔을 수행하도록 함

        # 2. Extract using unified metadata utility
        metadata = get_video_info(filepath, fast_only=fast_only, progress_callback=progress_callback)
            
        # 3. Store in cache and save
        if cache_key:
            self.metadata_cache[cache_key] = metadata
            self.save_cache()
            
        return metadata



if __name__ == "__main__":
    # Test code
    print("=== Video Searcher Test ===")
    
    searcher = VideoSearcher()
    status = searcher.get_everything_status()
    
    print(f"Everything Status: {status['status_text']}")
    print(f"Available Drives: {searcher.get_drives()}")
