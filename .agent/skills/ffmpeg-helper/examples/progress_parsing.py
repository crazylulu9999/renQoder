"""
FFmpeg 진행률 파싱 예제

이 스크립트는 renQoder의 encoder.py에서 사용하는 패턴을 기반으로
FFmpeg의 stderr 출력을 파싱하여 진행률을 계산하는 방법을 보여줍니다.
"""

import subprocess
import re
import os


def convert_to_seconds(time_str):
    """
    HH:MM:SS.ms 형식의 문자열을 초(float) 단위로 변환
    
    Args:
        time_str: "00:01:23.45" 형식의 시간 문자열
    
    Returns:
        float: 초 단위 시간
    """
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    if len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


def encode_with_progress(input_file, output_file, total_duration):
    """
    FFmpeg로 인코딩하면서 진행률을 실시간으로 출력합니다.
    
    Args:
        input_file: 입력 파일 경로
        output_file: 출력 파일 경로
        total_duration: 전체 재생 시간 (초)
    """
    # FFmpeg 명령어 (간단한 HEVC 인코딩 예제)
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-i', input_file,
        '-c:v', 'libx265',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_file
    ]
    
    print(f"실행 명령어: {' '.join(cmd)}")
    print("=" * 60)
    
    # Windows에서 CMD 창 생성 방지
    creationflags = 0x08000000 if os.name == 'nt' else 0
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # stderr를 stdout으로 통합
            universal_newlines=True,
            bufsize=1,
            creationflags=creationflags
        )
        
        # 진행률 모니터링
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if not line:
                continue
            
            clean_line = line.strip()
            
            # FFmpeg의 기본 진행률 라인 감지
            if 'frame=' in clean_line and 'time=' in clean_line:
                # 진행률 바 업데이트를 위한 시간 추출
                time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}[.,]\d+)", clean_line)
                speed_match = re.search(r"speed=\s*([\d.]+)x", clean_line)
                
                if time_match:
                    current_seconds = convert_to_seconds(time_match.group(1))
                    if total_duration > 0:
                        progress = min(100, int((current_seconds / total_duration) * 100))
                        
                        # 속도 및 남은 시간 계산
                        speed_str = "0.00x"
                        remaining_str = "계산 중..."
                        
                        if speed_match:
                            speed_val = float(speed_match.group(1))
                            speed_str = f"{speed_val:.2f}x"
                            
                            if speed_val > 0:
                                remaining_seconds = (total_duration - current_seconds) / speed_val
                                if remaining_seconds > 0:
                                    m, s = divmod(int(remaining_seconds), 60)
                                    h, m = divmod(m, 60)
                                    if h > 0:
                                        remaining_str = f"{h:d}:{m:02d}:{s:02d}"
                                    else:
                                        remaining_str = f"{m:02d}:{s:02d}"
                                else:
                                    remaining_str = "00:00"
                        
                        # 진행률 출력
                        print(f"\r진행률: {progress}% | 속도: {speed_str} | 남은 시간: {remaining_str}", end='')
            
            # 기타 정보성 로그 (Duration, Stream 등)
            elif "Duration:" in clean_line or "Stream #" in clean_line:
                print(clean_line)
        
        print("\n" + "=" * 60)
        
        # 프로세스 종료 대기
        return_code = process.wait()
        
        if return_code == 0:
            print("✅ 인코딩 완료!")
        else:
            print(f"❌ 인코딩 실패 (종료 코드: {return_code})")
        
        return return_code == 0
        
    except Exception as e:
        print(f"❌ 인코딩 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("사용법: python progress_parsing.py <입력 파일> <출력 파일> <재생 시간(초)>")
        print("예제: python progress_parsing.py input.mp4 output.mp4 120.5")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    total_duration = float(sys.argv[3])
    
    success = encode_with_progress(input_file, output_file, total_duration)
    sys.exit(0 if success else 1)
