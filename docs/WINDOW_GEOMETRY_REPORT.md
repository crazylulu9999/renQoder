# renQoder PoC 빌드 개선 보고서 v5

## 📅 업데이트 일자
2026-02-07 (5차 개선)

## 🎯 개선 목표
사용자가 이전에 사용하던 윈도우의 위치와 크기를 기억하여 다음 실행 시 동일한 환경을 제공하며, 모니터 구성 변경 등으로 인해 윈도우가 화면 밖으로 나가는 상황에 대한 폴백 처리 구현

---

## ✨ 주요 개선 사항

### 1. 윈도우 위치 및 크기 기억

#### 추가된 기능
애플리케이션 종료 시 윈도우의 상태(좌표, 너비, 높이)를 저장하고, 다음 실행 시 이를 복원합니다.

**저장 항목:**
- `x`: 윈도우 왼쪽 좌표
- `y`: 윈도우 상단 좌표
- `w`: 윈도우 너비
- `h`: 윈도우 높이

**저장 위치:**
- `~/.renqoder_config.json` (기존 설정 파일에 통합)

### 2. 스마트 오프스크린 폴백 (Off-screen Fallback)

#### 문제 해결
멀티 모니터 사용자가 모니터를 분리하거나 해상도를 변경하여 이전 위치가 현재 가시 영역 밖일 경우, 프로그램이 실행되어도 화면에 보이지 않는 문제를 방지합니다.

#### 동작 로직
1. 저장된 좌표값을 기반으로 윈도우 영역(`QRect`)을 계산합니다.
2. 현재 연결된 모든 모니터(`QApplication.screens()`)의 유효 영역(`availableGeometry`)과 대조합니다.
3. **가시성 검사**: 윈도우 영역의 최소 100x100 픽셀 이상이 어느 한 모니터에라도 포함되어 있는지 확인합니다.
4. **결과**:
   - **가시적일 경우**: 이전 위치 그대로 복원
   - **비가시적일 경우**: 주 모니터의 중앙에 기본 크기로 배치 (폴백)

---

## 📝 코드 변경 사항

### 1. `main.py` - 추가 Import
```python
from PySide6.QtCore import QRect, QPoint, QSize
from PySide6.QtGui import QScreen
```

### 2. `main.py` - 설정 관리 통합

기존의 개별적인 설정 저장 방식을 통합 관리 방식으로 리팩토링하였습니다.
- `load_config()`: JSON 파일 전체 로드
- `save_config(key, value)`: 특정 키의 값만 업데이트하여 저장

### 3. `main.py` - 윈도우 복원 및 중앙 배치 메서드

```python
def restore_window_geometry(self):
    config = self.load_config()
    geom = config.get('window_geometry')
    if geom:
        # 가시성 검사 로직 적용
        # ... (검사 통과 시) self.setGeometry(rect)
    else:
        self.center_window()

def center_window(self):
    """윈도우를 주 화면 중앙에 배치"""
    frame_gm = self.frameGeometry()
    screen_center = QApplication.primaryScreen().availableGeometry().center()
    frame_gm.moveCenter(screen_center)
    self.move(frame_gm.topLeft())
```

### 4. `main.py` - 종료 이벤트 오버라이드

```python
def closeEvent(self, event):
    """종료 시 현재 위치/사이즈 저장"""
    geom = self.geometry()
    self.save_config('window_geometry', {
        'x': geom.x(),
        'y': geom.y(),
        'w': geom.width(),
        'h': geom.height()
    })
    event.accept()
```

---

## 🧪 테스트 시나리오

| 시나리오 | 예상 동작 | 결과 |
|----------|----------|------|
| 일반 종료 후 재실행 | 이전 위치와 크기 그대로 복원 | ✅ 통과 |
| 윈도우를 구석으로 이동 후 재실행 | 이동된 위치 기억 | ✅ 통과 |
| 모니터 해상도 변경 시 | 화면 내에 걸쳐있으면 위치 유지 | ✅ 통과 |
| 강제로 설정 파일을 수정하여 오프스크린 좌표 입력 | 화면 밖임을 감지하고 자동으로 중앙 배치 | ✅ 통과 |
| 설정 파일이 없는 최초 실행 | 기본 사이즈로 중앙 배치 | ✅ 통과 |

---

## 💡 사용자 혜택

### 1. 개인화된 사용자 경험
✅ 사용자가 선호하는 작업 위치와 창 크기를 매번 재설정할 필요가 없습니다.

### 2. 안정성 확보
✅ 멀티 모니터 환경에서도 "창이 안 보여요"와 같은 현상을 방지하여 신뢰성을 높였습니다.

### 3. 일관된 설정 관리
✅ 폴더 경로, 윈도우 설정 등 모든 데이터가 하나의 설정 파일에서 체계적으로 관리됩니다.

---

## 🔄 0.2.0 버전 변경 사항 (CustomTkinter 전환)

GUI 프레임워크가 PySide6에서 CustomTkinter로 전환되면서 윈도우 지오메트리 관리 방식이 다음과 같이 최적화되었습니다:

- **데이터 포맷**: `QRect` 객체 기반의 개별 좌표 저장 방식에서 Tkinter 표준 `geometry` 문자열(예: `"700x850+100+100"`) 저장 방식으로 간소화되었습니다.
- **키 변경**: 설정 파일 내 키 이름을 `window_geometry`에서 `window_geometry_ctk`로 분리하여 프레임워크 간 설정 충돌을 방지했습니다.
- **복원 엔진**: PySide6의 `QScreen` API 대신 Tkinter의 내장 `geometry()` 메서드와 `on_closing` 이벤트를 사용하여 더 가볍고 안정적인 복원 로직을 구현했습니다.

---

## 🎉 결론

이번 개선을 통해 renQoder는 더욱 성숙한 데스크톱 애플리케이션의 면모를 갖추게 되었습니다. 특히 프레임워크 전환 후에도 사용자의 작업 환경을 그대로 유지할 수 있도록 설계되었습니다.

**최종 기능 완성!** 🚀
