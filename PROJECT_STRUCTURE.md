# 프로젝트 구조

```
renQoder/
├── README.md                  # 프로젝트 설명서
├── requirements.txt           # Python 의존성
├── run.py                     # 실행 진입점
├── .gitignore                 # Git 무시 파일
│
├── src/                       # 소스 코드
│   └── renqoder/              # 메인 패키지
│       ├── __init__.py        # 패키지 초기화
│       ├── main.py            # GUI 메인 애플리케이션 (탭 기반 UI)
│       ├── encoder.py         # 비디오 인코딩 핵심 로직
│       ├── searcher.py        # Everything 연동 동영상 검색 모듈 ✨
│       ├── notification.py    # Windows Toast 알림 모듈
│       ├── taskbar.py         # 작업표시줄 진행률 표시 모듈 (Windows)
│       └── hardware_detector.py # GPU 감지 및 가속기 선택 모듈
│
├── scripts/                   # 빌드/유틸리티 스크립트
│   └── build_exe.py           # Standalone 빌드 스크립트
│
├── dist/                      # 빌드 결과물
│   └── renQoder-v{version}.exe  # 실행 파일 (빌드 후 생성)
│
└── build/                     # 빌드 임시 파일 (자동 생성)
```

## 실행 방법

### 개발 모드
```bash
# 프로젝트 루트에서
python run.py
```

### Standalone 빌드
```bash
# 빌드
python scripts\build_exe.py

# 빌드 파일 정리
python scripts\build_exe.py --clean
```
