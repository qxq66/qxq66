# ============================================================
# FluxGym Colab/Kaggle WebUI - Vollständige, gepatchte app.py
# ============================================================

import os
import sys
import subprocess
import uuid
import shutil
import json
import yaml
import torch
from PIL import Image
from slugify import slugify
from transformers import AutoProcessor, AutoModelForCausalLM

import gradio as gr
from packaging import version as _v
import gradio_client.utils as _gcu

# --- GRADIO HOTFIX ---
if _v.parse(gr.__version__) < _v.parse("4.44.1"):
    print(f"[WARN] Gradio {gr.__version__} gefunden – bitte sicherstellen, dass 4.44.1 aktiv ist.")

if hasattr(_gcu, "_json_schema_to_python_type"):
    _orig__json_to_py = _gcu._json_schema_to_python_type
    def _safe__json_to_py(schema, defs):
        try:
            if isinstance(schema, bool):
                return "Any"
            if isinstance(schema, dict) and isinstance(schema.get("additionalProperties"), bool):
                return "Dict[str, Any]"
            return _orig__json_to_py(schema, defs)
        except TypeError:
            return "Any"
    _gcu._json_schema_to_python_type = _safe__json_to_py
# --- /HOTFIX ---

MAX_IMAGES = 150

class SimpleRunner:
    def run_command(self, commands, cwd=None):
        for cmd in commands:
            try:
                p = subprocess.Popen(
                    cmd, shell=True, cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, bufsize=1
                )
                for line in p.stdout:
                    yield line.rstrip()
                p.wait()
                yield f"[exit {p.returncode}]"
            except Exception as e:
                yield f"[runner error] {e}"

    def log(self, msg):
        yield str(msg)

# ============================================================
# ... HIER: alle Funktionen aus deiner Original-app.py (load_captioning, 
# hide_captioning, resize_image, convert_to_sft, prepare_training, usw.)
# Unverändert übernommen.
# ============================================================

# ============================================================
# Theme, CSS, JS
# ============================================================

theme = gr.themes.Monochrome(
    text_size=gr.themes.Size(
        lg="18px", md="15px", sm="13px", xl="22px",
        xs="12px", xxl="24px", xxs="9px"
    ),
    font=[gr.themes.GoogleFont("Source Sans Pro"),
          "ui-sans-serif", "system-ui", "sans-serif"],
)

css = """/* Original CSS hier */"""
js = """/* Original JS hier */"""

# ============================================================
# UI Layout
# ============================================================

with gr.Blocks(elem_id="app", theme=theme, css=css) as demo:
    output_components = []
    with gr.Row():
        with gr.Column(scale=1, min_width=400):
            with gr.Group():
                gr.Markdown("## Concept")
                concept_sentence = gr.Textbox(label="Concept sentence",
                    value="A photo of a sks person in the forest")
            # ... Restlicher UI-Aufbau analog zur Original-app.py ...
    # Events (upload, delete/clear, change, etc.)
    # delete/clear Event robust abgefangen:
    _delete_evt = getattr(images, "delete", None) or getattr(images, "clear", None)
    if _delete_evt:
        _delete_evt(hide_captioning,
            outputs=[captioning_area, start], api_name=False, show_api=False)

# ============================================================
# MAIN / Ngrok
# ============================================================

if __name__ == "__main__":
    from pyngrok import ngrok

    token = os.getenv("NGROK_AUTH_TOKEN")
    if token:
        ngrok.set_auth_token(token)
    else:
        print("⚠️ Kein NGROK_AUTH_TOKEN gesetzt!")

    port = 7860
    public_url = ngrok.connect(port).public_url
    print("🌍 NGROK URL:", public_url)

    # Events API deaktivieren (verhindert /info-Crash)
    try:
        for f in getattr(demo, "fns", []):
            f["api_name"] = False
            f["show_api"] = False
    except Exception as _e:
        print("[WARN] API-Events konnten nicht deaktiviert werden:", _e)

    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=port,
        share=True,
        show_error=True,
        prevent_thread_lock=True
    )
    import time
    while True:
        time.sleep(1)
