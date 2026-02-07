"""
하드웨어 감지 모듈
GPU 제조사를 감지하고 최적의 FFmpeg 코덱을 반환합니다.
"""

import subprocess
import platform
import os


class HardwareDetector:
    """시스템 하드웨어를 감지하고 최적의 인코더를 제안하는 클래스"""
    
    def __init__(self):
        self.gpu_vendor = None
        self.recommended_encoder = None
        self.encoder_name = None
        
    def detect_gpu(self):
        """GPU 제조사를 감지합니다."""
        system = platform.system()
        
        if system == "Windows":
            return self._detect_gpu_windows()
        else:
            # Linux/Mac은 추후 구현
            return self._detect_gpu_fallback()
    
    def _detect_gpu_windows(self):
        """Windows에서 GPU를 감지합니다."""
        try:
            # Windows에서 CMD 창 생성 방지
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            # wmic 명령어로 GPU 정보 확인
            result = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=creationflags
            )
            
            gpu_info = result.stdout.lower()
            
            # NVIDIA 우선 확인
            if 'nvidia' in gpu_info or 'geforce' in gpu_info or 'rtx' in gpu_info or 'gtx' in gpu_info:
                self.gpu_vendor = "NVIDIA"
                self.recommended_encoder = "hevc_nvenc"
                self.encoder_name = "NVIDIA NVENC"
                return True
            
            # Intel 확인
            elif 'intel' in gpu_info:
                self.gpu_vendor = "Intel"
                self.recommended_encoder = "hevc_qsv"
                self.encoder_name = "Intel Quick Sync Video"
                return True
            
            # AMD 확인
            elif 'amd' in gpu_info or 'radeon' in gpu_info:
                self.gpu_vendor = "AMD"
                self.recommended_encoder = "hevc_amf"
                self.encoder_name = "AMD AMF"
                return True
            
            else:
                return self._detect_gpu_fallback()
                
        except Exception as e:
            print(f"GPU 감지 중 오류: {e}")
            return self._detect_gpu_fallback()
    
    def _detect_gpu_fallback(self):
        """GPU를 감지하지 못한 경우 CPU 인코더 사용"""
        self.gpu_vendor = "CPU"
        self.recommended_encoder = "libx265"
        self.encoder_name = "CPU (libx265)"
        return False
    
    def get_encoder_info(self):
        """현재 감지된 인코더 정보를 반환합니다."""
        return {
            'vendor': self.gpu_vendor,
            'encoder': self.recommended_encoder,
            'name': self.encoder_name
        }
    
    def get_accent_color(self):
        """GPU 제조사에 따른 UI 포인트 컬러를 반환합니다."""
        color_map = {
            'NVIDIA': '#76b900',  # Green
            'Intel': '#0071c5',   # Blue
            'AMD': '#ed1c24',     # Red
            'CPU': '#888888'      # Gray
        }
        return color_map.get(self.gpu_vendor, '#888888')


def check_ffmpeg():
    """FFmpeg 설치 여부를 확인합니다."""
    try:
        # Windows에서 CMD 창 생성 방지
        creationflags = 0x08000000 if os.name == 'nt' else 0
        
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5,
            creationflags=creationflags
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    # 테스트 코드
    print("=== Hardware Detection Test ===")
    
    # FFmpeg 확인
    if check_ffmpeg():
        print("✓ FFmpeg 설치됨")
    else:
        print("✗ FFmpeg 미설치")
    
    # GPU 감지
    detector = HardwareDetector()
    detector.detect_gpu()
    info = detector.get_encoder_info()
    
    print(f"\n감지된 GPU: {info['vendor']}")
    print(f"권장 인코더: {info['encoder']}")
    print(f"인코더 이름: {info['name']}")
    print(f"UI 포인트 컬러: {detector.get_accent_color()}")
