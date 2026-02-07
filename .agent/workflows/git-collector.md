---
description: Git의 모든 상태(status, staged diff, log)를 한 번에 수집하여 리포트를 생성합니다.
---

# Git Context 수집 워크플로우

이 워크플로우는 `git-collector` 스킬을 호출하여 프로젝트의 현재 Git 상태를 완벽하게 파악합니다.

// turbo
## 1. Git 정보 통합 수집
```cmd
python .agent\skills\git-collector\scripts\get_git_context.py
```

## 2. 결과 분석
수집된 리포트를 바탕으로 다음 작업을 수행할 수 있습니다:
- 커밋 메시지 추천
- 변경 사항 분석 및 요약
- 충돌 발생 가능성 확인
