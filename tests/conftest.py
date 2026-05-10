import sys
from pathlib import Path

# Add project root to Python path so 'server' and 'shared' modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Register DI services before any tests run
from server.di import container, register_services
register_services(container)
