**renQoder** 개발 및 배포를 위한 **제품 기획서(Product Requirement Document, PRD)** 개선안입니다.
이 기획서는 다양한 하드웨어 환경을 지원하고, 사용자에게 최적의 인코딩 경험을 제공하는 것을 목표로 합니다.

---

# 📄 프로젝트 기획서: renQoder

## 1. 프로젝트 개요 (Project Overview)

* **제품명:** renQoder (렌코더)
* **슬로건:** "Smart Render, Slim Storage."
* **정의:** 사용자의 하드웨어(GPU)를 자동으로 감지하여 가장 효율적인 코덱으로 고화질 비디오를 압축하는 지능형 트랜스코딩 툴.
* **개발 목표:** 복잡한 설정 없이도 사용자의 PC 성능을 최대로 활용하여 '시각적 무손실' 압축을 수행하고 스토리지 공간을 극대화한다.

## 2. 기획 배경 및 문제 정의 (Background & Problem)

1. **스토리지의 압박:** 고화질 비디오를 '무손실에 가까운 품질(CQP 15~16)'로 녹화할 경우, 시간당 수십 GB의 파일이 생성됨.
2. **하드웨어 파편화:** 사용자의 그래픽카드(NVIDIA, AMD, Intel)마다 최적의 하드웨어 가속 코덱이 다르지만, 일반 사용자는 이를 구분하여 설정하기 어려움.
3. **기존 툴의 한계:** 
    * **HandBrake:** 초보자가 사용하기엔 옵션이 너무 방대함.
    * **FFmpeg (CLI):** GPU별 코덱 이름(`hevc_nvenc`, `hevc_amf`, `hevc_qsv`)을 직접 알아야 하며 명령어가 복잡함.

## 3. 핵심 타겟 (Target Audience)

* **게이머 & 스트리머:** 영상 보관을 위해 고효율 압축이 필요한 사용자.
* **크리에이터:** 편집 시스템의 용량 확보가 절실한 사용자.
* **범용 사용자:** 하드웨어 가속(NVIDIA Pascal 이상, AMD GCN 4.0 이상, Intel Skylake 이상)이 가능한 PC 보유자.

## 4. 핵심 기능 명세 (Functional Specifications)

### A. 하드웨어 지능형 감지 (Intelligent Hardware Detection)
* **GPU 스캐닝:** 실행 시 시스템의 GPU 제조사를 확인하여 사용 가능한 최적의 하드웨어 인코더를 자동으로 선택.
    * **NVIDIA:** `hevc_nvenc` (1순위)
    * **Intel:** `hevc_qsv` (2순위)
    * **AMD:** `hevc_amf` (3순위)
    * **Fallback:** 하드웨어 가속 불가 시 `libx265` (CPU) 사용 안내 및 제안.

### B. 인코딩 엔진 (Core Engine)
* **코덱:** H.265 (HEVC) 기반 하드웨어 가속.
* **품질 제어:** CQP (Constant Quantization Parameter) 또는 이에 준하는 가변 비트레이트 방식 적용.
* **최적화 프리셋:** 각 GPU 제조사별 '고품질/저지연' 프리셋 자동 매핑 (예: NVENC의 `p7`, QSV의 `veryslow`).
* **호환성:** 애플 기기 및 범용 플레이어 호환성을 위한 `hvc1` 태그 기본 적용.

### C. 사용자 설정 (User Interface)
* **화질 슬라이더 (Quality Slider):**
    * 범위: 18 (초고화질) ~ 30 (저용량)
    * 기본값: **20** (권장)
* **오디오 모드 (Audio Selector):**
    * **Mode 1 (Copy):** 원본 오디오 유지 (무손실 스트림 복사). MKV 컨테이너 권장.
    * **Mode 2 (AAC):** 192kbps 변환. MP4 컨테이너 호환성 강조.

### D. 출력 (Output)
* **파일명 규칙:** `{원본명}_renQoder.{확장자}`
* **실시간 모니터링:** 진행률, 현재 프레임 속도(FPS), 예상 완료 시간 표시.

