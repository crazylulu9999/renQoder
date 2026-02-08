# Documentation & Versioning Rules (문서화 및 버전 관리 규칙)

이 문서는 프로젝트의 문서 업데이트 및 버전 번호 관리 시 준수해야 할 규칙을 정의합니다.

## 1. Single Source of Truth for Version (버전 정보의 단일 출처)
- **Version Definition**: 프로젝트의 현재 버전은 반드시 `src\renqoder\__init__.py` 파일의 `__version__` 변수에 정의된 값을 기준으로 합니다.
- **Verification**: 모든 문서(README.md, CHANGELOG.md 등)를 업데이트할 때는 반드시 `src\renqoder\__init__.py`의 버전을 먼저 확인하고 일치시켜야 합니다.

## 2. Documentation Synchronization (문서 동기화)
- **README.md**:
    - `## ✨ 주요 기능 (PoC 버전)` 섹션 옆이나 로드맵 등에서 버전을 언급할 때 현재 버전과 일치하는지 확인합니다.
    - 로드맵(`${v0.3}` 등)의 체크박스 상태를 코드 구현 상태와 동기화합니다.
- **CHANGELOG.md**:
    - 새로운 기능을 추가하거나 버그를 수정한 경우, `src\renqoder\__init__.py`의 버전에 해당하는 섹션에 내용을 기록합니다.
    - `[Unreleased]` 섹션에 있던 내용이 릴리즈된 경우, 해당 버전 섹션으로 이동시키고 날짜를 기입합니다.
    - 하단의 `Version History` 섹션에도 동일한 버전을 추가하여 일관성을 유지합니다.

## 3. Version Update Flow (버전 업데이트 절차)
1. 기능 구현 또는 버그 수정 완료.
2. `src\renqoder\__init__.py`에서 `__version__` 값을 업데이트 (필요 시).
3. 업데이트된 버전을 바탕으로 `CHANGELOG.md` 작성.
4. `README.md`의 주요 기능 및 로드맵 업데이트.
5. 버전 번호가 포함된 모든 참조가 최신 상태인지 최종 확인.

## 4. Automation Consideration (자동화 고려)
- CLI 또는 스크립트를 통해 버전을 확인할 때는 다음 명령어를 활용할 수 있습니다:
  - `python -c "import sys; sys.path.append('src'); from renqoder import __version__; print(__version__)"`
  - 또는 단순 파일 읽기: `type src\renqoder\__init__.py | findstr "__version__"`
