<div align="center">

# Document OCR & Layout API (v5)

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/Gradio-5.0+-orange.svg)](https://gradio.app/)
[![OCR](https://img.shields.io/badge/OCR-RapidOCR%20ONNX-teal.svg)](https://github.com/RapidAI/RapidOCR)
[![Layout](https://img.shields.io/badge/Layout-RapidLayout-blueviolet.svg)](https://github.com/RapidAI/RapidLayout)
[![Table](https://img.shields.io/badge/Table-RapidTable-coral.svg)](https://github.com/RapidAI/RapidTable)
[![Tunnel](https://img.shields.io/badge/Tunnel-Cloudflare%20%7C%20Gradio-purple.svg)](https://cloudflare.com/)
</div>

A document OCR and structural parsing service for extracting text, layout elements, and formatted tables from PDF documents. It runs **100% locally** using ONNX runtimes and PyMuPDF with **zero external cloud** dependencies. Monitored 80%+ accuracy.

Extract full documents or custom page ranges into formatted Markdown tables, Word (.docx), plain text, or JSON with automated API integration.

##

> **Demo video** [link](https://youtu.be/85EKcOm-m2I?si=UqkVu-mDTtAm2zD7)

> **Tested Demo Scan:** [ocr_demo_test.pdf](ocr_demo_test.pdf)


---

## Capabilities

- **Document Layout Analysis:** Integrates RapidLayout to classify regions into text, headings, tables, formulas and figures before extraction.
- **Table Structure Recognition:** Routes table regions into RapidTable to reconstruct rows and columns.
- **OCR Engine:**
  - `Mode 1: Good (Ultra Fast)`: 150 DPI rasterization, 736px side limit for high-throughput batch processing with .
  - `Mode 2: Better (Balanced)`: 250 DPI rasterization, 1024px side limit, adaptive CLAHE contrast equalization for **everyday scans.**
  - `Mode 3: Best (High Precision)`: 300 DPI rasterization, 1536px side limit, percentile dynamic range stretch + CLAHE + soft Gaussian unsharp deblurring, and polygon contour mean scoring for **degraded and blurry documents.**
  - `Standard RapidOCR (2D Layout)`: Balanced 300 DPI 2D spatial layout

- **API Architecture:** Full OCR backend works on FastAPI / REST API architecture

- **Universal Dual Tunneling:** Automatically provisions Cloudflare Tunnel (`*.trycloudflare.com`) alongside Gradio Live (`*.gradio.live`).

---

## Startup

### 1. Local Machine / Server

1. Enter the `v5` directory:
```bash
cd v5
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Launch the backend:
```bash
python run.py
```

---

## API Documentation

The OCR service provides a REST endpoint `/predict` accessible via any HTTP client or Python script.

The endpoint accepts 6 positional parameters:
- `file_input`: PDF file upload handle.
- `page_selection`: Target page string (e.g. `( 1 )`, `( 3 or 3-5 )`, `1-4`, or `all`).
- `engine_choice`: OCR precision tier.
- `output_format`: Target file format (`txt`, `md`, `docx`, `json`).
- `enable_layout`: Boolean to enable document layout & table extraction.
- `preserve_layout`: Boolean flag to maintain 2D spatial arrangement.

### Output Sample (JSON)

```json
[
  {
    "page_number": 1,
    "content": "| Item | Quantity | Price |\n|---|---|---|\n| Service A | 1 | $150.00 |"
  }
]
```

---

<details>
<summary><b>API Appendix (Code Examples)</b></summary>

### Python Client (`gradio_client`)

```python
from gradio_client import Client, handle_file

client = Client("https://your-public-url.trycloudflare.com")

result = client.predict(
    handle_file("sample_document.pdf"),
    "( 1 )",
    "Mode 1: Good (Ultra Fast)",
    "md",
    True,
    True,
    api_name="/predict"
)

print(result[0])
```

### Standalone Script Runner

```bash
python api/clnt.py
```

### cURL / HTTP POST

```bash
curl -X POST "https://your-public-url.trycloudflare.com/gradio_api/call/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"path": "sample_document.pdf"},
      "( 1 )",
      "Mode 1: Good (Ultra Fast)",
      "md",
      true,
      true
    ]
  }'
```

</details>

<details>
<summary><b>Appendix: Tools Used</b></summary>

- RapidOCR ONNX
- DBNet (`ch_PP-OCRv4_det`)
- MobileNetV3 / LCNet backbone + Feature Pyramid Network (FPN) + Differentiable Binarization (DB)
- RapidOCR SVTR-LCNet (`ch_PP-OCRv4_rec`) + CTC Greedy Decoder
- Direction Classifier: MobileNet-Cls / ShuffleNet (`ch_ppocr_mobile_v2.0_cls`)
- RapidLayout (PicoDet-LCNet / YOLOv8-DocLayout + Path Aggregation Network (PAN))
- RapidTable SLANet (Structure-Location Alignment Network + MobileNetV3)
- PyMuPDF (`fitz`)
- OpenCV (CLAHE, Gaussian Unsharp Mask)
- Gradio
- Cloudflare Tunnel (`cloudflared`)

</details>

---

