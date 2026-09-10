ENGINE_CHOICES = [
    "Standard RapidOCR (2D Layout)",
    "Mode 1: Good (Ultra Fast)",
    "Mode 2: Better (Balanced)",
    "Mode 3: Best (High Precision)"
]

TIER_CONFIGS = {
    "Standard RapidOCR (2D Layout)": {
        "det_limit_side_len": 960,
        "det_thresh": 0.25,
        "box_thresh": 0.45,
        "unclip_ratio": 1.60,
        "text_score": 0.40,
        "score_mode": "fast",
        "enhance_mode": "none",
        "dpi": 300
    },
    "Mode 1: Good (Ultra Fast)": {
        "det_limit_side_len": 736,
        "det_thresh": 0.30,
        "box_thresh": 0.50,
        "unclip_ratio": 1.60,
        "text_score": 0.45,
        "score_mode": "fast",
        "enhance_mode": "none",
        "dpi": 150
    },
    "Mode 2: Better (Balanced)": {
        "det_limit_side_len": 1024,
        "det_thresh": 0.22,
        "box_thresh": 0.42,
        "unclip_ratio": 1.65,
        "text_score": 0.38,
        "score_mode": "fast",
        "enhance_mode": "clahe",
        "dpi": 250
    },
    "Mode 3: Best (High Precision)": {
        "det_limit_side_len": 1536,
        "det_thresh": 0.15,
        "box_thresh": 0.30,
        "unclip_ratio": 1.70,
        "text_score": 0.30,
        "score_mode": "slow",
        "enhance_mode": "adaptive_deblur",
        "dpi": 300
    }
}

LAYOUT_SETTINGS = {
    "model_type": "pp_layout_cdla",
    "conf_thresh": 0.5,
    "iou_thresh": 0.5
}
