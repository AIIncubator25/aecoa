from __future__ import annotations
from typing import Dict, Any, List, Optional
import yaml

# Load YAML string and extract csv_schema rows if present

def load_yaml_file(text: str) -> Dict[str, Any]:
    return yaml.safe_load(text)

def extract_csv_schema_rows(yaml_text: str) -> List[Dict[str, Any]]:
    data = yaml.safe_load(yaml_text) if yaml_text else {}
    def find_csv_schema(d):
        if isinstance(d, dict):
            if 'csv_schema' in d:
                return d['csv_schema']
            for v in d.values():
                found = find_csv_schema(v)
                if found:
                    return found
        return None
    csv_schema = find_csv_schema(data) or {}
    cols = csv_schema.get('columns') or csv_schema.get('columns_pretty') or []
    rows = csv_schema.get('rows', [])
    norm_rows = []
    for r in rows:
        if isinstance(r, dict):
            norm_rows.append(r)
        elif isinstance(r, list):
            entry = {}
            for i, c in enumerate(cols):
                if i < len(r):
                    entry[c] = r[i]
            norm_rows.append(entry)
    return norm_rows
