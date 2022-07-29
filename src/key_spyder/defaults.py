from datetime import datetime
from os import path, makedirs
from pathlib import Path

DEFAULT_PATH = path.expanduser("~/Documents/key-spyder")
if not Path(DEFAULT_PATH).exists():
    Path(DEFAULT_PATH).mkdir(parents=True)
NOW = datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
