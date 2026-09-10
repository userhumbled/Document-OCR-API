import re
import numpy as np

def make_box_item(box, text, score=1.0):
    t = str(text).strip()
    try:
        if isinstance(box[0], (list, tuple, np.ndarray)):
            xs = [float(p[0]) for p in box]
            ys = [float(p[1]) for p in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
        else:
            x_min, y_min, x_max, y_max = float(box[0]), float(box[1]), float(box[2]), float(box[3])
    except Exception:
        x_min, x_max, y_min, y_max = 0.0, 100.0, 0.0, 20.0
    h = max(2.0, y_max - y_min)
    w = max(2.0, x_max - x_min)
    return {
        "box": box,
        "text": t,
        "score": float(score) if score is not None else 1.0,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "center_x": (x_min + x_max) / 2.0,
        "center_y": (y_min + y_max) / 2.0,
        "height": h,
        "width": w,
        "char_w": w / max(1, len(t))
    }

def reconstruct_text_layout(raw_results, preserve_layout=True):
    if not raw_results:
        return ""
    blocks = []
    for item in raw_results:
        if not item or len(item) < 2:
            continue
        box = item[0]
        text = str(item[1]).strip()
        score = item[2] if len(item) > 2 else 1.0
        if text:
            blocks.append(make_box_item(box, text, score))
    if not blocks:
        return ""

    blocks.sort(key=lambda b: (b["y_min"], b["x_min"]))
    
    char_widths = [b["char_w"] for b in blocks if len(b["text"]) >= 2]
    ref_char_w = float(np.median(char_widths)) if char_widths else 10.0
    ref_char_w = max(3.0, min(50.0, ref_char_w))
    
    heights = [b["height"] for b in blocks]
    ref_h = float(np.median(heights)) if heights else 20.0
    ref_h = max(6.0, min(80.0, ref_h))
    
    lines = []
    for b in blocks:
        best_line = None
        best_dist = float("inf")
        for line in lines:
            l_top = min(x["y_min"] for x in line)
            l_bot = max(x["y_max"] for x in line)
            l_avg_y = sum(x["center_y"] for x in line) / len(line)
            l_h = max(l_bot - l_top, ref_h)
            overlap = min(b["y_max"], l_bot) - max(b["y_min"], l_top)
            ratio = overlap / min(b["height"], l_h) if min(b["height"], l_h) > 0 else 0
            c_dist = abs(b["center_y"] - l_avg_y)
            if ratio >= 0.45 or c_dist < (0.42 * l_h):
                if c_dist < best_dist:
                    best_dist = c_dist
                    best_line = line
        if best_line is not None:
            best_line.append(b)
        else:
            lines.append([b])
            
    lines.sort(key=lambda l: min(b["y_min"] for b in l))
    
    if not preserve_layout:
        res = []
        for line in lines:
            line.sort(key=lambda b: b["x_min"])
            res.append(" ".join(b["text"] for b in line))
        return "\n".join(res)
        
    page_min_x = min(b["x_min"] for b in blocks)
    rendered_lines = []
    prev_y_bot = None
    
    for line in lines:
        line.sort(key=lambda b: (b["x_min"], b["y_min"]))
        l_top = min(b["y_min"] for b in line)
        l_bot = max(b["y_max"] for b in line)
        
        if prev_y_bot is not None:
            v_gap = l_top - prev_y_bot
            if v_gap > 0.75 * ref_h:
                blank_lines = max(1, min(4, int(round(v_gap / ref_h)) - 1))
                for _ in range(blank_lines):
                    rendered_lines.append("")
                    
        line_buf = []
        prev_b = None
        for b in line:
            target_col = int(round((b["x_min"] - page_min_x) / ref_char_w))
            target_col = max(0, min(180, target_col))
            cur_len = len("".join(line_buf))
            if prev_b is None:
                if target_col > 0:
                    line_buf.append(" " * target_col)
            else:
                gap = b["x_min"] - prev_b["x_max"]
                if gap > (ref_char_w * 0.35):
                    spaces = max(1, target_col - cur_len)
                    line_buf.append(" " * spaces)
                elif gap > 1.0:
                    line_buf.append(" ")
            line_buf.append(b["text"])
            prev_b = b
            
        rendered_lines.append("".join(line_buf).rstrip())
        prev_y_bot = l_bot
        
    return "\n".join(rendered_lines)

def html_to_markdown_table(html_str):
    if not html_str or "table" not in html_str.lower():
        return html_str or ""
        
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html_str, flags=re.IGNORECASE | re.DOTALL)
    if not rows:
        return re.sub(r"<[^>]+>", " ", html_str).strip()
        
    grid = []
    for r in rows:
        cells = re.findall(r"<(?:td|th)[^>]*>(.*?)</(?:td|th)>", r, flags=re.IGNORECASE | re.DOTALL)
        clean_cells = [re.sub(r"<[^>]+>", "", c).strip().replace("\n", " ") for c in cells]
        if clean_cells:
            grid.append(clean_cells)
            
    if not grid:
        return ""
        
    max_cols = max(len(r) for r in grid)
    if max_cols == 0:
        return ""
        
    norm_grid = []
    for r in grid:
        padded = r + [""] * (max_cols - len(r))
        norm_grid.append(padded)
        
    md_lines = []
    header = norm_grid[0]
    md_lines.append("| " + " | ".join(c if c else " " for c in header) + " |")
    md_lines.append("| " + " | ".join("---" for _ in range(max_cols)) + " |")
    
    for row in norm_grid[1:]:
        md_lines.append("| " + " | ".join(c if c else " " for c in row) + " |")
        
    return "\n".join(md_lines)
