"""
비디오 및 오디오 메타데이터 추출 유틸리티 모듈
FFmpeg 및 ffprobe를 사용하여 미디어 정보를 분석합니다.
"""

import subprocess
import os
import re
import json
import time as time_module
from typing import Dict, Optional, Callable

def check_everything_available() -> bool:
    """es.exe(Everything CLI)가 사용 가능한지 확인합니다."""
    try:
        creationflags = 0x08000000 if os.name == 'nt' else 0
        result = subprocess.run(
            ['es.exe', '-n', '0'],
            capture_output=True,
            timeout=1,
            creationflags=creationflags
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False

def get_file_size_via_everything(filepath: str) -> int:
    """Everything을 통해 파일 크기를 초고속으로 가져옵니다."""
    try:
        creationflags = 0x08000000 if os.name == 'nt' else 0
        # -size-column 옵션으로 크기만 출력하도록 시도
        result = subprocess.run(
            ['es.exe', filepath, '-size'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=2,
            creationflags=creationflags
        )
        if result.returncode == 0 and result.stdout:
            # 출력 형식: "파일명 크기" 또는 "크기" (설정에 따라 다름)
            # 보통 es.exe 파일명 -size 하면 "경로  크기" 형태로 나옴
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].rsplit(None, 1) # 오른쪽 끝의 공백 기준 분리
                if len(parts) >= 1 and parts[-1].isdigit():
                    return int(parts[-1])
    except Exception:
        pass
    return 0

def format_duration(seconds: float) -> str:
    """재생 시간을 'XX분 XX초' 형식 문자열로 변환합니다."""
    if seconds <= 0:
        return "알 수 없음"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}분 {secs}초"

