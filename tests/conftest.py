import sys
from pathlib import Path

# Add project root to Python path so 'server' and 'shared' modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent))
