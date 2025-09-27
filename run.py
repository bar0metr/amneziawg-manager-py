import json
import sys
from pathlib import Path
import uvicorn

config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.json")
with config_path.open("r") as f:
    CONFIG = json.load(f)

from app.main import app
import app.utils as utils
utils.load_config(CONFIG)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=CONFIG["app"]["host"],
        port=CONFIG["app"]["port"],
        reload=CONFIG["app"].get("reload", True),
        log_level=CONFIG["app"].get("log_level", "info").lower()
    )
