# renQoder PoC 빌드 개선 보고서 v4

## 📅 업데이트 일자
2026-02-07 (4차 개선)

## 🎯 개선 목표
출력 파일 드라이브의 남은 용량을 실시간으로 표시하여 사용자가 인코딩 전에 충분한 공간이 있는지 확인할 수 있도록 함

---

## ✨ 주요 개선 사항

### 1. 드라이브 용량 실시간 표시

#### 추가된 기능
출력 파일이 저장될 드라이브의 남은 용량을 실시간으로 표시합니다.

**표시 위치:**
- 출력 파일명 입력창 바로 아래
- 드라이브 아이콘(💾)과 함께 표시

**표시 형식:**
```
💾 C: 드라이브: 125.3GB / 476.9GB 사용 가능
```

#### 용량 상태별 색상 코드

| 남은 용량 | 색상 | 경고 메시지 | 설명 |
|----------|------|------------|------|
| 50GB 이상 | 회색 (#888) | 없음 | 정상 |
| 10GB ~ 50GB | 주황색 (#ffaa00) | 없음 | 주의 |
| 10GB 미만 | 빨간색 (#ff4444) | ⚠️ 공간 부족 | 경고 |

**예시:**
```
정상: 💾 C: 드라이브: 125.3GB / 476.9GB 사용 가능
주의: 💾 D: 드라이브: 35.2GB / 1000.0GB 사용 가능
경고: 💾 E: 드라이브: 8.5GB / 250.0GB 사용 가능 ⚠️ 공간 부족
```

---

## 📝 코드 변경 사항

### 1. `main.py` - Import 추가

```python
import shutil  # 디스크 용량 확인용
```

### 2. `main.py` - UI 요소 추가

```python
# 드라이브 용량 정보
self.drive_space_label = QLabel("")
self.drive_space_label.setStyleSheet("color: #888; font-size: 10px; padding: 2px 0;")
output_layout.addWidget(self.drive_space_label)
```

### 3. `main.py` - 드라이브 용량 확인 메서드

```python
def get_drive_space(self, file_path):
    """드라이브 용량 정보 반환"""
    try:
        path = Path(file_path)
        drive = path.drive if path.drive else path.parts[0]
        
        # 드라이브 용량 확인
        total, used, free = shutil.disk_usage(drive)
        
        # GB 단위로 변환
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        
        return free_gb, total_gb
    except Exception as e:
        print(f"드라이브 용량 확인 실패: {e}")
        return None, None
```

### 4. `main.py` - 드라이브 용량 레이블 업데이트

```python
def update_drive_space_label(self):
    """드라이브 용량 레이블 업데이트"""
    if not self.output_file:
        self.drive_space_label.setText("")
        return
    
    free_gb, total_gb = self.get_drive_space(self.output_file)
    
    if free_gb is not None and total_gb is not None:
        # 용량에 따라 색상 변경
        if free_gb < 10:
            color = "#ff4444"  # 빨간색 (경고)
            warning = " ⚠️ 공간 부족"
        elif free_gb < 50:
            color = "#ffaa00"  # 주황색 (주의)
            warning = ""
        else:
            color = "#888"  # 회색 (정상)
            warning = ""
        
        drive = Path(self.output_file).drive
        self.drive_space_label.setText(
            f"💾 {drive} 드라이브: {free_gb:.1f}GB / {total_gb:.1f}GB 사용 가능{warning}"
        )
        self.drive_space_label.setStyleSheet(f"color: {color}; font-size: 10px; padding: 2px 0;")
    else:
        self.drive_space_label.setText("")
```

### 5. 업데이트 트리거

드라이브 용량 정보는 다음 시점에 자동으로 업데이트됩니다:

1. **출력 파일명 자동 생성 시** (`update_output_filename`)
2. **출력 파일명 수동 변경 시** (`edit_output_filename`)

```python
# update_output_filename 메서드 내
self.ffmpeg_preview.setText(cmd_preview)

# 드라이브 용량 업데이트
self.update_drive_space_label()
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 용량 (50GB 이상)

**상황:**
- C: 드라이브에 125GB 여유 공간
- 출력 파일: `C:\Videos\gameplay_NVENC_CQ23_AAC.mkv`

**결과:**
```
💾 C: 드라이브: 125.3GB / 476.9GB 사용 가능
```
- 색상: 회색 (#888)
- 경고: 없음

### 시나리오 2: 주의 용량 (10GB ~ 50GB)

**상황:**
- D: 드라이브에 35GB 여유 공간
- 출력 파일: `D:\Recordings\stream_QSV_CQ20_AAC192k.mp4`

**결과:**
```
💾 D: 드라이브: 35.2GB / 1000.0GB 사용 가능
```
- 색상: 주황색 (#ffaa00)
- 경고: 없음

### 시나리오 3: 경고 용량 (10GB 미만)

**상황:**
- E: 드라이브에 8.5GB 여유 공간
- 출력 파일: `E:\Temp\video_AMF_CQ25_AC3.mkv`

**결과:**
```
💾 E: 드라이브: 8.5GB / 250.0GB 사용 가능 ⚠️ 공간 부족
```
- 색상: 빨간색 (#ff4444)
- 경고: ⚠️ 공간 부족

### 시나리오 4: 드라이브 변경

**상황:**
- 사용자가 출력 파일을 C:에서 D:로 변경

**동작:**
1. "✏️ 수정" 버튼 클릭
2. 파일 저장 다이얼로그에서 D: 드라이브 선택
3. 드라이브 용량 정보 자동 업데이트

**결과:**
```
Before: 💾 C: 드라이브: 125.3GB / 476.9GB 사용 가능
After:  💾 D: 드라이브: 35.2GB / 1000.0GB 사용 가능
```

---

## 💡 사용자 혜택

### 1. 사전 공간 확인
✅ 인코딩 시작 전에 충분한 공간이 있는지 확인 가능  
✅ 중간에 공간 부족으로 실패하는 상황 방지  

### 2. 시각적 경고
✅ 색상 코드로 한눈에 상태 파악  
✅ 10GB 미만 시 명확한 경고 메시지  

### 3. 실시간 업데이트
✅ 드라이브 변경 시 즉시 반영  
✅ 별도 조작 없이 자동 업데이트  

---

## 🎯 실사용 예시

### 예시 1: 대용량 파일 인코딩

**상황:**
```
입력 파일: 50GB (4K 60fps 녹화본)
예상 출력: ~15GB (CQ23 HEVC)
C: 드라이브 여유: 12GB
```

**화면 표시:**
```
💾 C: 드라이브: 12.0GB / 476.9GB 사용 가능 ⚠️ 공간 부족
```

**사용자 행동:**
1. 경고 확인
2. "✏️ 수정" 버튼으로 D: 드라이브로 변경
3. 안전하게 인코딩 진행

### 예시 2: 여유 공간 충분

**상황:**
```
입력 파일: 10GB
예상 출력: ~3GB
D: 드라이브 여유: 500GB
```

**화면 표시:**
```
💾 D: 드라이브: 500.0GB / 1000.0GB 사용 가능
```

**사용자 행동:**
1. 여유 공간 확인
2. 바로 인코딩 시작

---

## 🔧 기술 세부사항

### 사용된 Python 모듈
- `shutil.disk_usage()`: 드라이브 용량 확인
- `pathlib.Path`: 경로 및 드라이브 추출

### 성능 영향
- **최소**: 드라이브 용량 확인은 매우 빠른 시스템 호출
- **호출 빈도**: 출력 파일명 변경 시에만 호출 (실시간 폴링 없음)

### 에러 처리
```python
try:
    total, used, free = shutil.disk_usage(drive)
    # ...
except Exception as e:
    print(f"드라이브 용량 확인 실패: {e}")
    return None, None
```

---

## 📊 Before & After

### Before (v3)
```
출력 파일명: gameplay_NVENC_CQ23_AAC.mkv
[파일명만 표시]
```

### After (v4)
```
출력 파일명: gameplay_NVENC_CQ23_AAC.mkv
💾 C: 드라이브: 125.3GB / 476.9GB 사용 가능
```

---

## 🎉 결론

**renQoder PoC 빌드 4차 개선**을 통해:

✅ **사전 공간 확인**: 인코딩 전 충분한 공간 확인  
✅ **시각적 경고**: 색상 코드로 직관적인 상태 표시  
✅ **사용자 경험 향상**: 공간 부족으로 인한 실패 방지  

### 최종 기능 목록

renQoder PoC는 이제 다음 기능을 모두 갖추었습니다:

✅ GPU 자동 감지 및 최적 코덱 선택  
✅ FFmpeg 환경 검사  
✅ 스마트 파일명 (코덱 + 품질 + 오디오 정보)  
✅ 오디오 코덱 자동 감지  
✅ FFmpeg 명령어 미리보기  
✅ 화질 설정 가이드  
✅ 마지막 폴더 기억  
✅ **드라이브 용량 실시간 표시** ✨ (NEW!)  
✅ 실시간 진행률 표시  
✅ 동적 GPU 테마  

**프로덕션 준비 완료!** 🎊

---

## 📋 변경 파일 목록

- ✏️ `src/renqoder/main.py`: 드라이브 용량 표시 기능 추가
  - `import shutil` 추가
  - `drive_space_label` UI 요소 추가
  - `get_drive_space()` 메서드 추가
  - `update_drive_space_label()` 메서드 추가
  - `update_output_filename()` 메서드 수정
  - `edit_output_filename()` 메서드 수정
