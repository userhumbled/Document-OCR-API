import os
import sys
import time
import pathlib
import threading

cur_dir = pathlib.Path(__file__).parent.resolve()
root_v5 = cur_dir.parent
for p in [str(cur_dir), str(root_v5), str(root_v5 / "api"), str(root_v5 / "main")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import cfg
from pdf_hlpr import get_pdf_page_count, render_pdf_page, parse_page_data
from ocr_eng import ocr_dataproc1
from export_dat import export_doc_file, update_api_helper

job_lock = threading.Lock()
job_count = 0

def process_document(pdf_file, page_selection, engine_choice, output_format, enable_layout=True, preserve_layout=True, request=None):
    global job_count
    with job_lock:
        job_count += 1
        job_id = job_count

    if not pdf_file:
        print("no file uploaded", flush=True)
        return "Error: Please upload a PDF file.", None, update_api_helper(page_selection, engine_choice, output_format, enable_layout)

    pdf_path = pdf_file.name if hasattr(pdf_file, "name") else str(pdf_file)
    file_name = os.path.basename(pdf_path)

    print(f"req #{job_id}: {file_name}, pgs: {page_selection}, mode: {engine_choice}, layout: {enable_layout}", flush=True)

    try:
        total_pages = get_pdf_page_count(pdf_path)
    except Exception as e:
        print(f"pdf open err: {e}", flush=True)
        return f"Error opening PDF: {e}", None, update_api_helper(page_selection, engine_choice, output_format, enable_layout)

    target_pages = parse_page_data(page_selection, total_pages)
    if not target_pages:
        print(f"bad page target: {page_selection}", flush=True)
        return "Error: No valid pages selected.", None, update_api_helper(page_selection, engine_choice, output_format, enable_layout)

    tier = cfg.TIER_CONFIGS.get(engine_choice, cfg.TIER_CONFIGS["Standard RapidOCR (2D Layout)"])
    render_dpi = tier.get("dpi", 300)

    page_results = []
    for page_num in target_pages:
        page_img = render_pdf_page(pdf_path, page_num, dpi=render_dpi)
        if page_img is None:
            continue
            
        print(f"processing p{page_num}", flush=True)
        extracted_text = ocr_dataproc1(
            page_img,
            mode_name=engine_choice,
            enable_layout=enable_layout,
            preserve_layout=preserve_layout
        )
        print(f"p{page_num} done: {len(extracted_text)} chars", flush=True)
        page_results.append((page_num, extracted_text))

    if not page_results:
        print("no text extracted", flush=True)
        return "Error: No content extracted.", None, update_api_helper(page_selection, engine_choice, output_format, enable_layout)

    display_text, out_path = export_doc_file(page_results, output_format)
    print(f"done: {os.path.basename(out_path)}", flush=True)

    code_helper = update_api_helper(page_selection, engine_choice, output_format, enable_layout)
    return display_text, out_path, code_helper
