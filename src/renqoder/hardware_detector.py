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


    
    def get_available_codecs(self):
        """시스템에서 사용 가능한 모든 FFmpeg 비디오 코덱 목록을 반환합니다."""
        # 감지할 코덱 맵핑 (우선순위 순)
        # 포맷: (ffmpeg_encoder_name, ui_label, type, description, vendor)
        target_codecs = [
            # Hardware - NVIDIA
            ('hevc_nvenc', 'HEVC (NVIDIA NVENC)', 'hardware', 'NVIDIA GPU를 사용한 고속 HEVC 인코딩', 'NVIDIA'),
            ('h264_nvenc', 'H.264 (NVIDIA NVENC)', 'hardware', 'NVIDIA GPU를 사용한 고속 H.264 인코딩', 'NVIDIA'),
            ('av1_nvenc', 'AV1 (NVIDIA NVENC)', 'hardware', 'NVIDIA GPU를 사용한 고속 AV1 인코딩 (RTX 40 시리즈 이상)', 'NVIDIA'),
            
            # Hardware - Intel QSV
            ('hevc_qsv', 'HEVC (Intel QSV)', 'hardware', 'Intel 내장/외장 그래픽을 사용한 고속 HEVC 인코딩', 'Intel'),
            ('h264_qsv', 'H.264 (Intel QSV)', 'hardware', 'Intel 내장/외장 그래픽을 사용한 고속 H.264 인코딩', 'Intel'),
            ('vp9_qsv', 'VP9 (Intel QSV)', 'hardware', 'Intel 그래픽을 사용한 고속 VP9 인코딩', 'Intel'),
            ('av1_qsv', 'AV1 (Intel QSV)', 'hardware', 'Intel Arc/14세대 이상 그래픽을 사용한 고속 AV1 인코딩', 'Intel'),
            
            # Hardware - AMD AMF
            ('hevc_amf', 'HEVC (AMD AMF)', 'hardware', 'AMD GPU를 사용한 고속 HEVC 인코딩', 'AMD'),
            ('h264_amf', 'H.264 (AMD AMF)', 'hardware', 'AMD GPU를 사용한 고속 H.264 인코딩', 'AMD'),
            ('av1_amf', 'AV1 (AMD AMF)', 'hardware', 'AMD GPU를 사용한 고속 AV1 인코딩 (RX 7000 시리즈 이상)', 'AMD'),
            
            # Software
            ('libx265', 'HEVC (x265)', 'software', '가장 대중적인 고효율 소프트웨어 HEVC 인코더', 'CPU'),
            ('libx264', 'H.264 (x264)', 'software', '최고의 안정성과 호환성을 가진 소프트웨어 H.264 인코더', 'CPU'),
            ('libvpx-vp9', 'VP9 (libvpx)', 'software', 'Google의 오픈소스 고성능 비디오 코덱', 'CPU'),
            ('libaom-av1', 'AV1 (libaom)', 'software', '차세대 표준 AV1 코덱 (느리지만 매우 높은 압축률)', 'CPU'),
            ('libsvtav1', 'AV1 (SVT-AV1)', 'software', '인텔에서 개발한 고속 AV1 소프트웨어 인코더', 'CPU'),
            ('libvpx', 'VP8 (libvpx)', 'software', '웹용 구형 오픈소스 코덱', 'CPU'),
            ('mpeg4', 'MPEG-4 (Xvid)', 'software', '오래된 장치 호환성을 위한 MPEG-4 코덱', 'CPU'),
        ]

        found_ids = set()
        
        # 실제 시스템에 존재하는 GPU 벤더 목록 확인 (중복 벤더 대응)
        present_vendors = {self.gpu_vendor}
        try:
            creationflags = 0x08000000 if os.name == 'nt' else 0
            res = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                capture_output=True, text=True, creationflags=creationflags, timeout=5)
            gpu_text = res.stdout.lower()
            if 'intel' in gpu_text: present_vendors.add('Intel')
            if 'nvidia' in gpu_text: present_vendors.add('NVIDIA')
            if 'amd' in gpu_text or 'radeon' in gpu_text: present_vendors.add('AMD')
        except:
            pass

        try:
            # 1. FFmpeg 인코더 목록 조회
            creationflags = 0x08000000 if os.name == 'nt' else 0
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                creationflags=creationflags,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                for line in output.splitlines():
                    clean_line = line.strip()
                    if not clean_line or len(clean_line) < 8 or not clean_line.startswith('V'):
                        continue
                        
                    parts = clean_line.split()
                    if len(parts) >= 2:
                        encoder_id = parts[1]
                        found_ids.add(encoder_id)
            
        except Exception:
            pass

        # 2. 모든 코덱 정보 구성 (지원 여부 + 하드웨어 검증 포함)
        all_info = []
        for target_id, label, c_type, desc, vendor in target_codecs:
            is_available = target_id in found_ids
            
            # 하드웨어 코덱의 경우, FFmpeg 목록에 있더라도 실제 하드웨어 정보와 일치해야 함
            if c_type == 'hardware':
                if vendor not in present_vendors:
                    is_available = False
            
            # 추천 코덱은 무조건 available로 표시 시도
            if not is_available and target_id == self.recommended_encoder and self.gpu_vendor != "CPU":
                is_available = True
                
            all_info.append({
                'id': target_id,
                'label': label,
                'type': c_type,
                'available': is_available,
                'description': desc,
                'vendor': vendor
            })
            
        return all_info

    def _get_fallback_codecs(self):
        """코덱 검색 실패 시 기본 목록 반환"""
        return [
            {'id': 'libx264', 'label': 'H.264 (x264)', 'type': 'software'},
            {'id': 'libx265', 'label': 'HEVC (x265)', 'type': 'software'}
        ]

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
