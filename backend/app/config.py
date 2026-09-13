import sys
from pathlib import Path

# Allow importing the ml/ package from project root
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.utils import config as ml_config  # noqa: E402

DATABASE_URL = ml_config.DATABASE_URL
UPLOAD_DIR = ml_config.UPLOAD_DIR
GENERATED_DIR = ml_config.GENERATED_DIR