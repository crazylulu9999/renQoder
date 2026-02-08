---
name: ffmpeg-helper
description: FFmpeg를 사용한 비디오 인코딩 작업에 필요한 핵심 지식과 renQoder 프로젝트 특화 팁을 제공하는 스킬입니다.
---

# FFmpeg Helper Skill

이 스킬은 FFmpeg 공식 문서의 핵심 내용과 renQoder 프로젝트의 실제 사용 패턴을 결합하여, 비디오 인코딩 관련 작업 시 빠르게 참조할 수 있는 지식 베이스입니다.

## 주요 기능

- **ffprobe 정보 추출**: JSON 포맷을 사용한 비디오/오디오 메타데이터 추출
- **인코딩 옵션 가이드**: 코덱별 품질 제어, 프리셋, 오디오 처리 방법
- **진행률 모니터링**: FFmpeg stderr 출력 파싱 패턴
- **renQoder 특화 팁**: 파일 크기 추정, HEVC 태그 설정 등

---

## 1. ffprobe를 사용한 비디오 정보 추출

### 기본 명령어

```bash
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

### 주요 옵션

- `-v quiet`: 불필요한 로그 숨김
- `-print_format json`: JSON 포맷으로 출력
- `-show_format`: 컨테이너 포맷 정보 표시
- `-show_streams`: 스트림(비디오/오디오) 정보 표시

### JSON 출력 구조

```json
{
  "format": {
    "duration": "120.5",
    "size": "50000000",
    "bit_rate": "3320000"
  },
  "streams": [
    {
      "codec_type": "video",
      "codec_name": "h264",
      "width": 1920,
      "height": 1080,
      "r_frame_rate": "30/1",
      "nb_frames": "3615"
    },
    {
      "codec_type": "audio",
      "codec_name": "aac",
      "bit_rate": "192000",
      "duration": "120.5"
    }
  ]
}
```

### renQoder 활용 예시

`encoder.py`의 `get_video_info()` 메서드 참조:
- `format.duration`: 전체 재생 시간 (초)
- `format.size`: 파일 크기 (바이트)
- `streams[video].nb_frames`: 총 프레임 수
- `streams[video].r_frame_rate`: FPS (분수 형식, 예: "30/1")
- `streams[audio].size` 또는 `bit_rate * duration / 8`: 오디오 트랙 크기

---

## 2. 인코딩 옵션 가이드

### 코덱별 품질 제어

#### NVENC (NVIDIA 하드웨어 인코더)

```bash
ffmpeg -i input.mp4 -c:v hevc_nvenc -preset p7 -cq 23 output.mp4
```

- `-preset p7`: 최고 품질 프리셋 (p1~p7, 높을수록 느리지만 고품질)
- `-cq <value>`: Constant Quality 모드 (18-35, 낮을수록 고품질)

#### QSV (Intel Quick Sync Video)

```bash
ffmpeg -i input.mp4 -c:v hevc_qsv -preset veryslow -global_quality 23 output.mp4
```

- `-preset veryslow`: 품질 우선 프리셋
- `-global_quality <value>`: 품질 값 (18-35)

#### AMF (AMD 하드웨어 인코더)

```bash
ffmpeg -i input.mp4 -c:v hevc_amf -quality quality -qp_i 23 -qp_p 23 output.mp4
```

- `-quality quality`: 품질 우선 모드
- `-qp_i`, `-qp_p`: I/P 프레임 QP 값

#### libx265 (소프트웨어 인코더)

```bash
ffmpeg -i input.mp4 -c:v libx265 -preset slow -crf 23 output.mp4
```

- `-preset slow`: 인코딩 속도/품질 균형 (ultrafast ~ veryslow)
- `-crf <value>`: Constant Rate Factor (18-28 권장, 낮을수록 고품질)

### 오디오 처리

#### 오디오 복사 (재인코딩 없음)

```bash
ffmpeg -i input.mp4 -c:a copy output.mp4
```

#### AAC 인코딩

```bash
ffmpeg -i input.mp4 -c:a aac -b:a 192k output.mp4
```

- `-b:a 192k`: 오디오 비트레이트 (128k, 192k, 256k 등)

### 스트림 매핑

```bash
ffmpeg -i input.mp4 -map 0:v -map 0:a -c:v libx265 -c:a copy output.mp4
```

- `-map 0:v`: 모든 비디오 스트림 선택
- `-map 0:a`: 모든 오디오 스트림 선택

### renQoder 특화: HEVC 태그 설정

Apple 기기 호환성을 위해 HEVC 태그를 `hvc1`로 설정:

```bash
ffmpeg -i input.mp4 -c:v hevc_nvenc -tag:v hvc1 output.mp4
```

---

## 3. 진행률 모니터링

### FFmpeg stderr 출력 패턴

FFmpeg는 진행 상황을 stderr로 출력합니다:

```
frame= 1234 fps= 45 q=28.0 size=   12345kB time=00:01:23.45 bitrate=1234.5kbits/s speed=1.50x
```

### 주요 필드

- `frame=`: 현재 처리된 프레임 번호
- `fps=`: 초당 처리 프레임 수
- `time=`: 현재 처리된 시간 (HH:MM:SS.ms)
- `speed=`: 인코딩 속도 배율 (1.0x = 실시간)
- `bitrate=`: 현재 비트레이트

### 진행률 계산

```python
# time 필드에서 시간 추출
time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}[.,]\d+)", line)
if time_match:
    current_seconds = convert_to_seconds(time_match.group(1))
    progress = (current_seconds / total_seconds) * 100
