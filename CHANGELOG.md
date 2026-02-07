# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-07

### Added
- 🎉 **Initial PoC Release**
- ✅ 자동 GPU 감지 (NVIDIA/AMD/Intel)
- ✅ 최적 하드웨어 인코더 자동 선택 (NVENC/QSV/AMF)
- ✅ FFmpeg 설치 확인 및 다운로드 안내
- ✅ **CustomTkinter 기반 모던 다크 테마 GUI (MIT 라이선스)**
- ✅ 화질 조정 슬라이더 (CQ 18-35)
- ✅ 오디오 모드 선택 (Copy/AAC)
- ✅ 스마트 출력 파일명 자동 생성 (코덱, 품질, 오디오 코덱 정보 포함)
- ✅ 오디오 코덱 자동 감지 및 실시간 반영
- ✅ FFmpeg 명령어 미리보기 및 **"한 줄로 복사"** 기능 ✨
- ✅ **SCTE-35 방송 트랙** 대응 (-map 0:v -map 0:a 강제) ✨
- ✅ 백그라운드 인코딩 프로세스 (threading 사용) ✨
- ✅ **인코딩 진행률 및 퍼센트(%) 실시간 표시** ✨
- ✅ 드라이브 남은 용량 실시간 표시 (출력 경로 기준) ✨
- ✅ 마지막 윈도우 위치 및 크기 기억/복원 기능 ✨
- ✅ 윈도우 오프스크린 폴백 처리 (모니터 구성 변경 대응) ✨
- ✅ 마지막 사용 폴더 기억 기능
- ✅ 출력 파일명 수동 수정 기능
- ✅ PyInstaller 기반 Standalone 빌드 지원
- 📁 체계적인 프로젝트 구조 및 문서화
- 🤖 **AI 기여 및 아이콘 제작 명시 추가** (README.md)

### Fixed
- ✅ 오디오 코덱 자동 감지 오류 수정
- ✅ 리소스 경로 인식 로직 개선 (Standalone 대응)
- ✅ 재생 시간 및 FPS 감지 신뢰도 향상

### Technical Details
- **Language**: Python 3.10+
- **GUI Framework**: CustomTkinter (MIT)
- **Video Encoder**: FFmpeg
- **Hardware Detection**: Windows wmic
- **Build Tool**: PyInstaller

### Known Limitations
- Windows 전용 (현재 버전)
- FFmpeg 별도 설치 필요
- 단일 파일 처리만 지원 (배치 처리 미지원)

---

## [Unreleased]

### Planned for v0.5
- [ ] 배치 처리 기능
- [ ] 드래그 앤 드롭 지원

### Planned for v1.0
- [ ] 예상 파일 크기 계산
- [ ] 설정 저장/불러오기
- [ ] macOS 지원
- [ ] 프리셋 시스템

### Planned for v1.5
- [ ] Linux 지원
- [ ] 크로스 플랫폼 빌드 시스템

### Planned for v2.0
- [ ] Watch Folder 기능
- [ ] 멀티 GPU 지원

---

## Version History

- **v0.1.0** (2026-02-07): Initial PoC Release
