import os
import time
from gradio_client import Client, handle_file

TARGET_URL = "https://your-public-link.gradio.live"
PDF_FILE_PATH = "ocr_demo_test.pdf" if os.path.exists("ocr_demo_test.pdf") else "sample_document.pdf"
PAGE_SELECTION = "( 1 )"
ENGINE_CHOICE = "Mode 1: Good (Ultra Fast)"
OUTPUT_FORMAT = "txt"
ENABLE_LAYOUT = True
PRESERVE_LAYOUT = True

def make_sample_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (600, 300), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((30, 40), "Invoice Number: #10492    Date: 2026-09-06", fill=(0, 0, 0))
        d.text((30, 80), "Client: ACME Corp         Total: $450.00", fill=(0, 0, 0))
        d.text((30, 140), "Document OCR & Layout Verification Page", fill=(0, 0, 0))
        img.save(pdf_path, "PDF", resolution=100.0)

def run_client_req():
    make_sample_pdf(PDF_FILE_PATH)
    print(f"calling {TARGET_URL}", flush=True)

    t0 = time.time()
    try:
        client = Client(TARGET_URL)
        result = client.predict(
            handle_file(PDF_FILE_PATH),
            PAGE_SELECTION,
            ENGINE_CHOICE,
            OUTPUT_FORMAT,
            ENABLE_LAYOUT,
            PRESERVE_LAYOUT,
            api_name="/predict"
        )
        
        el = time.time() - t0
        print(f"done in {el:.2f}s", flush=True)
        
        if isinstance(result, (list, tuple)):
            print(result[0])
            download_info = result[1]
            if download_info:
                file_path = download_info if isinstance(download_info, str) else download_info.get("path", "")
                if file_path and os.path.exists(file_path):
                    dest_file = f"downloaded_ocr_result.{OUTPUT_FORMAT}"
                    with open(file_path, "rb") as src, open(dest_file, "wb") as dst:
                        dst.write(src.read())
                    print(f"saved: {dest_file}", flush=True)
    except Exception as e:
        print(f"err: {e}", flush=True)

if __name__ == "__main__":
    run_client_req()
