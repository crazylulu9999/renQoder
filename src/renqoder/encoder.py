"""
비디오 인코딩 모듈
FFmpeg를 사용하여 비디오를 변환합니다.
"""

import subprocess
import os
import re
import json
from pathlib import Path


class VideoEncoder:
    """비디오 인코딩을 담당하는 클래스"""
    
    def __init__(self, encoder_type="hevc_nvenc"):
        self.encoder_type = encoder_type
        self.process = None
        self.total_frames = 0
        self.current_frame = 0
        self.total_seconds = 0
        self.current_seconds = 0
        
    def get_audio_info(self, input_file):
        """ffprobe JSON 포맷을 사용하여 오디오 상세 정보(코덱 + 비트레이트)를 가져옵니다."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a:0',
                input_file
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
                if 'AAC' in codec: display_codec = 'AAC'
                elif 'AC3' in codec: display_codec = 'AC3'
                elif 'EAC3' in codec: display_codec = 'EAC3'
                elif 'DTS' in codec: display_codec = 'DTS'
                elif 'TRUEHD' in codec: display_codec = 'TrueHD'
                elif 'FLAC' in codec: display_codec = 'FLAC'
                elif 'OPUS' in codec: display_codec = 'Opus'
                elif 'PCM' in codec: display_codec = 'PCM'
                else: display_codec = codec
                
                # 비트레이트 정보 추가
                if bitrate_raw and str(bitrate_raw).isdigit():
                    kbps = round(int(bitrate_raw) / 1000)
                    return f"{display_codec}{kbps}k"
                
                return display_codec
        except Exception as e:
            print(f"오디오 정보 가져오기 실패: {e}")
        
        return 'Unknown'
    
    def get_video_info(self, input_file):
        """
        ffprobe JSON 포맷을 사용하여 비디오 파일의 상세 정보를 가져옵니다.
        """
        info = {
            'duration': 0,
            'frames': 0,
            'fps': 0,
            'width': 0,
            'height': 0,
            'codec': 'unknown',
            'size': 0,
            'bit_rate': 0,
            'audio_size': 0
        }
        
        try:
            # JSON 포맷으로 상세 정보 요청
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_file
            ]
            
            # Windows에서 CMD 창 생성 방지
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=creationflags)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Format 섹션에서 전체 정보 확인
                format_data = data.get('format', {})
                if 'duration' in format_data:
                    info['duration'] = float(format_data['duration'])
                if 'size' in format_data:
                    info['size'] = int(format_data['size'])
                if 'bit_rate' in format_data:
                    info['bit_rate'] = int(format_data['bit_rate'])

                # Stream 섹션에서 스트림 정보 확인
                streams = data.get('streams', [])
                total_audio_size = 0
                
                for stream in streams:
                    codec_type = stream.get('codec_type')
                    
                    if codec_type == 'video' and info['codec'] == 'unknown':
                        info['codec'] = stream.get('codec_name', 'unknown')
                        info['width'] = int(stream.get('width', 0))
                        info['height'] = int(stream.get('height', 0))
                        
                        # nb_frames 확인
                        if stream.get('nb_frames'):
                            info['frames'] = int(stream['nb_frames'])
                        
                        # FPS 확인 (r_frame_rate "30/1" 형식 대응)
                        fps_raw = stream.get('r_frame_rate', '0/0')
                        if '/' in fps_raw:
                            num, den = fps_raw.split('/')
                            if float(den) > 0:
                                info['fps'] = float(num) / float(den)
                    
                    elif codec_type == 'audio':
                        # 실제 스트림 사이즈 정보가 있는 경우 사용
                        s_size = int(stream.get('size', 0))
                        if s_size <= 0:
                            # 사이즈 정보가 없으면 비트레이트와 길이로 계산
                            s_bitrate = int(stream.get('bit_rate', 0))
                            s_duration = float(stream.get('duration', info['duration']))
                            if s_bitrate > 0 and s_duration > 0:
                                s_size = int((s_bitrate * s_duration) / 8)
                        
                        total_audio_size += s_size
                
                info['audio_size'] = total_audio_size
                
                # 보정: nb_frames가 없거나 0인 경우 (duration * fps)
                if info['frames'] <= 0 and info['duration'] > 0 and info['fps'] > 0:
                    info['frames'] = int(info['duration'] * info['fps'])
                # 보정: duration이 없는데 frames/fps가 있는 경우
                elif info['duration'] <= 0 and info['frames'] > 0 and info['fps'] > 0:
                    info['duration'] = info['frames'] / info['fps']

            # 최종 클래스 변수 업데이트
            self.total_seconds = info['duration']
            self.total_frames = info['frames']
            
            return info
            
        except Exception as e:
            print(f"비디오 정보 가져오기 실패: {e}")
        
        return info
    
    def build_command(self, input_file, output_file, quality=23, audio_mode="copy", overwrite=False):
        """FFmpeg 명령어를 생성합니다."""
        
        # 기본 명령어
        cmd = ['ffmpeg', '-hide_banner']
        if overwrite:
            cmd.append('-y')
        
        cmd.extend(['-i', input_file, '-map', '0:v', '-map', '0:a'])
        
        # 비디오 인코더 설정
        cmd.extend(['-c:v', self.encoder_type])
        
        # 품질 설정 (CQP)
        if 'nvenc' in self.encoder_type:
            cmd.extend(['-preset', 'p7', '-cq', str(quality)])
        elif 'qsv' in self.encoder_type:
            cmd.extend(['-preset', 'veryslow', '-global_quality', str(quality)])
        elif 'amf' in self.encoder_type:
            cmd.extend(['-quality', 'quality', '-qp_i', str(quality), '-qp_p', str(quality)])
        else:  # libx265
            cmd.extend(['-preset', 'slow', '-crf', str(quality)])
        
        # 오디오 설정
        if audio_mode == "copy":
            cmd.extend(['-c:a', 'copy'])
        else:  # AAC
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        
        # HEVC 태그 (Apple 호환성)
        cmd.extend(['-tag:v', 'hvc1'])
        
        
        # 출력 파일
        cmd.append(output_file)
        
        return cmd
    
    def generate_output_filename(self, input_file, quality, audio_mode):
        """
        출력 파일명을 생성합니다.
        
        Args:
            input_file: 입력 파일 경로
            quality: 화질 설정값
            audio_mode: 오디오 모드
            
        Returns:
            생성된 출력 파일 경로
        """
        input_path = Path(input_file)
        
        # 코덱 이름 간소화
        codec_map = {
            'hevc_nvenc': 'NVENC',
            'hevc_qsv': 'QSV',
            'hevc_amf': 'AMF',
            'libx265': 'x265'
        }
        codec_short = codec_map.get(self.encoder_type, 'HEVC')
        
        # 오디오 모드 표시
        if audio_mode == 'aac':
            audio_suffix = 'AAC192k'  # AAC 변환 시 비트레이트 명시
        else:
            # Copy 모드일 때 원본 오디오 정보 감지 (코덱 + 비트레이트)
            original_audio_info = self.get_audio_info(input_file)
            audio_suffix = original_audio_info
        
        # 파일명 생성: 원본명_코덱_CQ품질_오디오.mp4
        output_filename = f"{input_path.stem}_{codec_short}_CQ{quality}_{audio_suffix}.mp4"
        output_file = str(input_path.parent / output_filename)
        
        return output_file

    def estimate_output_size(self, video_info, quality, audio_mode):
        """
        인코딩 후 예상되는 파일 크기를 계산합니다. (Heuristic model)
        
        Args:
            video_info: get_video_info에서 반환된 딕셔너리
            quality: CQ 설정값 (18-35)
            audio_mode: 'copy' 또는 'aac'
            
        Returns:
            예상 파일 크기 (bytes)
        """
        duration = video_info.get('duration', 0)
        if duration <= 0:
            return 0
            
        width = video_info.get('width', 1920)
        height = video_info.get('height', 1080)
        fps = video_info.get('fps', 30)
        
        # 1. 비디오 비트레이트 추정 (HEVC/H.265 기준)
        # 기본 픽셀 당 비트 모델: bpp (bits per pixel)
        # CQ 23, 1080p, 30fps 기준 대략 2Mbps-4Mbps 타겟
        # CQ에 따른 지수적 변화 반영: CQ가 6 증가할 때마다 비트레이트 대략 절반
        
        base_bpp = 0.12  # CQ 23 기준의 기준 bpp (현실적인 실사 영상 기준)
        cq_offset = quality - 23
        # 지수적 감쇄: 2^(-cq_offset/7) (보정된 감쇄율)
        estimated_bpp = base_bpp * (0.5 ** (cq_offset / 7.0))
        
        # 해상도 및 FPS 반영
        pixel_count = width * height * fps
        v_bitrate = pixel_count * estimated_bpp
        
        if audio_mode == 'aac':
            a_bitrate = 192000  # 192kbps
            a_size = (a_bitrate * duration) / 8
        else:
            # 원본 오디오 사이즈를 그대로 사용 (Copy 모드)
            a_size = video_info.get('audio_size', 0)
            
            # 만약 audio_size가 감지되지 않았다면 폴백
            if a_size <= 0:
                total_orig_bitrate = video_info.get('bit_rate', 0)
                if total_orig_bitrate > 0:
                    a_bitrate = total_orig_bitrate * 0.1 # 대략 10% 가정
                    a_size = (a_bitrate * duration) / 8
                else:
                    a_size = (128000 * duration) / 8
        
        # 3. 전체 크기 계산
        v_size = (v_bitrate * duration) / 8
        estimated_size = v_size + a_size
        
        return {
            'total': int(estimated_size),
            'video': int(v_size),
            'audio': int(a_size)
        }
    
    def get_command_preview(self, input_file, output_file, quality=23, audio_mode="copy", overwrite=False):
        """
        실행될 FFmpeg 명령어를 미리보기용 문자열로 반환합니다.
        
        Args:
            input_file: 입력 파일 경로
            output_file: 출력 파일 경로
            quality: 화질 설정값
            audio_mode: 오디오 모드
            overwrite: 덮어쓰기 여부
            
        Returns:
            FFmpeg 명령어 문자열
        """
        cmd = self.build_command(input_file, output_file, quality, audio_mode, overwrite)
        
        # 명령어를 읽기 쉽게 여러 줄로 포맷팅 (Windows CLI 스타일)
        formatted_cmd = [cmd[0]] # 'ffmpeg'
        
        i = 1
        while i < len(cmd):
            arg = cmd[i]
            # 출력 파일(마지막 인자) 앞에는 줄바꿈
            if i == len(cmd) - 1:
                formatted_cmd.append(f" ^\n    \"{arg}\"")
            # 주요 옵션들 앞에 줄바꿈
            elif arg.startswith('-'):
                # 값과 함께 붙여서 표시할 옵션들 처리
                if i + 1 < len(cmd) and not cmd[i+1].startswith('-'):
                    # 파일 경로인 경우 따옴표 추가
                    val = cmd[i+1]
                    if '\\' in val or '/' in val or ' ' in val:
                        val = f"\"{val}\""
                    formatted_cmd.append(f" ^\n    {arg} {val}")
                    i += 1
                else:
                    formatted_cmd.append(f" ^\n    {arg}")
            else:
                formatted_cmd.append(f" {arg}")
            i += 1
            
        return "".join(formatted_cmd)
    
    def encode(self, input_file, quality=23, audio_mode="copy", output_file=None, progress_callback=None, log_callback=None, overwrite=False):
        """
        비디오를 인코딩합니다.
        
        Args:
            input_file: 입력 파일 경로
            quality: 화질 (18-35, 낮을수록 고화질)
            audio_mode: 오디오 모드 ("copy" 또는 "aac")
            output_file: 출력 파일 경로 (None이면 자동 생성)
            progress_callback: 진행률 콜백 함수 (0-100 값 전달)
            log_callback: 로그 콜백 함수 (문자열 전달)
            overwrite: 덮어쓰기 여부
        
        Returns:
            성공 시 출력 파일 경로, 실패 시 None
        """
        
        # 출력 파일명 생성 또는 사용
        if output_file is None:
            output_file = self.generate_output_filename(input_file, quality, audio_mode)

        
        # 비디오 정보 가져오기 (인코딩 시작 직전 최종 동기화)
        info = self.get_video_info(input_file)
        self.total_seconds = info['duration']
        self.total_frames = info['frames']
        
        if log_callback:
            log_callback(f"진행률 계산 기준: {self.total_seconds:.2f}초 / {self.total_frames}프레임")
        
        # FFmpeg 명령어 생성
        cmd = self.build_command(input_file, output_file, quality, audio_mode, overwrite)
        
        if log_callback:
            log_callback(f"실행 명령어: {' '.join(cmd)}")
        else:
            print(f"실행 명령어: {' '.join(cmd)}")
        
        try:
            # FFmpeg 프로세스 실행
            # Windows에서 CMD 창 생성 방지
            creationflags = 0x08000000 if os.name == 'nt' else 0
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,  # 사용자 입력 요구 차단
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # stderr를 stdout으로 통합
                universal_newlines=True,
                bufsize=1,
                creationflags=creationflags
            )
            
            # 진행률 모니터링
            while True:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                
                if not line:
                    continue
                
                clean_line = line.strip()
                
                # FFmpeg의 기본 진행률 라인 감지 (frame= ... fps= ... q= ... size= ... time= ... bitrate= ... speed= ...)
                if 'frame=' in clean_line and 'time=' in clean_line:
                    if log_callback:
                        log_callback(clean_line)
                    
                    # 진행률 바 업데이트를 위한 시간 추출
                    time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}[.,]\d+)", clean_line)
                    speed_match = re.search(r"speed=\s*([\d.]+)x", clean_line)
                    
                    if time_match:
                        self.current_seconds = self.convert_to_seconds(time_match.group(1).replace(',', '.'))
                        if self.total_seconds > 0:
                            progress = min(100, int((self.current_seconds / self.total_seconds) * 100))
                            
                            # 속도 및 남은 시간 계산
                            speed_str = "0.00x"
                            remaining_str = "계산 중..."
                            
                            if speed_match:
                                speed_val = float(speed_match.group(1))
                                speed_str = f"{speed_val:.2f}x"
                                
                                if speed_val > 0:
                                    remaining_seconds = (self.total_seconds - self.current_seconds) / speed_val
                                    if remaining_seconds > 0:
                                        m, s = divmod(int(remaining_seconds), 60)
                                        h, m = divmod(m, 60)
                                        if h > 0:
                                            remaining_str = f"{h:d}:{m:02d}:{s:02d}"
                                        else:
                                            remaining_str = f"{m:02d}:{s:02d}"
                                    else:
                                        remaining_str = "00:00"
                            
                            if progress_callback:
                                # 하위 호환성을 위해 progress 값과 함께 상세 정보 전달
                                progress_data = {
                                    'progress': progress,
                                    'speed': speed_str,
                                    'remaining': remaining_str
                                }
                                progress_callback(progress_data)
                
                # 기타 정보성 로그 (Duration, Stream 등)
                elif "Duration:" in clean_line or "Stream #" in clean_line:
                    if log_callback:
                        log_callback(clean_line)
                    
                    # 수동 Duration 감지 (폴백)
                    if "Duration:" in clean_line and self.total_seconds <= 0:
                        match = re.search(r"Duration:\s*(\d{2}:\d{2}:\d{2}[.,]\d+)", clean_line)
                        if match:
                            found_duration = self.convert_to_seconds(match.group(1).replace(',', '.'))
                            if found_duration > 0:
                                self.total_seconds = found_duration

                # 에러 로그 출력 (디버깅용)
                lower_line = line.lower()
                if 'error' in lower_line or 'fail' in lower_line or 'critical' in lower_line:
                    print(f"FFmpeg Log: {line.strip()}")
                elif 'size=' in lower_line and 'time=' in lower_line:
                    # 일반 로그줄에서 진행률 추출 시도 (위에서 안됐을 경우 대비)
                    pass

            # 프로세스 종료 대기
            self.process.wait()
            
            if self.process.returncode == 0:
                print(f"인코딩 완료: {output_file}")
                return output_file
            else:
                error = self.process.stderr.read()
                print(f"인코딩 실패: {error}")
                return None
                
        except Exception as e:
            print(f"인코딩 중 오류: {e}")
            return None
    
    def cancel(self):
        """진행 중인 인코딩을 취소합니다."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()

    def convert_to_seconds(self, time_str):
        """HH:MM:SS.ms 형식의 문자열을 초(float) 단위로 변환"""
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            return 0


if __name__ == "__main__":
    # 테스트 코드
    print("=== Encoder Test ===")
    
    def progress_test(percent):
        print(f"진행률: {percent}%")
    
    encoder = VideoEncoder("hevc_nvenc")
    print(f"인코더: {encoder.encoder_type}")
