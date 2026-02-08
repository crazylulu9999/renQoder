# Testing & Verification Rules (테스트 및 검증 규칙)

기능 개발 단계에서 작성하는 모든 검증용 스크립트 및 테스트 코드는 프로젝트의 루트 디렉토리가 아닌 `tests` 폴더 하위에 생성해야 합니다.

## 1. Verification Scripts (검증 스크립트)
- **위치 (Placement)**: 기능 구현 중 동작 확인이나 버그 재현을 위해 작성하는 임시/검증용 스크립트는 반드시 `tests` 폴더 또는 그 하위 폴더에 보관합니다.
- **루트 디렉토리 정리 (Maintain Clean Root)**: 루트 디렉토리에는 프로젝트의 메인 설정 파일, 빌드 스크립트, 핵심 문서만 남겨두고, 실행 가능한 개별 스크립트는 `tests` 또는 `scripts` 폴더로 분리합니다.
- **예시 (Examples)**:
  - `tests\check_file_access.py`
  - `tests\diagnose_ffprobe.py`

## 2. Test Execution (테스트 실행)
- 모든 테스트 및 검증 스크립트는 루트 디렉토리에서 모듈 경로를 유지한 상태로 실행될 수 있도록 환경을 구성합니다.