### E. 환경 검사 (Environment Check)
* **FFmpeg 감지:** 프로그램 시작 시 시스템 경로(PATH)에서 FFmpeg 실행 파일 존재 여부를 확인.
* **미설치 시 대응:** FFmpeg가 감지되지 않을 경우, 사용자에게 안내 메시지(다이얼로그)를 표시하고 공식 다운로드 페이지 방문을 유도.
    * **권장 링크:** [FFmpeg 공식 다운로드 페이지](https://www.ffmpeg.org/download.html)

### F. 배포 및 설치 (Distribution)
* **Standalone Executable:** 사용자가 파이썬 환경을 구축할 필요 없이 즉시 실행할 수 있도록 단일 실행파일(`.exe`) 형태로 배포.
* **빌드 시스템:** PyInstaller를 활용한 빌드 자동화 (`build_exe.py`).
* **패키징 전략:**
    * GUI 리소스 및 의존성 라이브러리를 포함한 단일 바이너리 제공.
    * 외부 의존성(FFmpeg)의 경우 시스템 PATH 감지 및 로컬 폴더 참조 우선순위 정립.

## 5. UI/UX 디자인 가이드

* **테마:** **Modern Dark & Dynamic Color**
* **컬러 시스템:**
    * **Accent:** 감지된 GPU에 따라 포인트 컬러 변경 (NVIDIA: Green, Intel: Blue, AMD: Red).
    * **Base:** Deep Charcoal (`#1E1E1E`).
* **레이아웃:** 원클릭 워크플로우를 지향하는 심플한 대시보드 형태.

## 6. 기술 스택 (Tech Stack)

* **Language:** Python 3.10+
* **GUI Framework:** CustomTkinter (MIT License, Tkinter-based Modern UI)
* **Process Management:** `subprocess`를 통한 FFmpeg 파이프라인 제어.
* **Hardware Info:** `pyadl` (AMD), `pynvml` (NVIDIA) 또는 FFmpeg 자체 하드웨어 가속 목록 쿼리.

## 7. 개발 로드맵 (Roadmap)

| 단계 | 버전 | 목표 기능 | 상태 |
| --- | --- | --- | --- |
| **1단계** | **v0.1** | 기본 NVENC 구현 및 MVP 검증 | **완료** |
| **2단계** | **v0.5** | **GPU 자동 감지 엔진**, 하드웨어별 코덱 분기 처리, QSS 테마 적용 | **완료** |
| **3단계** | **v0.8** | **Standalone 실행파일(.exe)** 배포 자동화, 빌드 스크립트 고도화 | **진행 중** |
| **4단계** | **v1.0** | 배치(Batch) 인코딩, 드래그 앤 드롭, 예상 절감 용량 계산기 | 계획 |
| **5단계** | **v1.x** | 멀티 GPU 지원, Watch Folder(자동 감시) 기능 | 계획 |

## 9. AI 활용 (AI Usage)

본 프로젝트는 최신 AI 기술을 적극적으로 활용하여 개발되었습니다.

*   **개발 보조:** 코드 아키텍처 설계, 로직 구현 및 리팩토링 과정에서 AI 코딩 어시스턴트의 지원을 받았습니다.
*   **리소스 제작:** 애플리케이션의 공식 아이콘 및 그래픽 리소스는 AI 생성 도구를 기반으로 제작되었습니다.

---

## 8. 예상 시나리오 (User Story)

> "인텔 내장 그래픽과 라데온 그래픽카드를 사용하는 사용자 박씨는 renQoder를 실행한다.
> 프로그램은 'AMD Radeon GPU 감지됨 - HEVC_AMF 인코더 활성화' 메시지를 띄운다.
> 박씨는 복잡한 인코딩 설정 없이 슬라이더만 '고화질' 쪽으로 옮기고 'START'를 누른다.
> 하드웨어 가속을 통해 CPU 점유율은 낮게 유지되면서, 30GB의 영상이 8GB로 마법처럼 줄어든다."

