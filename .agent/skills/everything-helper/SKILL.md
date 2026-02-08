---
name: everything-helper
description: Everything 검색 엔진을 커맨드라인에서 사용하여 윈도우 파일 시스템을 초고속으로 검색하는 스킬입니다.
---

# Everything Helper Skill

이 스킬은 Everything 검색 엔진의 커맨드라인 인터페이스(es.exe)와 GUI 옵션(Everything.exe)을 활용하여 윈도우 파일 시스템을 빠르게 검색하는 방법을 제공합니다.

## 주요 기능

- **초고속 파일 검색**: NTFS 인덱싱을 활용한 실시간 검색
- **다양한 출력 형식**: CSV, EFU, TXT, M3U 등 지원
- **정규식 및 고급 검색**: 복잡한 검색 패턴 지원
- **스크립트 자동화**: 배치 처리 및 파이프라인 통합

---

## 1. 기본 사용법 (es.exe)

### 필수 조건

- Everything이 설치되어 있고 실행 중이어야 합니다
- `es.exe`는 Everything 설치 폴더에 있거나 별도 다운로드 필요

### 기본 검색

```cmd
es.exe *.mp4
```

모든 MP4 파일 검색

### 검색 결과 제한

```cmd
es.exe -n 10 *.mp4
```

최대 10개 결과만 표시

---

## 2. 검색 옵션

### 정규식 검색

```cmd
es.exe -regex "^test.*\.txt$"
```

- `-r`, `-regex`: 정규식 모드 활성화

### 대소문자 구분

```cmd
es.exe -case README.md
```

- `-i`, `-case`: 대소문자 구분

### 전체 경로 검색

```cmd
es.exe -p -search "C:\dev\*.py"
```

- `-p`, `-match-path`: 파일명뿐 아니라 전체 경로에서 검색

### 전체 단어 일치

```cmd
es.exe -w test
```

- `-w`, `-ww`, `-whole-word`: 전체 단어가 일치하는 경우만 검색

---

## 3. 정렬 및 출력 형식

### 크기별 정렬

```cmd
es.exe -sort size -sort-descending *.mp4
```

가장 큰 파일부터 표시

### 수정 날짜별 정렬

```cmd
es.exe -sort date-modified -sort-descending -n 10
```

최근 수정된 파일 10개 표시

### 출력 열 선택

```cmd
es.exe -size -dm -path *.mp4
```

- `-size`: 파일 크기 표시
- `-dm`, `-date-modified`: 수정 날짜 표시
- `-path`: 경로 표시

---

## 4. 파일 내보내기

### CSV 형식으로 내보내기

```cmd
es.exe *.mp4 -export-csv output.csv
```

### EFU 파일 목록 생성

```cmd
es.exe *.mp3 -export-efu music.efu
```

EFU는 Everything의 파일 목록 형식

### M3U 재생목록 생성

```cmd
es.exe *.mp3 -export-m3u8 playlist.m3u8
```

---

## 5. 고급 검색 패턴

### 특정 경로 내 검색

```cmd
es.exe -path "C:\dev" *.py
```

C:\dev 폴더와 하위 폴더에서 모든 .py 파일 검색

### 부모 경로 지정

```cmd
es.exe -parent "C:\dev\renQoder" *.py
```

해당 경로의 직접 자식만 검색 (하위 폴더 제외)

### 속성 필터 (dir 스타일)

```cmd
es.exe /ad
```

폴더만 표시

```cmd
es.exe /a-d
```

파일만 표시

```cmd
es.exe /ar
```

읽기 전용 파일만 표시

```cmd
es.exe /a-h
```

숨김 파일 제외

---

## 6. 윈도우 환경 최적화

### 파이프라인 활용

```cmd
es.exe *.mp4 | findstr /i "test"
```

검색 결과를 다른 명령어로 파이프

### 파일 개수 세기

```cmd
es.exe *.mp4 -n 999999 | find /c /v ""
```

### 배치 스크립트 예제

```batch
@echo off
REM 가장 큰 비디오 파일 10개 찾기
es.exe -sort size -sort-descending -n 10 *.mp4 *.mkv *.avi

REM 최근 7일 이내 수정된 Python 파일
es.exe -sort dm -sort-descending dm:last7days *.py
```

---

## 7. Everything.exe GUI 옵션

### GUI에서 검색 열기

