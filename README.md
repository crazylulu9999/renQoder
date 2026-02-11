# renQoder - Smart Video Transcoder

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-v0.4.0-blue.svg)

**"Smart Render, Slim Storage."**

고화질 비디오를 지능적으로 압축하는 비디오 트랜스코딩 툴입니다.

</div>

---

## ✨ 주요 기능 (0.4.0 버전)

- ✅ **자동 GPU 감지**: NVIDIA/AMD/Intel GPU를 자동으로 감지하여 최적의 하드웨어 인코더 선택
- ✅ **FFmpeg 환경 검사**: FFmpeg 설치 여부를 확인하고 미설치 시 다운로드 안내
- ✅ **광범위한 포맷 지원**: MP4, MKV 뿐만 아니라 TS, M2TS, WMV, FLV, WebM 등 다양한 비디오 포맷 지원
- ✅ **동영상 파일 검색 고도화**: Everything 연동 초고속 검색 및 지능형 메타데이터 분석 시스템 ✨
  - 드라이브 카드 UI로 직관적인 드라이브 선택 및 용량 정보 표시
  - 2단계 메타데이터 분석 (빠른 스캔 + 정밀 스캔)으로 미완성 녹화 파일도 정확히 감지
  - SHA-256 해시 기반 메타데이터 캐시 시스템으로 재검색 속도 향상
  - 컨텍스트 메뉴(우클릭)로 폴더 열기, 경로 복사, 캐시 재분석, 파일 삭제 등 지원
  - 키보드 단축키 및 더블클릭으로 빠른 워크플로우
- ✅ **필터링 및 정렬**: 검색 결과에서 코덱, 비트레이트, 크기 등으로 즉시 필터링 및 정렬 지원 ✨
- ✅ **탭 기반 UI**: 인코딩과 검색 기능을 분리하고 탭 스타일을 개선하여 명확한 워크플로우 제공 ✨
- ✅ **통합 메타데이터 엔진**: 검색과 인코딩 로직을 단일화하여 신뢰성 있는 정보 분석 (`metadata_utils.py`) ✨
- ✅ **비정상 파일 감지**: 손상된 인덱스나 부정확한 재생 시간을 가진 파일을 자동으로 감지하여 시각적 경고 표시 ✨
- ✅ **간편한 UI**: 파일 선택, 화질 조정, 원클릭 변환
- ✅ **스마트 파일명**: 코덱, 품질, 오디오 코덱 정보가 포함된 출력 파일명 자동 생성 (수정 가능)
- ✅ **오디오 코덱 감지**: 원본 비디오의 오디오 코덱을 자동 감지하여 파일명에 표시
- ✅ **FFmpeg 명령어 미리보기**: 실행될 명령어를 사전에 확인 가능
- ✅ **화질 설정 가이드**: CQ 값에 대한 직관적인 설명 제공
- ✅ **실시간 진행률 및 예상 남은 시간**: 인코딩 진행 퍼센트(%)와 예상 남은 시간을 START 버튼에 두 줄로 표시하여 직관성 극대화 ✨
- ✅ **인코딩 완료 알림**: Windows 10/11 Toast 알림으로 인코딩 완료 및 용량 절감 정보를 실시간으로 알림 ✨
- ✅ **지능형 용량 알림**: 예상 결과물 크기를 계산하여 드라이브 여유 공간 부족(125% 미만) 시 경고 표시 ✨
- ✅ **동적 테마**: 감지된 GPU에 따라 포인트 컬러 자동 변경
- ✅ **안전한 덮어쓰기**: 기존 파일을 영구 삭제하는 대신 시스템 휴지통으로 이동 (복구 가능)
- ✅ **버전 정보 표시**: 윈도우 타이틀에 현재 실행 중인 앱 버전을 표시하여 버전 확인 용이

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

빌드가 완료되면 `dist/renQoder-{version}.exe` 파일이 생성됩니다.

**주의**: 
- 생성된 `.exe` 파일은 단독으로 실행 가능하지만, **FFmpeg는 별도로 시스템에 설치**되어 있어야 합니다.
- FFmpeg를 시스템 PATH에 등록하거나, `renQoder.exe`와 같은 폴더에 `ffmpeg.exe`와 `ffprobe.exe`를 함께 배포하세요.

## 📁 프로젝트 구조

자세한 프로젝트 구조는 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)를 참조하세요.