```

### 남은 시간 계산

```python
# speed 필드에서 속도 추출
speed_match = re.search(r"speed=\s*([\d.]+)x", line)
if speed_match:
    speed = float(speed_match.group(1))
    remaining_seconds = (total_seconds - current_seconds) / speed
```

### renQoder 활용 예시

`encoder.py`의 `encode()` 메서드에서 실시간 진행률 파싱:
- `subprocess.Popen`으로 FFmpeg 프로세스 실행
- `stdout.readline()`으로 한 줄씩 읽기
- 정규식으로 `time=`, `speed=` 추출
- `progress_callback`으로 UI 업데이트

---

## 4. 파일 크기 추정 (renQoder 특화)

### Heuristic 모델

`encoder.py`의 `estimate_output_size()` 메서드 참조:

```python
# 비디오 크기 추정
pixels_per_frame = width * height
base_bpp = 0.1  # bits per pixel (품질에 따라 조정)
video_size = (pixels_per_frame * base_bpp * total_frames) / 8

# 오디오 크기
if audio_mode == "copy":
    audio_size = original_audio_size
else:  # AAC
    audio_size = (192000 * duration) / 8  # 192kbps
```

### 품질별 BPP (Bits Per Pixel)

- CQ/CRF 18: ~0.15 bpp (고품질)
- CQ/CRF 23: ~0.10 bpp (중간 품질)
- CQ/CRF 28: ~0.07 bpp (저품질)

---

## 5. 윈도우 환경 최적화

### CMD 창 숨김

```python
creationflags = 0x08000000 if os.name == 'nt' else 0

subprocess.Popen(
    cmd,
    creationflags=creationflags
)
```

### 경로 처리

- 백슬래시(`\`) 사용
- 공백 포함 경로는 자동으로 처리됨 (리스트 형식 명령어 사용 시)

---

## 참고 자료

- [FFmpeg 공식 문서](https://www.ffmpeg.org/ffmpeg.html)
- [ffprobe 공식 문서](https://www.ffmpeg.org/ffprobe.html)
- renQoder 프로젝트: `src/renqoder/encoder.py`

## 사용 예제

실제 사용 예제는 `examples/` 디렉토리를 참조하세요:
- `ffprobe_json_parsing.py`: ffprobe JSON 파싱 예제
- `progress_parsing.py`: 진행률 파싱 예제
- `command_building.md`: 다양한 인코딩 시나리오별 명령어 예제
