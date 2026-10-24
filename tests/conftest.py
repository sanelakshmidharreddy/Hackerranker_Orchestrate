import sys
from pathlib import Path

# Add 'code' directory to sys.path so 'audit' and 'config' can be imported directly
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))
