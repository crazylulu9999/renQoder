"""
ffprobe JSON 파싱 예제

이 스크립트는 renQoder의 encoder.py에서 사용하는 패턴을 기반으로
ffprobe를 사용하여 비디오 파일의 상세 정보를 추출하는 방법을 보여줍니다.
"""

import subprocess
import json
import os


def get_video_info(input_file):
    """
    ffprobe JSON 포맷을 사용하여 비디오 파일의 상세 정보를 가져옵니다.
    
    Returns:
        dict: 비디오 정보 딕셔너리
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
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=5, 
            creationflags=creationflags
        )
        
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

        return info
        
    except Exception as e:
        print(f"비디오 정보 가져오기 실패: {e}")
    
    return info


if __name__ == "__main__":
    # 사용 예제
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python ffprobe_json_parsing.py <비디오 파일>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    info = get_video_info(video_file)
    
    print("=== 비디오 정보 ===")
    print(f"코덱: {info['codec']}")
    print(f"해상도: {info['width']}x{info['height']}")
    print(f"FPS: {info['fps']:.2f}")
    print(f"총 프레임: {info['frames']}")
    print(f"재생 시간: {info['duration']:.2f}초")
    print(f"파일 크기: {info['size'] / 1024 / 1024:.2f} MB")
    print(f"비트레이트: {info['bit_rate'] / 1000:.0f} kbps")
    print(f"오디오 크기: {info['audio_size'] / 1024 / 1024:.2f} MB")
