# exporters/to_json.py

import json
import os
from datetime import date


def export(data, output_dir):
    today = date.today().strftime("%Y%m%d")
    platform = data.get("플랫폼", "unknown")
    filename = platform + "_" + today + ".json"
    filepath = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath
