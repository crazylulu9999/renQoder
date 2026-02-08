# Everything 고급 검색 쿼리 모음

이 문서는 Everything 검색 엔진의 강력한 쿼리 언어를 활용한 고급 검색 예제를 제공합니다.

## 기본 연산자

### AND (그리고)

```
test file
```

"test"와 "file"을 모두 포함하는 파일

### OR (또는)

```
.mp4|.mkv|.avi
```

MP4, MKV, AVI 중 하나의 확장자를 가진 파일

### NOT (제외)

```
*.txt !readme
```

TXT 파일 중 "readme"가 포함되지 않은 파일

## 크기 검색

### 정확한 크기

```
size:1mb
```

정확히 1MB인 파일

### 범위 검색

```
size:1mb..10mb
```

1MB ~ 10MB 사이의 파일

### 비교 연산자

```
size:>1gb
```

1GB보다 큰 파일

```
size:<100kb
```

100KB보다 작은 파일

### 빈 파일

```
size:0
```

크기가 0인 빈 파일

## 날짜 검색

### 오늘

```
dm:today
```

오늘 수정된 파일

### 어제

```
dm:yesterday
```

어제 수정된 파일

### 최근 N일

```
dm:last7days
```

최근 7일 이내 수정된 파일

```
dm:last30days
```

최근 30일 이내 수정된 파일

### 특정 날짜

```
dm:2024-01-01
```

2024년 1월 1일에 수정된 파일

### 날짜 범위

```
dm:2024-01-01..2024-12-31
```

2024년에 수정된 파일

### 생성 날짜

```
dc:last7days
```

최근 7일 이내 생성된 파일

### 접근 날짜

```
da:today
```

오늘 접근한 파일

## 경로 및 위치

### 특정 폴더

```
path:C:\dev *.py
```

C:\dev 폴더와 하위 폴더의 모든 Python 파일

### 정확한 폴더 (하위 폴더 제외)

```
parent:C:\dev *.py
```

C:\dev 폴더의 직접 자식 Python 파일만

### 폴더 이름 검색

```
folder:test
```

이름에 "test"가 포함된 폴더

### 루트 폴더만

```
parent:C:\ folder:
```

C 드라이브 루트의 폴더만

## 파일 속성

### 폴더만

```
folder:
```

모든 폴더

### 파일만

```
file:
```

모든 파일

### 숨김 파일

```
attrib:H
```

숨김 속성이 있는 파일

### 읽기 전용

```
attrib:R
```

읽기 전용 파일

### 시스템 파일

```
attrib:S
```

시스템 파일

### 보관 파일

```
attrib:A
```

보관 속성이 있는 파일

### 속성 제외

```
attrib:!H
```

숨김 파일 제외

## 확장자

### 특정 확장자

```
ext:mp4
```

MP4 확장자 파일

### 여러 확장자

```
ext:mp4;mkv;avi
```

MP4, MKV, AVI 확장자 파일

### 확장자 없음

```
noext:
```

확장자가 없는 파일

## 정규식

### 기본 정규식

```
regex:^test.*\.txt$
```

"test"로 시작하고 ".txt"로 끝나는 파일

### 숫자 패턴

```
regex:file_\d{4}\.txt
```

"file_0001.txt" 형식의 파일

### 날짜 패턴

```
regex:\d{4}-\d{2}-\d{2}
```

"2024-01-01" 형식이 포함된 파일

## 복합 검색

### 최근 큰 비디오 파일

```
ext:mp4;mkv;avi size:>1gb dm:last30days
```

최근 30일 이내 수정된 1GB 이상의 비디오 파일

### 특정 폴더의 최근 문서

```
path:C:\Documents ext:docx;xlsx;pptx dm:last7days
```

C:\Documents의 최근 7일 이내 수정된 Office 문서

### 오래된 임시 파일

```
path:C:\Temp dm:<2024-01-01
```

2024년 이전에 수정된 임시 파일

### 중복 가능성 있는 파일

```
*.mp3 dupe:
```

중복된 MP3 파일 (이름 기준)

## 특수 검색

### 빈 폴더

```
empty:
```

빈 폴더

### 실행 파일

```
ext:exe;bat;cmd;ps1
```

실행 가능한 파일

### 이미지 파일

```
ext:jpg;jpeg;png;gif;bmp;webp
```

이미지 파일

### 압축 파일

```
ext:zip;rar;7z;tar;gz
```

압축 파일

### 코드 파일

```
ext:py;js;ts;java;cpp;c;h;cs
```

프로그래밍 언어 파일

## 명령줄에서 사용

### 기본 검색

```cmd
es.exe "size:>1gb dm:last7days"
```

### 정렬 포함

```cmd
es.exe -sort size -sort-descending "*.mp4"
```

### 결과 제한

```cmd
es.exe -n 10 "dm:today"
```

### CSV 내보내기

```cmd
es.exe "size:>1gb" -export-csv large_files.csv
```

## Python에서 사용

### 복잡한 쿼리 실행

```python
import subprocess

def search_everything(query):
    cmd = ["es.exe", query]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip().split('\n')

# 최근 큰 비디오 파일
results = search_everything("ext:mp4;mkv size:>1gb dm:last30days")
for file in results:
    print(file)
```

### 동적 쿼리 생성

```python
def build_query(extensions=None, min_size=None, date_range=None, path=None):
    """동적으로 검색 쿼리 생성"""
    parts = []
    
    if extensions:
        parts.append(f"ext:{';'.join(extensions)}")
    
    if min_size:
        parts.append(f"size:>{min_size}")
    
    if date_range:
        parts.append(f"dm:{date_range}")
    
    if path:
        parts.append(f"path:{path}")
    
    return " ".join(parts)

# 사용 예
query = build_query(
    extensions=["mp4", "mkv"],
    min_size="1gb",
    date_range="last30days",
    path="C:\\Videos"
)
print(f"쿼리: {query}")
# 출력: ext:mp4;mkv size:>1gb dm:last30days path:C:\Videos
```

## 성능 최적화

### 경로 제한으로 속도 향상

```
path:C:\dev *.py
```

전체 드라이브 검색보다 빠름

### 결과 제한

```cmd
es.exe -n 100 "*.mp4"
```

필요한 만큼만 검색

### 인덱싱된 속성 사용

```
size:>1gb
```

파일 내용 검색보다 빠름

## 참고 사항

- 공백은 AND 연산자로 작동
- 대소문자 구분 없음 (기본값)
- 와일드카드(`*`, `?`)는 정규식보다 빠름
- 복잡한 쿼리는 성능에 영향을 줄 수 있음
