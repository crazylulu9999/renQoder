---
description: staged된 변경 사항을 분석하여 Conventional Commits 스타일의 커밋 메시지를 추천합니다.
---

# Git staged 커밋 메시지 추천 워크플로우 (Windows 11 최적화)

이 워크플로우는 윈도우 11의 PowerShell 환경을 활용하여 staged된 변경 사항을 가장 빠르고 정확하게 분석합니다.

// turbo-all
## 1. 프로젝트 맥락 및 변경 사항 통합 수집
에이전트는 윈도우 환경의 `run_command` 호출 시 실시간 결과 캡처의 안정성을 보장하기 위해 반드시 `cmd /c`를 사용하여 모든 정보를 수집합니다.

### Windows CMD (강제)
```cmd
cmd /c git status
cmd /c git diff --cached --stat
cmd /c git diff --cached
```

## 2. 메시지 생성 가이드라인 (Conventional Commits)
수집된 정보를 바탕으로 다음 규칙을 준수하여 메시지를 생성합니다:

- **Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **Scope**: (선택) 모듈명 (예: `ui`, `core`, `agent`)
- **Subject**: 명확한 요약
- **Body**: 변경 이유 및 상세 내용 (필요시)

## 3. 추천 서식
```text
<type>(<scope>): <subject>

- <변경 사항 설명 1>
- <변경 사항 설명 2>
```

## 윈도우 11 사용을 위한 팁
- `run_command` 호출 시 `WaitMsBeforeAsync`를 2000ms 이상으로 설정하면 `command_status` 확인 없이도 대부분의 결과를 동기적으로 받아볼 수 있어 실행 단계가 획기적으로 줄어듭니다.