```
renQoder/
├── src/renqoder/      # 소스 코드 (상세 구조는 PROJECT_STRUCTURE.md 참조)
├── scripts/           # 빌드/유틸리티 스크립트
├── dist/              # 빌드 결과물 (.exe)
└── docs/              # 각종 보고서 및 문서
```

## 🎮 지원 하드웨어

| GPU 제조사 | 인코더 | 최소 요구사항 |
|-----------|--------|--------------|
| NVIDIA | NVENC (hevc_nvenc) | GTX 10시리즈 (Pascal) 이상 |
| Intel | Quick Sync (hevc_qsv) | Skylake 이상 |
| AMD | AMF (hevc_amf) | GCN 4.0 이상 |
| CPU | libx265 | Fallback 옵션 |

## 📖 사용 방법

### 인코딩 탭
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
6. **START**: 변환 시작! 버튼 자체에서 실시간 진행률과 예상 남은 시간 확인 가능

### 검색 탭 ✨
1. **드라이브 선택**: 상단의 드라이브 카드에서 검색할 드라이브를 클릭합니다.
   - 💡 각 카드에는 드라이브 레이블, 용량, 사용률이 표시됩니다.
   - 마우스 휠 또는 드래그로 가로 스크롤이 가능합니다.
2. **검색 시작**: '🔍 검색 시작' 버튼을 클릭하여 동영상 파일을 검색합니다.
   - Everything이 설치되어 있으면 초고속 검색이 수행됩니다.
3. **메타데이터 로드**: 파일 목록이 나타나면 백그라운드에서 2단계 메타데이터 분석이 자동으로 수행됩니다.
   - **Stage 1 (빠른 스캔)**: 기본 정보(코덱, 해상도, FPS, 비트레이트) 추출
   - **Stage 2 (정밀 스캔)**: 재생시간이 0인 파일(미완성 녹화 등)에 대해 정밀 분석 수행
   - 💡 분석된 정보는 캐시에 저장되어 다음 검색 시 즉시 표시됩니다.
4. **필터링 및 정렬**:
   - 컨테이너, 최소 크기, 코덱, 비트레이트 필터를 사용하여 결과를 좁힐 수 있습니다.
   - **비정상 파일 필터**: 헤더 정보가 부정확하여 보정이 필요한 파일만 필터링하여 확인할 수 있습니다. ✨
   - 테이블 헤더를 클릭하여 파일명, 크기, 비트레이트 등으로 정렬합니다 (클릭할 때마다 오름/내림차순 전환).
   - 💡 **지능형 정렬**: 해상도는 픽셀 수 기준으로, 재생 시간은 실제 초 단위 기준으로 정렬되어 직관적입니다. ✨
5. **컨텍스트 메뉴 (우클릭)**:
   - **폴더 열기**: 파일이 있는 폴더를 탐색기로 엽니다.
   - **경로 복사**: 파일의 전체 경로를 클립보드에 복사합니다.
   - **파일명 복사**: 파일명만 클립보드에 복사합니다.
   - **캐시 재분석**: 해당 파일의 메타데이터를 다시 분석합니다.
   - **휴지통으로 삭제**: 파일을 휴지통으로 이동합니다 (복구 가능).
6. **키보드 단축키**:
   - **Home**: 첫 번째 항목으로 이동
   - **End**: 마지막 항목으로 이동
   - **더블클릭**: 선택한 파일을 인코딩 탭으로 전송
7. **인코딩 전송**: 파일을 선택하고 '➡️ 선택한 파일을 인코딩 탭으로 보내기'를 클릭하거나 더블클릭하면 즉시 인코딩 설정이 시작됩니다.

## 🛠️ 기술 스택

- **Language**: Python 3.10+
- **GUI**: CustomTkinter (Tkinter based, MIT License)
- **Encoder**: FFmpeg
- **Hardware Detection**: Windows wmic

## 📋 로드맵

- [x] v0.1: Initial PoC Release
- [x] v0.2: Feature enhancement & UI improvement
- [x] v0.3: 남은 시간 표시, UI 레이아웃 최적화, 입력 필터 확장 및 빌드 자동화
- [x] v0.4: 메타데이터 분석 엔진 통합, 비정상 파일 감지/필터링 및 정렬 시스템 고도화 ✨
- [ ] v0.5: 배치 처리, 드래그 앤 드롭
- [ ] v1.0: 설정 저장, macOS 지원
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
