from typing import Dict, Any

def generate_pdf_report(data: Dict[str, Any]) -> bytes:
    return b"%PDF-1.4 stub report"

def generate_excel_report(data: Dict[str, Any]) -> bytes:
    return b"xlsx stub report"

def generate_png_report(data: Dict[str, Any]) -> bytes:
    return b"png stub report"
