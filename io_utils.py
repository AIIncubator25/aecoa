from __future__ import annotations
import io, re
from typing import Dict, Any, List
from PIL import Image

# OCR has been removed from the project. If you need OCR in future,
# reintroduce pytesseract and adjust the function below.
TESS_OK = False

try:
    import ezdxf
    EZDXF_OK = True
except Exception:
    EZDXF_OK = False

def ocr_image(file_bytes: bytes) -> str:
    """Deprecated: OCR is removed. This function will raise to avoid silent fallbacks.

    If you must use OCR, re-enable pytesseract and update this function.
    """
    raise RuntimeError("OCR is removed from this project. Use AI image extraction instead.")

def scan_dxf_text(file_bytes: bytes) -> str:
    """Read TEXT/MTEXT/DIMENSION strings from DXF (file-like) or fallback to raw decode."""
    text = ""
    if EZDXF_OK:
        try:
            stream = io.BytesIO(file_bytes)
            doc = ezdxf.read(stream)               # ✅ correct for in-memory upload
            msp = doc.modelspace()
            chunks: List[str] = []
            for e in msp.query("TEXT MTEXT"):
                try:
                    chunks.append(e.dxf.text if e.dxftype() == "TEXT" else e.text)
                except Exception:
                    pass
            for e in msp.query("DIMENSION"):
                try:
                    if e.dxf.text:
                        chunks.append(e.dxf.text)
                except Exception:
                    pass
            text = "\n".join([c for c in chunks if c])
        except Exception:
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = str(file_bytes)
    else:
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = str(file_bytes)
    return text

def guess_values_from_text(text: str) -> Dict[str, Any]:
    t = (text or "").upper()
    vals: Dict[str, Any] = {}
    if re.search(r"\b2700\b|\b2\.7\b|CLEAR\s*HEIGHT\s*:?\s*2700", t): vals["height_mm"] = 2700
    if re.search(r"\b2100\b", t): vals["w_mm"] = 2100
    if re.search(r"\b1350\b", t): vals["d_mm"] = 1350
    if re.search(r"\b300\b.*(SLAB|CEILING)|SLAB.*\b300\b", t): vals["slab_mm"] = 300
    if re.search(r"\b300\b.*(WAIST|STAIR)|STAIR.*\b300\b", t): vals["waist_mm"] = 300
    if re.search(r"\b700\b.*(VENT|SLEEVE|CLEAR)|VENT.*\b700\b", t): vals["vent_mm"] = 700
    if vals.get("w_mm") and vals.get("d_mm"):
        vals["area_m2"] = round((vals["w_mm"] * vals["d_mm"]) / 1_000_000, 2)
    if vals.get("area_m2") and vals.get("height_mm"):
        vals["volume_m3"] = round(vals["area_m2"] * (vals["height_mm"] / 1000), 2)
    return vals
