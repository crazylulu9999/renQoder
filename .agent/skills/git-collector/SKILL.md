---
name: git-collector
description: Git의 모든 상태(status, staged diff, log)를 한 번에 수집하여 최적화된 컨텍스트를 제공하는 스킬입니다.
---

# Git Collector Skill

이 스킬은 윈도우 환경에서 Git의 모든 변경 사항을 가장 안정적이고 정확하게 수집하기 위해 설계되었습니다. `commit-msg` 워크플로우나 기타 Git 작업 시 컨텍스트가 필요할 때 사용합니다.

## 주요 기능
- **통합 수집**: `git status`, `git diff --cached --stat`, `git diff --cached`, `git branch`, `git log`를 하나의 리포트로 생성합니다.
- **인코딩 최적화**: 한글 깨짐 방지를 위해 UTF-8 출력을 강제하며, 윈도우 CLI 환경에 최적화된 `cmd /c` 방식을 사용합니다.
- **Markdown 형식**: 수집된 아웃풋은 에이전트가 이해하기 쉬운 Markdown 형식으로 제공됩니다.

## 사용 방법
에이전트가 Git 컨텍스트를 수집해야 할 때 다음 명령어를 실행합니다.

```cmd
python .agent\skills\git-collector\scripts\get_git_context.py
```

## 연계 워크플로우
- `.agent\workflows\commit-msg.md`: 이 스킬을 사용하여 staged된 변경 사항을 분석하고 메시지를 생성합니다.
