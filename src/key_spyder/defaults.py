from datetime import datetime
from os import path, makedirs

DEFAULT_PATH = path.expanduser("~/Documents/key-spyder")
if not path.exists(DEFAULT_PATH):
    makedirs(DEFAULT_PATH)
NOW = datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
