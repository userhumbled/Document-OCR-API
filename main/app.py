import os
import sys
import pathlib

cur_dir = pathlib.Path(__file__).parent.resolve()
root_v5 = cur_dir.parent
for p in [str(cur_dir), str(root_v5), str(root_v5 / "api"), str(root_v5 / "file_processor")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import gradio as gr
import cfg
from doc_proc import process_document
from export_dat import update_api_helper

def on_file_upload(file_obj):
    if file_obj:
        path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        print(f"file uploaded: {os.path.basename(path)}", flush=True)

def on_page_change(page_val, engine_val, format_val, layout_val):
    return update_api_helper(page_val, engine_val, format_val, layout_val)

def on_engine_change(page_val, engine_val, format_val, layout_val):
    return update_api_helper(page_val, engine_val, format_val, layout_val)

def on_format_change(page_val, engine_val, format_val, layout_val):
    return update_api_helper(page_val, engine_val, format_val, layout_val)

def on_layout_toggle(layout_val, page_val, engine_val, format_val):
    return update_api_helper(page_val, engine_val, format_val, layout_val)

def create_ui():
    with gr.Blocks(title="Document OCR & Layout API (v5)") as demo:
        gr.Markdown("# Document OCR & Layout API (v5)")
        gr.Markdown("Local Document OCR, Layout Parsing, and Table Extraction Service.")
        
        with gr.Row():
            with gr.Column(scale=1):
                file_input = gr.File(label="Upload PDF Document", file_types=[".pdf"])
                page_input = gr.Textbox(
                    label="Page Selection",
                    value="( 1 )",
                    placeholder="e.g. ( 3 or 3-5 ) or 1, 3, 5 or 1-4 or all"
                )
                engine_input = gr.Radio(
                    choices=cfg.ENGINE_CHOICES,
                    value="Standard RapidOCR (2D Layout)",
                    label="OCR Accuracy Tier"
                )
                format_input = gr.Dropdown(
                    choices=["txt", "md", "docx", "json"],
                    value="txt",
                    label="Output Format"
                )
                layout_check = gr.Checkbox(
                    label="Enable Document Layout & Table Analysis",
                    value=True
                )
                spatial_check = gr.Checkbox(
                    label="Preserve 2D Spatial Layout",
                    value=True
                )
                process_btn = gr.Button("Process Document", variant="primary")
                
            with gr.Column(scale=1):
                output_text = gr.Textbox(label="Processed Content Display", lines=14)
                output_file = gr.File(label="Download File Artifact")
                
                gr.Markdown("## Rest API Guide:")
                code_display = gr.Code(
                    label="Client Python Script (gradio_client):",
                    language="python",
                    value=update_api_helper("( 1 )", "Standard RapidOCR (2D Layout)", "txt", True)
                )
                
        file_input.change(fn=on_file_upload, inputs=[file_input], outputs=[])
        format_input.change(
            fn=on_format_change,
            inputs=[page_input, engine_input, format_input, layout_check],
            outputs=[code_display]
        )
        page_input.change(
            fn=on_page_change,
            inputs=[page_input, engine_input, format_input, layout_check],
            outputs=[code_display]
        )
        engine_input.change(
            fn=on_engine_change,
            inputs=[page_input, engine_input, format_input, layout_check],
            outputs=[code_display]
        )
        layout_check.change(
            fn=on_layout_toggle,
            inputs=[layout_check, page_input, engine_input, format_input],
            outputs=[code_display]
        )
        
        process_btn.click(
            fn=process_document,
            inputs=[file_input, page_input, engine_input, format_input, layout_check, spatial_check],
            outputs=[output_text, output_file, code_display],
            api_name="predict"
        )
        return demo

demo = create_ui()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
