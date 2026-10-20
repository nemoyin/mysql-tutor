from pathlib import Path
import json


def load_catalog():
    path = Path(__file__).resolve().parents[1] / 'dataset/catalog.json'
    return json.loads(path.read_text(encoding='utf-8'))
