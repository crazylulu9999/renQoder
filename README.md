# renQoder - Smart Video Transcoder

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-PoC-yellow.svg)

**"Smart Render, Slim Storage."**

고화질 비디오를 지능적으로 압축하는 비디오 트랜스코딩 툴입니다.

</div>

---

## ✨ 주요 기능 (PoC 버전)

- ✅ **자동 GPU 감지**: NVIDIA/AMD/Intel GPU를 자동으로 감지하여 최적의 하드웨어 인코더 선택
- ✅ **FFmpeg 환경 검사**: FFmpeg 설치 여부를 확인하고 미설치 시 다운로드 안내
- ✅ **광범위한 포맷 지원**: MP4, MKV 뿐만 아니라 TS, M2TS, WMV, FLV, WebM 등 다양한 비디오 포맷 지원
- ✅ **간편한 UI**: 파일 선택, 화질 조정, 원클릭 변환
- ✅ **스마트 파일명**: 코덱, 품질, 오디오 코덱 정보가 포함된 출력 파일명 자동 생성 (수정 가능)
- ✅ **오디오 코덱 감지**: 원본 비디오의 오디오 코덱을 자동 감지하여 파일명에 표시
- ✅ **FFmpeg 명령어 미리보기**: 실행될 명령어를 사전에 확인 가능
- ✅ **화질 설정 가이드**: CQ 값에 대한 직관적인 설명 제공
- ✅ **실시간 진행률**: 인코딩 진행 상황을 실시간으로 확인
- ✅ **동적 테마**: 감지된 GPU에 따라 포인트 컬러 자동 변경
- ✅ **안전한 덮어쓰기**: 기존 파일을 영구 삭제하는 대신 시스템 휴지통으로 이동 (복구 가능)

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.10 이상
- FFmpeg (시스템 PATH에 등록되어 있어야 함)
- Windows OS (현재 버전)

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/renQoder.git
cd renQoder

# 의존성 설치
pip install -r requirements.txt
```

### 3. 실행

```bash
# 개발 모드
python run.py

# 또는 직접 실행
python src\renqoder\main.py
```

### 4. Standalone 실행파일 빌드 (선택사항)

단일 `.exe` 파일로 배포하려면:

```bash
# 실행파일 빌드
python scripts\build_exe.py

# 빌드 파일 정리
python scripts\build_exe.py --clean
```

빌드가 완료되면 `dist/renQoder.exe` 파일이 생성됩니다.

**주의**: 
- 생성된 `.exe` 파일은 단독으로 실행 가능하지만, **FFmpeg는 별도로 시스템에 설치**되어 있어야 합니다.
- FFmpeg를 시스템 PATH에 등록하거나, `renQoder.exe`와 같은 폴더에 `ffmpeg.exe`와 `ffprobe.exe`를 함께 배포하세요.

## 📁 프로젝트 구조

자세한 프로젝트 구조는 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)를 참조하세요.

```
renQoder/
├── src/renqoder/      # 소스 코드
├── docs/              # 문서
├── tests/             # 테스트
├── scripts/           # 빌드 스크립트
└── dist/              # 빌드 결과물
```

## 🎮 지원 하드웨어

| GPU 제조사 | 인코더 | 최소 요구사항 |
|-----------|--------|--------------|
| NVIDIA | NVENC (hevc_nvenc) | GTX 10시리즈 (Pascal) 이상 |
| Intel | Quick Sync (hevc_qsv) | Skylake 이상 |
| AMD | AMF (hevc_amf) | GCN 4.0 이상 |
| CPU | libx265 | Fallback 옵션 |

## 📖 사용 방법

1. **파일 선택**: "파일 선택" 버튼을 클릭하여 변환할 비디오 파일 선택
2. **화질 조정**: 슬라이더로 원하는 화질 설정 (기본값 23 권장)
   - 💡 CQ 값이 낮을수록 고화질/대용량, 높을수록 저화질/저용량
   - 18-20: 초고화질 | 23: 균형 (권장) | 28-30: 저용량
3. **오디오 모드**: 원본 유지(Copy) 또는 AAC 변환 선택
4. **출력 파일명**: 자동 생성된 파일명 확인 (필요시 "수정" 버튼으로 변경 가능)
   - 기본 형식: `원본파일명_코덱_CQ품질_오디오정보.mp4`
   - 예시 (원본 유지): `gameplay_NVENC_CQ23_AAC.mp4` (원본 오디오가 AAC)
   - 예시 (원본 유지): `gameplay_NVENC_CQ23_AC3.mp4` (원본 오디오가 AC3)
   - 예시 (AAC 변환): `gameplay_NVENC_CQ23_AAC192k.mp4` (AAC 192kbps 변환)
5. **FFmpeg 명령어 확인**: 실행될 명령어를 미리보기 창에서 확인
6. **START**: 변환 시작!

## 🛠️ 기술 스택

- **Language**: Python 3.10+
- **GUI**: CustomTkinter (Tkinter based, MIT License)
- **Encoder**: FFmpeg
- **Hardware Detection**: Windows wmic

## 📋 로드맵

- [x] v0.1: Initial PoC Release
- [x] v0.2: Feature enhancement & UI improvement
- [x] v0.3: Mandatory MP4 encoding enforcement
- [ ] v0.5: 배치 처리, 드래그 앤 드롭
- [ ] v1.0: 예상 용량 계산, 설정 저장, macOS 지원
- [ ] v1.5: Linux 지원, 크로스 플랫폼 빌드
- [ ] v2.0: Watch Folder, 멀티 GPU

## 🤖 AI 기여 (AI Acknowledgements)

이 프로젝트의 개발 과정에는 AI 기술이 활용되었습니다.

- **코드 및 아키텍처**: 전체적인 프로젝트 설계 및 코드 구현 과정에서 AI의 도움을 받았습니다.
- **아이콘 및 디자인**: 프로젝트의 아이콘 이미지는 AI 생성 도구를 사용하여 제작되었습니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트 관련 문의사항은 GitHub Issues를 이용해주세요.

---

<div align="center">

Made with ❤️ by renQoder Team

</div>
