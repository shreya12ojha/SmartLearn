# Tests package
import sys
from pathlib import Path

# Add path_planning_agent root to sys.path so tests can import path_planning_agent directly
_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))
