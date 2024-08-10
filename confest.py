import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = str(Path(__file__).parents[0])
sys.path.insert(0, project_root)
