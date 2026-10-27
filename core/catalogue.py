"""Load the database catalogue from the project's JSON data file."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "databases.json"

def load_databases(path=DATA_FILE):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("databases.json must contain a list")
    return data
