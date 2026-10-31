"""Compatibility import for desktop tools."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from printing import bluetooth_client as implementation
sys.modules[__name__]=implementation
