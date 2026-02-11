# renQoder PoC 빌드 개선 보고서 v6

## 📅 업데이트 일자
2026-02-07 (6차 개선)

## 🎯 개선 목표
FFmpeg 명령어 미리보기의 가독성을 높이기 위해, 실무에서 사용하는 다중 행(Multiple Lines) 포맷으로 변경합니다.

---

## ✨ 주요 개선 사항

### 1. FFmpeg 명령어 다중 행 포맷팅

#### 변경 내용
기존의 한 줄로 길게 나열되던 명령어를 Windows CLI 스타일의 줄바꿈 포맷(`^`)으로 변경하였습니다.

**Before (Single Line):**
```bash
ffmpeg -i "C:\Videos\input.mp4" -c:v hevc_nvenc -preset p7 -cq 23 -c:a copy -tag:v hvc1 -progress pipe:1 "C:\Videos\input_NVENC_CQ23_AAC.mkv"
```

**After (Multi-line with ^):**
```bash
ffmpeg ^
    -i "C:\Videos\input.mp4" ^
    -c:v hevc_nvenc ^
    -preset p7 ^
    -cq 23 ^
    -c:a copy ^
    -tag:v hvc1 ^
    "C:\Videos\input_NVENC_CQ23_AAC.mkv"
```

#### 세부 개선 사항
- **가독성 특화**: `-i`, `-c:v`, `-preset` 등 주요 옵션마다 줄바꿈을 적용하여 한눈에 파악하기 쉽게 구현했습니다.
- **불필요한 옵션 제거**: 내부적으로 사용되는 `-progress pipe:1`과 같은 옵션은 미리보기에서 제외하여 핵심 명령어에만 집중할 수 있게 했습니다.
- **자동 따옴표 처리**: 경로에 공백이 있거나 특수문자가 포함된 경우 자동으로 따옴표(`"`)를 추가하여 실제 CLI에서 바로 복사하여 사용할 수 있도록 했습니다.

### 2. UI 레이아웃 최적화

#### 변경 내용
다중 행 명령어가 잘리지 않고 한눈에 들어올 수 있도록 미리보기 창의 높이를 조정했습니다.

- **변경 전**: 고정된 낮은 높이 (80px)
- **변경 후**: 최소 120px 이상의 높이 확보 및 내용에 따른 가독성 개선

---

## 📝 코드 변경 사항

### 1. `src/renqoder/encoder.py` - `get_command_preview` 메서드
- 명령어 리스트를 순회하며 주요 플래그와 값을 쌍으로 묶어 줄바꿈과 들여쓰기를 적용하는 로직 구현.
- `-progress` 관련 옵션 필터링 로직 추가.
- 경로 포함 인자에 대한 자동 따옴표(`"`) 처리 추가.

### 2. `src/renqoder/main.py` - UI 초기화
- `ffmpeg_preview` (QTextEdit)의 `maximumHeight(80)` 설정을 `setMinimumHeight(120)`로 변경하여 확장성 확보.

---

## 🧪 테스트 결과

- `tests/test_filename.py` 실행 결과:
  - NVENC, QSV, AMF 모든 인코더 타입에 대해 다중 행 포맷팅이 정상적으로 동작함을 확인.
  - 파일 경로에 따옴표가 정상적으로 붙는 것을 확인.

---

## 💡 사용자 혜택

1. **명령어 분석 용이**: 어떤 옵션이 적용되었는지 행별로 구분되어 즉시 파악 가능.
2. **복사 및 활용**: 미리보기 창의 내용을 그대로 복사하여 CMD 또는 PowerShell에서 즉시 실행 가능한 형태로 제공.
3. **투명성**: 프로그램이 내부적으로 어떤 작업을 수행하는지 더 명확하게 시각화.

---

## 🎉 결론

이번 개선으로 **renQoder**는 전문적인 인코딩 툴로서의 시각적 명확성을 한층 더 강화했습니다. 사용자는 이제 복잡한 FFmpeg 옵션들을 훨씬 편안하게 검토하고 신뢰할 수 있습니다. 🚀
