# renQoder PoC 빌드 개선 보고서 v15

## 📅 업데이트 일자
2026-02-07 (15차 개선)

## 🎯 개선 목표
- FFmpeg, ffprobe, wmic 등 백그라운드 프로세스가 실행될 때마다 잠깐씩 나타났다 사라지는 시커먼 CMD 창(콘솔 창)을 완전히 제거하여 사용자 경험을 개선합니다.

---

## ✨ 주요 개선 사항

### 1. 백그라운드 프로세스 창 숨김 처리 (CREATE_NO_WINDOW)
Windows 환경에서 서브프로세스를 생성할 때, 운영체제 수준에서 창을 만들지 않도록 강제하는 플래그를 적용했습니다.

- **적용 대상**:
    - **FFmpeg**: 인코딩 시작 시 나타나던 창 제거.
    - **ffprobe**: 파일 선택 시 비디오/오디오 정보를 분석할 때 나타나던 창 제거.
    - **wmic**: 프로그램 시작 시 GPU를 감지할 때 나타나던 창 제거.
- **기술적 구현**: `subprocess.run` 및 `subprocess.Popen` 호출 시 `creationflags=0x08000000` (CREATE_NO_WINDOW) 옵션을 적용했습니다. (Windows 전용)

---

## 📝 코드 변경 사항

### 1. `src/renqoder/encoder.py`
- `get_audio_info`, `get_video_info`, `encode` 메서드의 모든 서브프로세스 호출부에 `creationflags` 적용 로직 추가.

### 2. `src/renqoder/hardware_detector.py`
- `_detect_gpu_windows` 및 `check_ffmpeg` 함수에 `creationflags` 적용 및 `os` 모듈 임포트 추가.

---

## 🧪 테스트 결과

- **파일 선택 테스트**: 영상을 마우스로 선택할 때마다 뜨던 ffprobe 창이 더 이상 보이지 않고 조용히 데이터만 불러옵니다. ✅
- **변환 시작 테스트**: "START" 버튼 클릭 시 FFmpeg 창이 뜨지 않으며, UI 상의 로그창과 진행바만 정상적으로 작동합니다. ✅
- **안정성 확인**: 창만 숨겨졌을 뿐, 모든 프로세스는 백그라운드에서 정상적으로 데이터 통신을 수행합니다. ✅

---

## 🎉 결론

이번 15차 개선을 통해 **renQoder**는 더욱 깔끔하고 전문적인 소프트웨어의 면모를 갖추게 되었습니다. 이제 작업 도중 불필요한 콘솔 창 방해 없이 쾌적하게 비디오 변환을 즐기실 수 있습니다! 🚀
