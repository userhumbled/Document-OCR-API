import io
from PIL import Image
try:
    import pymupdf as fitz
except ImportError:
    import fitz

def get_pdf_page_count(pdf_path):
    with fitz.open(pdf_path) as doc:
        return len(doc)

def render_pdf_page(pdf_path, page_num, dpi=300):
    with fitz.open(pdf_path) as doc:
        if 1 <= page_num <= len(doc):
            page = doc[page_num - 1]
            pix = page.get_pixmap(dpi=dpi)
            return Image.open(io.BytesIO(pix.tobytes("png")))
    return None

def parse_page_data(page_str, total_pages):
    if not page_str:
        return [1] if total_pages >= 1 else []
        
    raw_str = str(page_str).strip().lower()
    if raw_str in ("all", "*", "everything"):
        return list(range(1, total_pages + 1))
        
    cleaned = raw_str.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ")
    cleaned = cleaned.replace(" or ", ",").replace(" and ", ",").replace(";", ",").replace("&", ",")
    
    pages = set()
    tokens = [t.strip() for t in cleaned.split(",") if t.strip()]
    
    for token in tokens:
        sub_tokens = token.split()
        for sub in sub_tokens:
            sub = sub.strip()
            if "-" in sub:
                range_parts = sub.split("-")
                if len(range_parts) == 2 and range_parts[0].strip().isdigit() and range_parts[1].strip().isdigit():
                    start_p = int(range_parts[0].strip())
                    end_p = int(range_parts[1].strip())
                    if start_p <= end_p:
                        for p in range(start_p, end_p + 1):
                            if 1 <= p <= total_pages:
                                pages.add(p)
                    else:
                        for p in range(end_p, start_p + 1):
                            if 1 <= p <= total_pages:
                                pages.add(p)
            elif sub.isdigit():
                p = int(sub)
                if 1 <= p <= total_pages:
                    pages.add(p)
                    
    result = sorted(list(pages))
    if not result:
        return [1] if total_pages >= 1 else []
    return result
