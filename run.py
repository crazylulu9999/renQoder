"""
renQoder 실행 진입점
"""

import sys
import subprocess
from pathlib import Path

def check_and_install_requirements():
    """requirements.txt 파일을 확인하고 필요한 패키지를 설치합니다."""
    requirements_path = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_path.exists():
        return

    needs_install = False
    
    try:
        # pkg_resources를 사용하여 버전 및 설치 여부 확인
        import pkg_resources
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            # 주석과 빈 줄 제외하고 파싱
            requirements = [
                str(req) for req in pkg_resources.parse_requirements(f)
            ]
            
        try:
            # 현재 환경에서 요구사항이 만족되는지 확인
            pkg_resources.require(requirements)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            needs_install = True
            
    except ImportError:
        # pkg_resources가 없으면 pip 실행을 시도 (안전책)
        needs_install = True
    except Exception as e:
        print(f"요구사항 확인 중 오류 발생: {e}")
        needs_install = True

    if needs_install:
        print("필요한 패키지를 설치 중입니다...", end=" ", flush=True)
        try:
            # pip install 실행 (조용히 실행)
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
            print("완료.")
        except subprocess.CalledProcessError:
            print("실패.")
            print(f"오류: 'pip install -r requirements.txt' 명령어를 수동으로 실행해 주세요.")
            sys.exit(1)

if __name__ == "__main__":
    # 라이브러리 설치 확인
    check_and_install_requirements()
    
    # src 디렉토리를 Python 경로에 추가
    src_path = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))
    
    # 애플리케이션 실행
    try:
        from renqoder.main import main
        main()
    except ImportError as e:
        print(f"애플리케이션 실행 오류: {e}")
        print("필요한 모듈을 불러올 수 없습니다. 설치가 제대로 되었는지 확인해주세요.")
        sys.exit(1)
