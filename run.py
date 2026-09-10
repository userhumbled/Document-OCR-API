import os
import sys
import time
import socket
import pathlib
import platform
import threading
import subprocess
import urllib.request
import re
import tempfile
import shutil

cur_dir = pathlib.Path(__file__).parent.resolve()
for p in [str(cur_dir), str(cur_dir / "main"), str(cur_dir / "api"), str(cur_dir / "file_processor")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import gradio as gr
from app import demo

def get_free_port(preferred=7860):
    for p in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]

def ensure_cloudflared_binary():
    candidates = [
        shutil.which("cloudflared"),
        os.path.join(os.getcwd(), "cloudflared.exe"),
        os.path.join(os.getcwd(), "cloudflared.EXE"),
        os.path.join(os.getcwd(), "cloudflared"),
        os.path.join(str(cur_dir), "cloudflared.exe"),
        os.path.join(str(cur_dir), "cloudflared.EXE"),
        os.path.join(str(cur_dir.parent), "cloudflared.exe"),
        os.path.join(str(cur_dir.parent), "cloudflared.EXE"),
        os.path.join(os.path.expanduser("~"), ".cloudflared", "cloudflared.exe"),
        os.path.join(tempfile.gettempdir(), "cloudflared.exe"),
        "/usr/local/bin/cloudflared",
        "/usr/bin/cloudflared",
    ]
    for p in candidates:
        if p and os.path.exists(p) and os.path.getsize(p) > 1000000:
            return os.path.abspath(p)

    sys_name = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if ("arm" in machine or "aarch64" in machine) else "amd64"
    
    if "windows" in sys_name:
        filename = "cloudflared.exe"
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-{arch}.exe"
    elif "darwin" in sys_name:
        filename = "cloudflared"
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}"
    else:
        filename = "cloudflared"
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}"

    target = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(target) and os.path.getsize(target) > 5000000:
        return os.path.abspath(target)

    try:
        print(f"downloading cloudflared ({sys_name}-{arch})", flush=True)
        urllib.request.urlretrieve(url, target)
        try:
            os.chmod(target, 0o777)
        except Exception:
            pass
        if os.path.exists(target) and os.path.getsize(target) > 5000000:
            return os.path.abspath(target)
    except Exception as e:
        print(f"tunnel download notice: {e}", flush=True)

    return None

def start_cloudflare_tunnel(port=7860):
    cloudflared = ensure_cloudflared_binary()
    if not cloudflared:
        print("cloudflared not found", flush=True)
        return None

    def tunnel_worker():
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            proc = subprocess.Popen(
                [cloudflared, "tunnel", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )

            def drain_stdout():
                try:
                    for _ in iter(proc.stdout.readline, ""):
                        pass
                except Exception:
                    pass
            threading.Thread(target=drain_stdout, daemon=True).start()

            url_found = False
            for line in iter(proc.stderr.readline, ""):
                if not url_found and "trycloudflare.com" in line:
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        url = match.group(0)
                        url_found = True
                        print(f"cloudflare tunnel: {url}", flush=True)
        except Exception as e:
            print(f"tunnel err: {e}", flush=True)

    t = threading.Thread(target=tunnel_worker, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    try:
        gr.close_all()
    except Exception:
        pass
        
    port = get_free_port(preferred=7860)
    print(f"server starting on port {port}", flush=True)
    
    start_cloudflare_tunnel(port=port)
    time.sleep(2)
    
    try:
        res = demo.launch(server_name="0.0.0.0", server_port=port, share=True, prevent_thread_lock=True)
        share_url = getattr(demo, "share_url", None)
        if not share_url and isinstance(res, (tuple, list)) and len(res) >= 3:
            share_url = res[2]
        if share_url:
            print(f"gradio share: {share_url}", flush=True)
    except Exception as e:
        print(f"gradio share notice: {e}", flush=True)
        demo.launch(server_name="0.0.0.0", server_port=port, share=False, prevent_thread_lock=True)

    print("server listening", flush=True)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("stopping server", flush=True)
    finally:
        try:
            demo.close()
        except Exception:
            pass
        print("server stopped", flush=True)
