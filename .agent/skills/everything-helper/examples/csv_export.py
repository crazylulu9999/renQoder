"""
Everything 검색 결과를 CSV로 내보내고 파싱하는 예제

이 스크립트는 es.exe의 CSV 내보내기 기능을 활용하여
검색 결과를 구조화된 데이터로 처리하는 방법을 보여줍니다.
"""

import subprocess
import csv
import tempfile
import os
from pathlib import Path


def search_to_csv(pattern, output_file=None, include_columns=None):
    """
    검색 결과를 CSV 파일로 내보내기
    
    Args:
        pattern: 검색 패턴
        output_file: 출력 CSV 파일 경로 (None이면 임시 파일)
        include_columns: 포함할 열 리스트 (예: ["path", "size", "dm"])
    
    Returns:
        CSV 파일 경로
    """
    if output_file is None:
        # 임시 파일 생성
        fd, output_file = tempfile.mkstemp(suffix='.csv', text=True)
        os.close(fd)
    
    cmd = ["es.exe", pattern]
    
    # 열 선택
    if include_columns:
        for col in include_columns:
            if col == "path":
                cmd.append("-path-column")
            elif col == "name":
                cmd.append("-name")
            elif col == "size":
                cmd.append("-size")
            elif col == "dm":
                cmd.append("-dm")
            elif col == "dc":
                cmd.append("-dc")
            elif col == "extension":
                cmd.append("-extension")
    
    # CSV 내보내기
    cmd.extend(["-export-csv", output_file])
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"CSV 내보내기 실패: {e}")
        return None


def parse_csv(csv_file):
    """
    CSV 파일을 파싱하여 딕셔너리 리스트로 반환
    
    Args:
        csv_file: CSV 파일 경로
    
    Returns:
        딕셔너리 리스트 (각 행이 하나의 딕셔너리)
    """
    results = []
    
    try:
        # UTF-8 BOM 처리
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            results = list(reader)
    except Exception as e:
        print(f"CSV 파싱 오류: {e}")
    
    return results


def search_to_dict(pattern, include_columns=None, max_results=None):
    """
    검색 결과를 딕셔너리 리스트로 반환 (원스톱 함수)
    
    Args:
        pattern: 검색 패턴
        include_columns: 포함할 열 리스트
        max_results: 최대 결과 개수
    
    Returns:
        딕셔너리 리스트
    """
    # 임시 CSV 파일 생성
    csv_file = search_to_csv(pattern, include_columns=include_columns)
    
    if csv_file is None:
        return []
    
    try:
        # CSV 파싱
        results = parse_csv(csv_file)
        
        # 결과 제한
        if max_results:
            results = results[:max_results]
        
        return results
    finally:
        # 임시 파일 삭제
        if os.path.exists(csv_file):
            try:
                os.remove(csv_file)
            except:
                pass


def analyze_file_sizes(pattern):
    """
    파일 크기 분석
    
    Args:
        pattern: 검색 패턴
    
    Returns:
        분석 결과 딕셔너리
    """
    results = search_to_dict(pattern, include_columns=["name", "size"])
    
    if not results:
        return None
    
    # 크기를 정수로 변환
    sizes = []
    for item in results:
        try:
            size = int(item.get('Size', 0))
            sizes.append(size)
        except ValueError:
            continue
    
    if not sizes:
        return None
    
    total_size = sum(sizes)
    avg_size = total_size / len(sizes)
    max_size = max(sizes)
    min_size = min(sizes)
    
    return {
        'count': len(sizes),
        'total_size': total_size,
        'avg_size': avg_size,
        'max_size': max_size,
        'min_size': min_size,
        'total_size_mb': total_size / (1024 * 1024),
        'total_size_gb': total_size / (1024 * 1024 * 1024)
    }


def find_duplicates_by_name(pattern):
    """
    파일명 중복 찾기 (경로는 다르지만 파일명이 같은 경우)
    
    Args:
        pattern: 검색 패턴
    
    Returns:
        중복 파일명 딕셔너리 {파일명: [경로 리스트]}
    """
    results = search_to_dict(pattern, include_columns=["path", "name"])
    
    # 파일명별로 그룹화
    name_groups = {}
    for item in results:
        name = item.get('Name', '')
        path = item.get('Path', '')
        
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(path)
    
    # 중복만 필터링
    duplicates = {name: paths for name, paths in name_groups.items() if len(paths) > 1}
    
    return duplicates


if __name__ == "__main__":
    print("=== Everything CSV 내보내기 예제 ===\n")
    
    # 예제 1: 기본 CSV 내보내기
    print("1. MP4 파일 검색 및 CSV 내보내기:")
    results = search_to_dict("*.mp4", include_columns=["name", "size", "dm"], max_results=5)
    for item in results:
        print(f"  - {item}")
    print()
    
    # 예제 2: 파일 크기 분석
    print("2. Python 파일 크기 분석:")
    analysis = analyze_file_sizes("*.py")
    if analysis:
        print(f"  - 파일 개수: {analysis['count']}")
        print(f"  - 총 크기: {analysis['total_size_mb']:.2f} MB")
        print(f"  - 평균 크기: {analysis['avg_size'] / 1024:.2f} KB")
        print(f"  - 최대 크기: {analysis['max_size'] / 1024:.2f} KB")
        print(f"  - 최소 크기: {analysis['min_size'] / 1024:.2f} KB")
    print()
    
    # 예제 3: 중복 파일명 찾기
    print("3. 중복 파일명 찾기 (README.md):")
    duplicates = find_duplicates_by_name("README.md")
    for name, paths in duplicates.items():
        print(f"  파일명: {name}")
        for path in paths:
            print(f"    - {path}")
    print()
    
    # 예제 4: 영구 CSV 파일로 저장
    print("4. 검색 결과를 파일로 저장:")
    output_file = "video_files.csv"
    csv_file = search_to_csv("*.mp4 | *.mkv | *.avi", 
                             output_file=output_file,
                             include_columns=["path", "size", "dm"])
    if csv_file:
        print(f"  저장 완료: {csv_file}")
        print(f"  파일 크기: {os.path.getsize(csv_file)} bytes")
