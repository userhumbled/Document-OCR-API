import os
import sys
import pathlib
import cv2
import numpy as np
from PIL import Image

cur_dir = pathlib.Path(__file__).parent.resolve()
root_v5 = cur_dir.parent
for p in [str(cur_dir), str(root_v5), str(root_v5 / "file_processor"), str(root_v5 / "main")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import cfg
from layout_proc import reconstruct_text_layout, html_to_markdown_table

_rapid_ocr_inst = None
_layout_engine_inst = None
_table_engine_inst = None
_layout_supported = None
_table_supported = None

def get_rapid_ocr():
    global _rapid_ocr_inst
    if _rapid_ocr_inst is None:
        from rapidocr_onnxruntime import RapidOCR
        _rapid_ocr_inst = RapidOCR()
    return _rapid_ocr_inst

def get_layout_engine():
    global _layout_engine_inst, _layout_supported
    if _layout_supported is False:
        return None
    if _layout_engine_inst is None:
        try:
            from rapid_layout import RapidLayout
            _layout_engine_inst = RapidLayout(conf_thresh=0.5)
            _layout_supported = True
        except Exception:
            _layout_supported = False
            return None
    return _layout_engine_inst

def get_table_engine():
    global _table_engine_inst, _table_supported
    if _table_supported is False:
        return None
    if _table_engine_inst is None:
        try:
            from rapid_table import RapidTable
            _table_engine_inst = RapidTable()
            _table_supported = True
        except Exception:
            _table_supported = False
            return None
    return _table_engine_inst

def apply_enhancement(img_arr, mode="none"):
    if not isinstance(img_arr, np.ndarray) or mode == "none":
        return img_arr
        
    try:
        if len(img_arr.shape) == 2:
            gray = img_arr
        else:
            gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
            
        if mode == "clahe":
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
        elif mode == "adaptive_deblur":
            p_min, p_max = np.percentile(gray, (1, 99))
            if p_max > p_min:
                stretched = np.clip((gray - p_min) * (255.0 / (p_max - p_min)), 0, 255).astype(np.uint8)
            else:
                stretched = gray
                
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            c_img = clahe.apply(stretched)
            
            blur = cv2.GaussianBlur(c_img, (0, 0), sigmaX=1.2)
            unsharp = cv2.addWeighted(c_img, 1.4, blur, -0.4, 0)
            return cv2.cvtColor(unsharp, cv2.COLOR_GRAY2RGB)
            
    except Exception:
        pass
        
    return img_arr

def configure_rapid_ocr(ocr, tier):
    try:
        limit_side_len = tier.get("det_limit_side_len", 960)
        det_thresh = tier.get("det_thresh", 0.25)
        box_thresh = tier.get("box_thresh", 0.45)
        unclip_ratio = tier.get("unclip_ratio", 1.60)
        score_mode = tier.get("score_mode", "fast")
        
        if hasattr(ocr, "text_detector"):
            if hasattr(ocr.text_detector, "preprocess_op") and len(ocr.text_detector.preprocess_op) > 0:
                ocr.text_detector.preprocess_op[0].limit_side_len = limit_side_len
            if hasattr(ocr.text_detector, "postprocess_op"):
                ocr.text_detector.postprocess_op.thresh = det_thresh
                ocr.text_detector.postprocess_op.box_thresh = box_thresh
                ocr.text_detector.postprocess_op.unclip_ratio = unclip_ratio
                ocr.text_detector.postprocess_op.score_mode = score_mode
    except Exception:
        pass

def img_crop_box1(pil_img, box, padding=25):
    w, h = pil_img.size
    try:
        if isinstance(box[0], (list, tuple)):
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
        else:
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
    except Exception:
        return pil_img
        
    x1 = max(0, int(x1) - padding)
    y1 = max(0, int(y1) - padding)
    x2 = min(w, int(x2) + padding)
    y2 = min(h, int(y2) + padding)
    
    if x2 <= x1 or y2 <= y1:
        return pil_img
        
    return pil_img.crop((x1, y1, x2, y2))

def ocr_func2(pil_img, tier, preserve_layout=True):
    ocr = get_rapid_ocr()
    configure_rapid_ocr(ocr, tier)
    
    img_arr = np.array(pil_img.convert("RGB"))
    enhance_mode = tier.get("enhance_mode", "none")
    proc_arr = apply_enhancement(img_arr, enhance_mode)
    
    box_thresh = tier.get("box_thresh", 0.45)
    unclip_ratio = tier.get("unclip_ratio", 1.60)
    text_score = tier.get("text_score", 0.40)
    
    result, _ = ocr(
        proc_arr,
        box_thresh=box_thresh,
        unclip_ratio=unclip_ratio,
        text_score=text_score
    )
    if not result:
        return ""
    return reconstruct_text_layout(result, preserve_layout=preserve_layout)

def tbl_extract_v2(table_crop_img, tier):
    tbl_engine = get_table_engine()
    ocr = get_rapid_ocr()
    configure_rapid_ocr(ocr, tier)
    
    crop_rgb = table_crop_img.convert("RGB")
    crop_arr = np.array(crop_rgb)
    enhance_mode = tier.get("enhance_mode", "none")
    proc_arr = apply_enhancement(crop_arr, enhance_mode)
    
    box_thresh = tier.get("box_thresh", 0.45)
    unclip_ratio = tier.get("unclip_ratio", 1.60)
    text_score = tier.get("text_score", 0.40)
    
    ocr_res, _ = ocr(
        proc_arr,
        box_thresh=box_thresh,
        unclip_ratio=unclip_ratio,
        text_score=text_score
    )
    
    if tbl_engine is not None and ocr_res:
        try:
            ocr_boxes = [item[0] for item in ocr_res]
            ocr_txts = [str(item[1]) for item in ocr_res]
            ocr_scores = [float(item[2]) if len(item) > 2 else 1.0 for item in ocr_res]
            ocr_data = list(zip(ocr_boxes, ocr_txts, ocr_scores))
            
            tbl_res = tbl_engine(crop_arr, ocr_data)
            html_content = getattr(tbl_res, "pred_html", None)
            if not html_content and isinstance(tbl_res, (list, tuple)) and len(tbl_res) > 0:
                html_content = tbl_res[0]
            elif isinstance(tbl_res, str):
                html_content = tbl_res
                
            if html_content:
                md_table = html_to_markdown_table(html_content)
                if md_table.strip():
                    return md_table
        except Exception:
            pass
            
    if ocr_res:
        return reconstruct_text_layout(ocr_res, preserve_layout=True)
    return ""

def ocr_dataproc1(page_image, mode_name="Standard RapidOCR (2D Layout)", enable_layout=True, preserve_layout=True):
    tier = cfg.TIER_CONFIGS.get(mode_name, cfg.TIER_CONFIGS["Standard RapidOCR (2D Layout)"])
    layout_eng = get_layout_engine() if enable_layout else None
    
    if layout_eng is None:
        return ocr_func2(page_image, tier, preserve_layout=preserve_layout)
        
    try:
        np_page = np.array(page_image.convert("RGB"))
        layout_out = layout_eng(np_page)
        
        boxes = None
        labels = None
        if isinstance(layout_out, (list, tuple)):
            if len(layout_out) >= 3:
                boxes = layout_out[0]
                labels = layout_out[2]
            elif len(layout_out) == 2 and isinstance(layout_out[0], list):
                boxes = layout_out[0]
                labels = [getattr(b, "label", "text") for b in boxes]
                
        if not boxes or len(boxes) == 0:
            return ocr_func2(page_image, tier, preserve_layout=preserve_layout)
            
        regions = []
        has_table = False
        for i, b in enumerate(boxes):
            lbl = str(labels[i]).lower() if labels and i < len(labels) else "text"
            if "table" in lbl:
                has_table = True
            if isinstance(b[0], (list, tuple)):
                ys = [p[1] for p in b]
                xs = [p[0] for p in b]
                y_min, x_min = min(ys), min(xs)
            else:
                x_min, y_min = b[0], b[1]
            regions.append((y_min, x_min, b, lbl))
            
        if not has_table:
            return ocr_func2(page_image, tier, preserve_layout=preserve_layout)
            
        regions.sort(key=lambda r: (r[0], r[1]))
        
        page_chunks = []
        for _, _, box, lbl in regions:
            crop_img = img_crop_box1(page_image, box, padding=25)
            
            if "table" in lbl:
                tbl_text = tbl_extract_v2(crop_img, tier)
                if tbl_text.strip():
                    page_chunks.append(tbl_text.strip())
            elif "figure" in lbl or "image" in lbl:
                fig_text = ocr_func2(crop_img, tier, preserve_layout=preserve_layout)
                if fig_text.strip():
                    page_chunks.append(fig_text.strip())
                else:
                    page_chunks.append("[Figure]")
            else:
                txt = ocr_func2(crop_img, tier, preserve_layout=preserve_layout)
                if txt.strip():
                    page_chunks.append(txt.strip())
                    
        result_text = "\n\n".join(page_chunks) if page_chunks else ""
        
        if len(result_text) < 50:
            full_text = ocr_func2(page_image, tier, preserve_layout=preserve_layout)
            if len(full_text) > len(result_text):
                return full_text
                
        return result_text if result_text else ocr_func2(page_image, tier, preserve_layout=preserve_layout)
            
    except Exception:
        return ocr_func2(page_image, tier, preserve_layout=preserve_layout)
