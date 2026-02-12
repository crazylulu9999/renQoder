"""
비디오 인코딩 모듈
FFmpeg를 사용하여 비디오를 변환합니다.
"""

import subprocess
import os
import re
import json
from pathlib import Path
from metadata_utils import get_video_info, get_audio_info, format_duration


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
        return get_audio_info(input_file)
    
    def get_video_info(self, input_file):
        """
        ffprobe JSON 포맷을 사용하여 비디오 파일의 상세 정보를 가져옵니다.
        """
        info = get_video_info(input_file)
        
        # 최종 클래스 변수 업데이트 (기존 코드 호환성)
        self.total_seconds = info['duration']
        self.total_frames = info.get('frames', 0)
        
        return info

    def get_quality_metadata(self):
        """현재 인코더 타입에 따른 품질 설정 메타데이터를 반환합니다."""
        etype = self.encoder_type.lower()
        
        # 1. 하드웨어 코덱
        if 'nvenc' in etype:
            return {
                "label": "Quality (CQ)", 
                "min": 0, "max": 51, "default": 23, 
                "hint": "낮을수록 고화질 (0: 무손실, 23: 표준, 51: 최저)",
                "tooltip": (
                    "NVIDIA NVENC (CQ 모드)\n\n"
                    "- CQ (Constant Quality)는 영상의 복잡도에 따라 비트레이트를 가변적으로 조절하여\n"
                    "  일정한 화질을 유지하는 방식입니다.\n"
                    "- 값 범위: 0 (무손실) ~ 51 (최저 화질)\n"
                    "- 권장값(23)은 화질과 용량의 균형이 가장 좋습니다."
                )
            }
        elif 'qsv' in etype:
            return {
                "label": "Quality (ICQ)", 
                "min": 1, "max": 51, "default": 23, 
                "hint": "낮을수록 고화질 (1: 최고, 23: 표준, 51: 최저)",
                "tooltip": (
                    "Intel QSV (ICQ 모드)\n\n"
                    "- ICQ (Intelligent Constant Quality)는 인텔 그래픽에 최적화된 화질 제어 방식입니다.\n"
                    "- 값 범위: 1 (최고 화질) ~ 51 (최저 화질)\n"
                    "- 숫자가 낮을수록 고화질이며, 사람이 보기에 원본과 차이가 없는 수준을 목표로 합니다."
                )
            }
        elif 'amf' in etype:
            return {
                "label": "Quality (QP)", 
                "min": 0, "max": 51, "default": 23, 
                "hint": "낮을수록 고화질 (0: 최고, 23: 표준, 51: 최저)",
                "tooltip": (
                    "AMD AMF (QP 모드)\n\n"
                    "- QP (Quantization Parameter)는 양자화 매개변수를 직접 제어합니다.\n"
                    "- 값 범위: 0 (최고 화질) ~ 51 (최저 화질)\n"
                    "- CQP 모드를 사용하여 프레임별 화질을 일정하게 유지합니다."
                )
            }
            
        # 2. 소프트웨어 코덱 (개별 특성 반영)
        elif 'mpeg4' in etype:
            return {
                "label": "Quality (qscale)", 
                "min": 1, "max": 31, "default": 3, 
                "hint": "낮을수록 고화질 (1: 최고, 3: 표준, 31: 최저)",
                "tooltip": (
                    "MPEG-4 (qscale 모드)\n\n"
                    "- qscale (Fixed Quantizer)은 고정 양자화 계수를 사용합니다.\n"
                    "- 값 범위: 1 (최고 화질) ~ 31 (최저 화질)\n"
                    "- 구형 기기 호환성을 위해 사용되는 코덱의 화질 제어 방식입니다."
                )
            }
        elif 'vp9' in etype or 'av1' in etype or 'libaom' in etype or 'libsvtav1' in etype:
            # VP9/AV1은 CRF 범위가 0-63이며, 권장값도 x264보다 약간 높음
            return {
                "label": "Quality (CRF)", 
                "min": 0, "max": 63, "default": 30, 
                "hint": "낮을수록 고화질 (0: 무손실, 30: 표준, 63: 최저)",
                "tooltip": (
                    "VP9 / AV1 (CRF 모드)\n\n"
                    "- 차세대 코덱인 VP9/AV1은 x264보다 더 넓은 제어 범위를 가집니다.\n"
                    "- 값 범위: 0 (무손실) ~ 63 (최저 화질)\n"
                    "- 기본값 30 정도가 x264의 23과 유사한 시각적 품질을 제공합니다."
                )
            }
            
        # 3. 그 외 (x264, x265 등 표준 CRF)
        else: 
            return {
                "label": "Quality (CRF)", 
                "min": 0, "max": 51, "default": 23, 
                "hint": "낮을수록 고화질 (0: 무손실, 23: 표준, 51: 최저)",
                "tooltip": (
                    "H.264 / H.265 (CRF 모드)\n\n"
                    "- CRF (Constant Rate Factor)는 가장 널리 쓰이는 지능형 화질 제어 방식입니다.\n"
                    "- 값 범위: 0 (무손실) ~ 51 (최저 화질)\n"
                    "- 움직임이 많은 구간은 비트레이트를 높이고, 정적인 구간은 낮춰 효율적으로 압축합니다."
                )
            }
    
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
        # 품질 설정
        if 'nvenc' in self.encoder_type:
            # NVIDIA: -cq (Constant Quality)
            cmd.extend(['-preset', 'p7', '-cq', str(quality)])
        
        elif 'qsv' in self.encoder_type:
            # Intel QuickSync: -global_quality (ICQ)
            # QSV의 global_quality는 숫자가 높을수록 고화질인 경우도 있고 낮을수록 고화질인 경우도 있음 (코덱별 상이)
            # 하지만 ffmpeg wrapper에서는 보통 ICQ 모드에서 낮을수록 고화질 (CRF와 유사)
            cmd.extend(['-preset', 'veryslow', '-global_quality', str(quality)])
        
        elif 'amf' in self.encoder_type:
            # AMD AMF: -qp_i / -qp_p
            # AMF는 품질 모드 명시 필요
            cmd.extend(['-usage', 'transcoding', '-quality', 'quality', '-rc', 'cqp', '-qp_i', str(quality), '-qp_p', str(quality)])
            
        elif 'libvpx' in self.encoder_type:
            # VP8/VP9
            # -crf 사용, -b:v 0 필수
            cmd.extend(['-crf', str(quality), '-b:v', '0'])
            if 'vp9' in self.encoder_type:
                cmd.extend(['-row-mt', '1']) # 멀티스레딩
        
        elif 'av1' in self.encoder_type or 'libaom' in self.encoder_type or 'libsvtav1' in self.encoder_type:
            # AV1 Software
            # SVT-AV1, libaom-av1 모두 crf 지원 (-qp 대신 -crf 사용 권장 추세)
            # SVT-AV1: -crf, -preset (0-13, 높을수록 빠름), 여기선 6 정도가 적당
            if 'libsvtav1' in self.encoder_type:
                cmd.extend(['-crf', str(quality), '-preset', '6'])
            elif 'libaom' in self.encoder_type:
                cmd.extend(['-crf', str(quality), '-cpu-used', '4']) # cpu-used 0-8
            else:
                 cmd.extend(['-crf', str(quality)]) # hardware av1 implies implementation dependent, usually cq/qp handles above
                 
        else:  
            # x264, x265, MPEG-4 등 범용/레거시
            # x264/x265: -crf
            # mpeg4: -qscale:v
            if 'mpeg4' in self.encoder_type:
                 cmd.extend(['-qscale:v', str(quality)]) # mpeg4 qscale 1-31 직접 사용
            else:
                preset = 'slow' if 'libx265' in self.encoder_type else 'medium'
                cmd.extend(['-preset', preset, '-crf', str(quality)])
        
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
            # Hardware - HEVC
            'hevc_nvenc': 'NVENC_HEVC',
            'hevc_qsv': 'QSV_HEVC',
            'hevc_amf': 'AMF_HEVC',
            
            # Hardware - H.264
            'h264_nvenc': 'NVENC_H264',
            'h264_qsv': 'QSV_H264',
            'h264_amf': 'AMF_H264',
            
            # Hardware - AV1/VP9
            'av1_nvenc': 'NVENC_AV1',
            'av1_qsv': 'QSV_AV1',
            'av1_amf': 'AMF_AV1',
            'vp9_qsv': 'QSV_VP9',
            
            # Software
            'libx265': 'x265',
            'libx264': 'x264',
            'libvpx': 'VP8',
            'libvpx-vp9': 'VP9',
            'libaom-av1': 'AV1',
            'libsvtav1': 'AV1_SVT',
            'mpeg4': 'Xvid'
        }
        codec_short = codec_map.get(self.encoder_type, self.encoder_type)
        
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
            return {'total': 0, 'video': 0, 'audio': 0}
            
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
    
    def get_command_preview(self, input_file, output_file, quality=23, audio_mode="copy", overwrite=False, style="cmd"):
        """
        실행될 FFmpeg 명령어를 미리보기용 문자열로 반환합니다.
        
        Args:
            input_file: 입력 파일 경로
            output_file: 출력 파일 경로
            quality: 화질 설정값
            audio_mode: 오디오 모드
            overwrite: 덮어쓰기 여부
            style: 터미널 스타일 ("cmd" 또는 "unix")
            
        Returns:
            FFmpeg 명령어 문자열
        """
        cmd = self.build_command(input_file, output_file, quality, audio_mode, overwrite)
        
        # 스타일별 줄 바꿈 기호 (Windows CMD: ^, Unix Shell: \)
        line_cont = "^" if style == "cmd" else "\\"
        
        def quote_arg(arg):
            """터미널 특성에 맞게 인자 이스케이프"""
            if not arg:
                return '""'
            # 공백, 경로 구분자, 괄호 등 특수문자가 포함된 경우 따옴표 처리
            if any(c in arg for c in ' \\/():<>|&^!%*? '):
                return f'"{arg}"'
            return arg

        result = [cmd[0]] # 'ffmpeg'
        
        i = 1
        while i < len(cmd):
            arg = cmd[i]
            
            # 마지막 인자 (출력 파일) 처리
            if i == len(cmd) - 1:
                result.append(f" {line_cont}\n    {quote_arg(arg)}")
                break
                
            # 옵션 처리 (-i, -c:v 등)
            if arg.startswith('-'):
                # 값과 함께 붙여서 표시할 옵션들 처리 (가독성 고려)
                if i + 1 < len(cmd) and not cmd[i+1].startswith('-'):
                    val = cmd[i+1]
                    result.append(f" {line_cont}\n    {arg} {quote_arg(val)}")
                    i += 1 # 값 인자 소모
                else:
                    result.append(f" {line_cont}\n    {arg}")
            else:
                # 독립 인자
                result.append(f" {quote_arg(arg)}")
            i += 1
            
        return "".join(result)
    
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
            # metadata_utils의 로직은 아니지만 단순 변환이므로 유지하거나 
            # 필요시 통합 가능. 여기서는 그대로 둠.
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
