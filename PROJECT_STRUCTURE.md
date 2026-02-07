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
│       ├── main.py            # GUI 메인 애플리케이션
│       ├── encoder.py         # 비디오 인코딩 모듈
│       └── hardware_detector.py  # GPU 감지 모듈
│
├── docs/                      # 문서
│   ├── DESIGN.md              # 제품 기획서
│   ├── POC_REPORT.md          # PoC 개발 보고서
│   └── IMPROVEMENT_REPORT.md  # 개선 사항 보고서
│
├── tests/                     # 테스트
│   └── test_filename.py       # 파일명 생성 테스트
│
├── scripts/                   # 빌드/유틸리티 스크립트
│   └── build_exe.py           # Standalone 빌드 스크립트
│
├── dist/                      # 빌드 결과물
│   └── renQoder.exe           # 실행 파일 (빌드 후 생성)
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
