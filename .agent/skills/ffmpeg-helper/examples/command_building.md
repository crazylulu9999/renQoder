# FFmpeg 명령어 구성 예제

이 문서는 다양한 인코딩 시나리오별로 FFmpeg 명령어를 구성하는 방법을 보여줍니다.

## 기본 구조

```bash
ffmpeg [전역 옵션] -i [입력 파일] [입력 옵션] [출력 옵션] [출력 파일]
```

---

## 시나리오 1: HEVC 인코딩 (NVIDIA GPU)

### 고품질 (CQ 18)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_nvenc -preset p7 -cq 18 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

### 중간 품질 (CQ 23)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

### 저품질 (CQ 28)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_nvenc -preset p7 -cq 28 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

---

## 시나리오 2: HEVC 인코딩 (Intel QSV)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_qsv -preset veryslow -global_quality 23 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

---

## 시나리오 3: HEVC 인코딩 (AMD AMF)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_amf -quality quality -qp_i 23 -qp_p 23 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

---

## 시나리오 4: HEVC 인코딩 (소프트웨어 - libx265)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v libx265 -preset slow -crf 23 \
  -c:a copy \
  -tag:v hvc1 \
  output.mp4
```

---

## 시나리오 5: 오디오 재인코딩 (AAC)

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v -map 0:a \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a aac -b:a 192k \
  -tag:v hvc1 \
  output.mp4
```

---

## 시나리오 6: 특정 스트림만 선택

### 첫 번째 비디오 스트림과 두 번째 오디오 스트림만

```bash
ffmpeg -hide_banner -i input.mp4 \
  -map 0:v:0 -map 0:a:1 \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

---

## 시나리오 7: 해상도 변경 (스케일링)

### 1080p로 다운스케일

```bash
ffmpeg -hide_banner -i input.mp4 \
  -vf "scale=1920:1080" \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

### 720p로 다운스케일

```bash
ffmpeg -hide_banner -i input.mp4 \
  -vf "scale=1280:720" \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

---

## 시나리오 8: 프레임레이트 변경

### 30fps로 변경

```bash
ffmpeg -hide_banner -i input.mp4 \
  -r 30 \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

---

## 시나리오 9: 특정 구간만 추출

### 10초부터 30초까지 (20초 분량)

```bash
ffmpeg -hide_banner -ss 00:00:10 -i input.mp4 -t 00:00:20 \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

---

## 시나리오 10: 덮어쓰기 모드

### 출력 파일이 이미 존재해도 강제로 덮어쓰기

```bash
ffmpeg -hide_banner -y -i input.mp4 \
  -c:v hevc_nvenc -preset p7 -cq 23 \
  -c:a copy \
  output.mp4
```

---

## renQoder 프로젝트에서 사용하는 패턴

renQoder의 `encoder.py`에서 `build_command()` 메서드는 다음과 같은 구조로 명령어를 생성합니다:

```python
cmd = ['ffmpeg', '-hide_banner']
if overwrite:
    cmd.append('-y')

cmd.extend(['-i', input_file, '-map', '0:v', '-map', '0:a'])

# 비디오 인코더 설정
cmd.extend(['-c:v', self.encoder_type])

# 품질 설정 (코덱별로 다름)
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

cmd.append(output_file)
```

---

## 참고 사항

### 품질 값 가이드

- **CQ/CRF 18**: 매우 고품질 (파일 크기 큼)
- **CQ/CRF 23**: 중간 품질 (권장)
- **CQ/CRF 28**: 저품질 (파일 크기 작음)

### 프리셋 가이드

- **NVENC**: `p1` (빠름) ~ `p7` (느림, 고품질)
- **QSV**: `veryfast` ~ `veryslow`
- **libx265**: `ultrafast` ~ `veryslow`

### 오디오 비트레이트 가이드

- **128k**: 저품질
- **192k**: 중간 품질 (권장)
- **256k**: 고품질
