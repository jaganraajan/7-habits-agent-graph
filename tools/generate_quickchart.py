import os
import json
import time
import pathlib
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import requests
from langchain_core.tools import tool

# Output directory (override with DATA_DIR env var)
DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _safe_filename(stem: Optional[str]) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = "".join(c for c in (stem or "chart") if c.isalnum() or c in ("-", "_")) or "chart"
    return f"{base}-{ts}.png"

@tool
def generate_quickchart(
    c: Dict[str, Any],
    width: int = 600,
    height: int = 400,
    filename_stem: Optional[str] = None,
) -> str:
    """
    Create a QuickChart PNG image from a Chart.js config.

    Args:
        c: Chart.js config as a Python dict (required).
        width: Image width in pixels (default 600).
        height: Image height in pixels (default 400).
        filename_stem: Optional base filename (timestamp appended).

    Returns:
        Absolute path to the saved PNG.

    Example:
        generate_quickchart(
            c={
                "type": "bar",
                "data": {
                    "labels": ["A","B","C"],
                    "datasets": [{"label": "Scores", "data": [3,7,4]}]
                }
            }
        )
    """
    if not isinstance(c, dict):
        raise ValueError("`c` must be a Python dict (Chart.js config).")

    query = urlencode(
        {
            "c": json.dumps(c, separators=(",", ":")),
            "width": width,
            "height": height,
            "format": "png",
        },
        doseq=True,
        safe=":,{}[]\""
    )
    url = f"https://quickchart.io/chart?{query}"

    try:
        resp = requests.get(url, timeout=20)  # fixed timeout
        if resp.status_code != 200:
            raise RuntimeError(f"QuickChart HTTP {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch QuickChart image: {e}") from e

    fpath = DATA_DIR / _safe_filename(filename_stem)
    with open(fpath, "wb") as f:
        f.write(resp.content)

    return str(fpath)
