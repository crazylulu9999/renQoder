"""
Everything 검색 엔진 기본 사용 예제

이 스크립트는 es.exe를 사용하여 파일을 검색하는 기본적인 방법을 보여줍니다.
"""

import subprocess
import sys


def search_files(pattern, max_results=100, sort_by="name"):
    """
    Everything을 사용하여 파일 검색
    
    Args:
        pattern: 검색 패턴 (예: "*.mp4", "test*.txt")
        max_results: 최대 결과 개수
        sort_by: 정렬 기준 ("name", "size", "date-modified" 등)
    
    Returns:
        검색 결과 리스트 (각 줄이 하나의 파일 경로)
    """
    cmd = [
        "es.exe",
        "-n", str(max_results),
        "-sort", sort_by,
        pattern
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        
        # 빈 줄 제거
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return lines
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 2:
            print("오류: Everything이 실행 중이지 않습니다.", file=sys.stderr)
            print("Everything을 먼저 실행해주세요.", file=sys.stderr)
        else:
            print(f"검색 오류: {e.stderr}", file=sys.stderr)
        return []


def search_with_details(pattern, max_results=100):
    """
    파일 검색 + 크기, 수정 날짜 정보 포함
    
    Args:
        pattern: 검색 패턴
        max_results: 최대 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    cmd = [
        "es.exe",
        "-n", str(max_results),
        "-path-column",
        "-size",
        "-dm",
        pattern
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return lines
        
    except subprocess.CalledProcessError as e:
        print(f"검색 오류: {e}", file=sys.stderr)
        return []


def search_largest_files(pattern, count=10):
    """
    가장 큰 파일 찾기
    
    Args:
        pattern: 검색 패턴
        count: 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    cmd = [
        "es.exe",
        "-n", str(count),
        "-sort", "size",
        "-sort-descending",
        "-size",
        pattern
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return lines
        
    except subprocess.CalledProcessError as e:
        print(f"검색 오류: {e}", file=sys.stderr)
        return []


def search_recent_files(pattern, count=10):
    """
    최근 수정된 파일 찾기
    
    Args:
        pattern: 검색 패턴
        count: 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    cmd = [
        "es.exe",
        "-n", str(count),
        "-sort", "date-modified",
        "-sort-descending",
        "-dm",
        pattern
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return lines
        
    except subprocess.CalledProcessError as e:
        print(f"검색 오류: {e}", file=sys.stderr)
        return []


if __name__ == "__main__":
    print("=== Everything 검색 예제 ===\n")
    
    # 예제 1: 기본 검색
    print("1. 모든 MP4 파일 검색 (최대 10개):")
    results = search_files("*.mp4", max_results=10)
    for file in results:
        print(f"  - {file}")
    print()
    
    # 예제 2: 상세 정보 포함 검색
    print("2. Python 파일 검색 (크기, 수정 날짜 포함):")
    results = search_with_details("*.py", max_results=5)
    for file in results:
        print(f"  - {file}")
    print()
    
    # 예제 3: 가장 큰 파일
    print("3. 가장 큰 비디오 파일 5개:")
    results = search_largest_files("*.mp4 | *.mkv | *.avi", count=5)
    for file in results:
        print(f"  - {file}")
    print()
    
    # 예제 4: 최근 수정된 파일
    print("4. 최근 수정된 문서 파일 5개:")
    results = search_recent_files("*.txt | *.md | *.doc*", count=5)
    for file in results:
        print(f"  - {file}")