```cmd
Everything.exe -s "*.mp4"
```

검색어를 미리 입력한 상태로 GUI 열기

### 특정 경로에서 검색

```cmd
Everything.exe -path "C:\dev" -s "*.py"
```

### 북마크 열기

```cmd
Everything.exe -bookmark "My Videos"
```

### 필터 적용

```cmd
Everything.exe -filter "Video" -s "test"
```

---

## 8. 실용 예제

### 중복 파일명 찾기

```cmd
es.exe -export-csv all_files.csv
REM CSV를 파싱하여 중복 파일명 분석
```

### 특정 크기 이상 파일 찾기

```cmd
es.exe size:>1gb
```

1GB 이상 파일 검색

### 오늘 수정된 파일

```cmd
es.exe dm:today
```

### 빈 폴더 찾기

```cmd
es.exe empty:
```

### 확장자 없는 파일

```cmd
es.exe noext:
```

---

## 9. Python 통합 예제

### subprocess로 검색 실행

```python
import subprocess
import json

def search_files(pattern, max_results=100):
    """Everything을 사용하여 파일 검색"""
    cmd = [
        "es.exe",
        "-n", str(max_results),
        "-path-column",
        "-size",
        pattern
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    
    return result.stdout.strip().split('\n')

# 사용 예
files = search_files("*.mp4")
for file in files:
    print(file)
```

### CSV 출력 파싱

```python
import subprocess
import csv
import tempfile
import os

def search_to_dict(pattern):
    """검색 결과를 딕셔너리 리스트로 반환"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_csv = f.name
    
    try:
        subprocess.run([
            "es.exe",
            pattern,
            "-export-csv", temp_csv,
            "-path-column",
            "-size",
            "-dm"
        ], check=True)
        
        with open(temp_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)
    finally:
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

# 사용 예
results = search_to_dict("*.mp4")
for item in results:
    print(f"{item['Name']}: {item['Size']} bytes")
```

---

## 10. 검색 문법 (Everything 쿼리 언어)

### 기본 연산자

- `AND` 또는 공백: `file1 file2` (둘 다 포함)
- `OR` 또는 `|`: `file1|file2` (하나라도 포함)
- `NOT` 또는 `!`: `!file1` (제외)

### 와일드카드

- `*`: 0개 이상의 문자
- `?`: 정확히 1개의 문자

### 함수

- `size:`: 크기 (`size:>1gb`, `size:1mb..10mb`)
- `dm:`: 수정 날짜 (`dm:today`, `dm:last7days`)
- `dc:`: 생성 날짜
- `da:`: 접근 날짜
- `ext:`: 확장자 (`ext:mp4;mkv;avi`)
- `folder:`: 폴더만
- `file:`: 파일만

---

## 11. 성능 팁

### 인덱스 최적화

- Everything이 백그라운드에서 실행 중이어야 함
- NTFS 볼륨에서만 초고속 검색 가능
- FAT32는 실시간 업데이트 불가

### 검색 속도 향상

```cmd
REM 결과 제한으로 속도 향상
es.exe -n 100 *.mp4

REM 불필요한 열 제거
es.exe -name *.mp4
```

---

## 12. 에러 처리

### 반환 값

- `0`: 성공
- `1`: 오류 발생
- `2`: Everything이 실행 중이지 않음

### Python에서 에러 처리

```python
import subprocess

try:
    result = subprocess.run(
        ["es.exe", "*.mp4"],
        capture_output=True,
        text=True,
        check=True
    )
    print(result.stdout)
except subprocess.CalledProcessError as e:
    if e.returncode == 2:
        print("Everything이 실행 중이지 않습니다.")
    else:
        print(f"검색 오류: {e.stderr}")
```

---

## 참고 자료

- [Everything 공식 사이트](https://www.voidtools.com/)
- [Command Line Interface 문서](https://www.voidtools.com/ko-kr/support/everything/command_line_interface/)
- [Command Line Options 문서](https://www.voidtools.com/ko-kr/support/everything/command_line_options/)
- [검색 문법 가이드](https://www.voidtools.com/ko-kr/support/everything/searching/)

## 사용 예제

실제 사용 예제는 `examples/` 디렉토리를 참조하세요:
- `basic_search.py`: 기본 검색 예제
- `csv_export.py`: CSV 내보내기 및 파싱
- `advanced_queries.md`: 고급 검색 쿼리 모음
