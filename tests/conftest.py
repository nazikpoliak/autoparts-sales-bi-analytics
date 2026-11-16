"""Make the generator modules importable and provide shared fixtures."""
import sys
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parents[1] / "python" / "data_generator"
if str(GENERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATOR_DIR))
