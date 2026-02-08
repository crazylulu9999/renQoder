"""
Standalone 실행파일 빌드 스크립트
PyInstaller를 사용하여 단일 .exe 파일을 생성합니다.
"""

import subprocess
import sys
import shutil
import re
from pathlib import Path


def get_version():
    """__init__.py에서 버전 정보 읽기"""
    project_root = Path(__file__).parent.parent
    init_file = project_root / 'src' / 'renqoder' / '__init__.py'
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠ 버전 정보를 읽을 수 없습니다: {e}")
    
    return "0.0.0"


def check_pyinstaller():
    """PyInstaller 설치 확인 및 자동 설치 시도"""
    try:
        import PyInstaller
        print("✓ PyInstaller 설치 확인됨")
        return True
    except ImportError:
        print("⚠ PyInstaller가 설치되어 있지 않습니다.")
        print("\n자동 설치를 시도합니다...")
        
        try:
            # 먼저 --user 옵션으로 설치 시도
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--user', 'pyinstaller'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ PyInstaller 설치 완료 (사용자 디렉토리)")
                return True
            else:
                print(f"✗ 설치 실패: {result.stderr}")
                print("\n수동 설치 방법:")
                print("  1. 관리자 권한으로 CMD 실행")
                print("  2. pip install pyinstaller")
                print("\n또는:")
                print("  pip install --user pyinstaller")
                return False
                
        except Exception as e:
            print(f"✗ 자동 설치 실패: {e}")
            print("\n수동으로 설치해주세요:")
            print("  pip install --user pyinstaller")
            return False


def build_exe():
    """PyInstaller로 실행파일 빌드"""
    
    print("=" * 60)
    print("renQoder Standalone 빌드 시작")
    print("=" * 60)
    
    # 버전 정보 가져오기
    version = get_version()
    exe_name = f"renQoder-v{version}"
    print(f"\n버전: {version}")
    print(f"출력 파일명: {exe_name}.exe")
    
    # PyInstaller 확인
    if not check_pyinstaller():
        return False
    
    # 프로젝트 루트로 이동 (scripts 폴더에서 실행되므로)
    project_root = Path(__file__).parent.parent
    
    # 소스 파일 경로
    main_script = project_root / 'src' / 'renqoder' / 'main.py'
    if not main_script.exists():
        print(f"\n✗ 메인 스크립트를 찾을 수 없습니다: {main_script}")
        return False
    
    # 아이콘 및 리소스 경로
    resources_dir = project_root / 'src' / 'renqoder' / 'resources'
    icon_file = resources_dir / 'icon.ico'
    
    # PyInstaller 명령어 구성
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        f'--name={exe_name}',
        '--onefile',
        '--windowed',
        f'--icon={str(icon_file)}' if icon_file.exists() else '--icon=NONE',
        f'--add-data={project_root / "README.md"};.',
        f'--add-data={resources_dir};resources',
        f'--paths={project_root / "src"}',
        f'--paths={project_root / "src" / "renqoder"}',
        '--clean',
        str(main_script)
    ]
    
    print(f"\n실행 명령어: {' '.join(cmd)}\n")
    
    try:
        # 프로젝트 루트에서 실행
        result = subprocess.run(cmd, cwd=str(project_root), check=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✓ 빌드 성공!")
            print("=" * 60)
            
            exe_path = project_root / 'dist' / f'{exe_name}.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\n실행파일 위치: {exe_path.absolute()}")
                print(f"파일 이름: {exe_name}.exe")
                print(f"버전: {version}")
                print(f"파일 크기: {size_mb:.2f} MB")
                print("\n주의: FFmpeg는 별도로 시스템에 설치되어 있어야 합니다!")
            
            return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 빌드 실패: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 예상치 못한 오류: {e}")
        return False


def clean_build():
    """빌드 아티팩트 정리"""
    print("\n빌드 파일 정리 중...")
    
    project_root = Path(__file__).parent.parent
    
    dirs_to_remove = ['build', 'dist', '__pycache__', 'src/renqoder/__pycache__']
    
    for dir_name in dirs_to_remove:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  - 삭제: {dir_name}/")
    
    # .spec 파일 삭제 (버전이 포함된 파일명 패턴)
    for spec_file in project_root.glob('renQoder*.spec'):
        spec_file.unlink()
        print(f"  - 삭제: {spec_file.name}")
    
    print("정리 완료!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='renQoder 빌드 스크립트')
    parser.add_argument('--clean', action='store_true', help='빌드 파일만 정리')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    else:
        success = build_exe()
        
        if success:
            version = get_version()
            print(f"\n배포 준비 완료! dist/renQoder-v{version}.exe를 배포하세요.")
        else:
            sys.exit(1)
