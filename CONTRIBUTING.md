# Contributing to renQoder

renQoder에 기여해주셔서 감사합니다! 🎉

## 기여 방법

### 버그 리포트

버그를 발견하셨나요? 다음 정보를 포함하여 Issue를 생성해주세요:

- **버그 설명**: 무엇이 잘못되었나요?
- **재현 방법**: 어떻게 하면 버그를 재현할 수 있나요?
- **예상 동작**: 어떻게 동작해야 하나요?
- **환경 정보**:
  - OS 버전
  - Python 버전
  - GPU 모델
  - FFmpeg 버전

### 기능 제안

새로운 기능을 제안하고 싶으신가요?

1. 먼저 Issue를 생성하여 제안 내용을 공유해주세요
2. 커뮤니티의 피드백을 받아보세요
3. 승인되면 구현을 시작하세요!

### Pull Request 프로세스

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/renQoder.git
   cd renQoder
   ```

2. **브랜치 생성**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **개발 환경 설정**
   ```bash
   pip install -r requirements.txt
   ```

4. **코드 작성**
   - 기존 코드 스타일을 따라주세요
   - 주석을 명확하게 작성해주세요
   - 가능하면 테스트를 추가해주세요

5. **테스트**
   ```bash
   # 애플리케이션 실행 테스트
   python run.py
   
   # 테스트 스크립트 실행
   python tests\test_filename.py
   ```

6. **커밋**
   ```bash
   git add .
   git commit -m "Add: 새로운 기능 설명"
   ```
   
   커밋 메시지 규칙:
   - `Add:` - 새로운 기능 추가
   - `Fix:` - 버그 수정
   - `Update:` - 기존 기능 개선
   - `Refactor:` - 코드 리팩토링
   - `Docs:` - 문서 수정

7. **Push & PR**
   ```bash
   git push origin feature/amazing-feature
   ```
   
   GitHub에서 Pull Request를 생성해주세요.

## 코드 스타일

- **Python**: PEP 8 스타일 가이드를 따릅니다
- **들여쓰기**: 스페이스 4칸
- **문자열**: 작은따옴표(`'`) 사용
- **주석**: 한글로 명확하게 작성

## 프로젝트 구조

```
renQoder/
├── src/renqoder/      # 메인 소스 코드
│   ├── main.py        # GUI 메인 애플리케이션
│   ├── encoder.py     # 비디오 인코딩 로직
│   └── hardware_detector.py  # GPU 감지 로직
├── docs/              # 문서
├── tests/             # 테스트
└── scripts/           # 빌드 스크립트
```

## 개발 팁

### 로컬 테스트

```bash
# 캐시 없이 실행 (권장)
python -B run.py

# 빌드 테스트
python scripts\build_exe.py
```

### 디버깅

- `main.py`의 `log()` 메서드를 활용하세요
- GUI 하단의 로그 창에서 실시간으로 확인 가능합니다

## 질문이 있으신가요?

- GitHub Issues에 질문을 남겨주세요
- 기존 Issues와 Pull Requests를 먼저 확인해보세요

## 행동 강령

- 서로를 존중해주세요
- 건설적인 피드백을 제공해주세요
- 다양성을 환영합니다

---

다시 한번 기여해주셔서 감사합니다! 🙏