def get_audio_info(filepath: str) -> str:
    """
    ffprobe JSON 포맷을 사용하여 오디오 상세 정보(코덱 + 비트레이트)를 가져옵니다.
    기존 encoder.py의 로직을 기반으로 합니다.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'a:0',
            filepath
        ]
        
        # Windows에서 CMD 창 생성 방지
        creationflags = 0x08000000 if os.name == 'nt' else 0
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=creationflags)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            if not streams:
                return 'None'
            
            a_stream = streams[0]
            codec = a_stream.get('codec_name', 'UNKNOWN').upper()
            bitrate_raw = a_stream.get('bit_rate', '')
            
            # 코덱 이름 정리
            codec_map = {
                'AAC': 'AAC',
                'AC3': 'AC3',
                'EAC3': 'EAC3',
                'DTS': 'DTS',
                'TRUEHD': 'TrueHD',
                'FLAC': 'FLAC',
                'OPUS': 'Opus',
                'PCM': 'PCM'
            }
            
            display_codec = codec
            for key, val in codec_map.items():
                if key in codec:
                    display_codec = val
                    break
            
            # 비트레이트 정보 추가 (미디어 표준인 1000 단위를 사용)
            if bitrate_raw and str(bitrate_raw).isdigit():
                kbps = round(int(bitrate_raw) / 1000)
                return f"{display_codec}{kbps}k"
            
            return display_codec
    except Exception as e:
        print(f"오디오 정보 가져오기 실패: {e}")
    
    return 'Unknown'

def get_video_info(filepath: str, fast_only: bool = False, progress_callback: Optional[Callable[[float], None]] = None) -> Dict:
    """
    ffprobe 및 ffmpeg를 사용하여 비디오 상세 정보(Stage 1 & 2)를 가져옵니다.
    정확한 FPS 추출 및 손상된 파일 정밀 분석을 포함합니다.
    """
    info = {
        'codec': 'unknown',
        'width': 0,
        'height': 0,
        'pixels': 0,
        'resolution': '0x0',
        'fps': 0.0,
        'bitrate': 0,
        'duration': 0.0,
        'duration_str': '알 수 없음',
        'audio_size': 0,
        'size': 0,
        'metadata_loaded': False,
        'invalid': False,
        'estimated_fields': {}
    }

    try:
        creationflags = 0x08000000 if os.name == 'nt' else 0
        
        # 1. ffprobe JSON 상세 분석 (Stage 1)
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            filepath
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            creationflags=creationflags,
            timeout=10
        )
        
        if result.returncode != 0:
            info['invalid'] = True
            info['metadata_loaded'] = True
            return info

        data = json.loads(result.stdout)
        
        # Format 정보 파싱
        format_data = data.get('format', {})
        duration_raw = float(format_data.get('duration', 0))
        
        # 파일 크기 확인 우선순위: 1. Everything, 2. OS System, 3. ffprobe
        file_size = 0
        if check_everything_available():
            file_size = get_file_size_via_everything(filepath)
            
        if file_size <= 0:
            try:
                file_size = os.path.getsize(filepath)
            except:
                pass
        
        if file_size <= 0:
            file_size = int(format_data.get('size', 0))
            
        info['size'] = file_size
        bitrate_raw = int(format_data.get('bit_rate', 0))

        # Stream 정보 파싱
        streams = data.get('streams', [])
        vstream = None
        total_audio_size = 0
        
        for s in streams:
            ctype = s.get('codec_type')
            if ctype == 'video' and vstream is None:
                vstream = s
            elif ctype == 'audio':
                # 오디오 사이즈 정보 추출
                s_size = int(s.get('size', 0))
                if s_size <= 0:
                    s_bitrate = int(s.get('bit_rate', 0))
                    s_duration = float(s.get('duration', duration_raw))
                    if s_bitrate > 0 and s_duration > 0:
                        s_size = int((s_bitrate * s_duration) / 8)
                total_audio_size += s_size
        
        info['audio_size'] = total_audio_size
        
        if vstream:
            info['codec'] = vstream.get('codec_name', 'unknown')
            info['width'] = int(vstream.get('width', 0))
            info['height'] = int(vstream.get('height', 0))
            info['pixels'] = info['width'] * info['height']
            info['resolution'] = f"{info['width']}x{info['height']}"
            info['frames'] = int(vstream.get('nb_frames', 0))
            
            # FPS 정확도 확보 (r_frame_rate)
            fps_raw = vstream.get('r_frame_rate', '0/0')
            if '/' in fps_raw:
                num, den = map(float, fps_raw.split('/'))
                if den > 0:
                    info['fps'] = round(num / den, 2)
            
            # Duration Fallback
            if duration_raw <= 0:
                try:
                    duration_raw = float(vstream.get('duration', 0))
                except (ValueError, TypeError):
                    pass
            
            # 보정: 재생 시간이 프레임 수에 비해 너무 짧은 경우 (corrupted timestamps)
            if duration_raw > 0 and info['fps'] > 0 and info['frames'] > 0:
                frame_based_duration = info['frames'] / info['fps']
                # 10배 이상 차이 나면 프레임 기반 정보가 더 정확할 가능성이 높음
                if frame_based_duration / duration_raw > 10:
                    duration_raw = frame_based_duration
                    info['estimated_fields']['duration'] = "파일 헤더의 재생 시간이 실제 데이터에 비해 너무 짧아 프레임 수 기반으로 계산되었습니다."
            
            # 2. ffmpeg 정밀 분석 (Stage 2)
            # 재생 시간이 0이거나, 파일 크기에 비해 너무 짧은 경우 (suspicious)
            is_suspicious = False
            if info['size'] > 10 * 1024 * 1024: # 10MB 이상 파일 대상
                if duration_raw < 1.0: # 1초 미만
                    is_suspicious = True
                else:
                    # 비트레이트가 비정상적으로 높은 경우 (예: 300Mbps 초과 - 일반적인 비디오에서는 거의 불가능)
                    temp_bitrate = (info['size'] * 8) / duration_raw
                    if temp_bitrate > 300 * 1000 * 1000: 
                        is_suspicious = True

            if (duration_raw <= 0 or is_suspicious) and not fast_only:
                try:
                    # 오디오 트랙 유무 확인
                    has_audio = False
                    for s in streams:
                        if s.get('codec_type') == 'audio':
                            has_audio = True
                            break
                    
                    # ffmpeg 스캔 명령어 빌드
                    ffmpeg_cmd = ['ffmpeg', '-i', filepath]
                    if has_audio:
                        ffmpeg_cmd.extend(['-map', '0:a', '-c', 'copy'])
                    ffmpeg_cmd.extend(['-f', 'null', '-'])
                    
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stderr=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        text=True,
                        encoding='utf-8',
                        creationflags=creationflags,
                        bufsize=1
                    )
                    
                    last_output_time = time_module.time()
                    inactivity_timeout = 60
                    final_dur = 0.0
                    
                    while True:
                        line = process.stderr.readline()
                        if line:
                            last_output_time = time_module.time()
                            time_match = re.search(r'time=\s*(\d+):(\d+):(\d+\.?\d*)', line)
                            if time_match:
                                h, m, s_val = map(float, time_match.groups())
                                current_dur = h * 3600 + m * 60 + s_val
                                if current_dur > final_dur:
                                    final_dur = current_dur
                                    if progress_callback:
                                        progress_callback(final_dur)
                        else:
                            if process.poll() is not None:
                                break
                            if time_module.time() - last_output_time > inactivity_timeout:
                                process.terminate()
                                process.wait(timeout=5)
                                break
                            time_module.sleep(0.1)
                    
                    duration_raw = final_dur
                    info['estimated_fields']['duration'] = "파일 헤더에 정보가 없어 FFmpeg 정밀 스캔을 통해 실제 재생 시간을 확인했습니다."
                except Exception as e:
                    print(f"정밀 분석 오류: {e}")
            
            info['duration'] = duration_raw
            info['duration_str'] = format_duration(duration_raw)
            
            # 보정: frames 계산 (반대 케이스: duration은 있는데 frames가 없는 경우)
            if info['frames'] <= 0 and info['duration'] > 0 and info['fps'] > 0:
                info['frames'] = int(info['duration'] * info['fps'])
            
            # 비트레이트 결정 (계산된 평균 비트레이트 우선 - 가장 정확함)
            # 비트레이트 표시 및 필터링 시에는 미디어 표준인 1000 단위를 사용 (1024 아님)
            if duration_raw > 0 and info['size'] > 0:
                info['bitrate'] = int((info['size'] * 8) / duration_raw)
                # 재생 시간이 추정된 것이라면 비트레이트 역시 결과적으로 추정된 값임
                if 'duration' in info['estimated_fields']:
                    info['estimated_fields']['bitrate'] = "추정된 재생 시간을 기반으로 계산된 평균 비트레이트입니다."
            else:
                bitrate = bitrate_raw
                if bitrate <= 0:
                    bitrate = int(vstream.get('bit_rate', 0))
                info['bitrate'] = bitrate
            
            info['metadata_loaded'] = True
        else:
            # 비디오 스트림이 없는 경우
            info['invalid'] = True
            info['metadata_loaded'] = True

    except Exception as e:
        print(f"메타데이터 추출 오류 ({filepath}): {e}")
        info['invalid'] = True
        info['metadata_loaded'] = True
        
    return info

