#!/usr/bin/env python3
"""
Wan2GP Video Generator - Standalone script using gradio_client.
Called by wan2gp.py via subprocess to avoid async/sync conflicts.

Usage:
    python wan2gp_generator.py --prompt "a flying panda" --width 832 --height 480 --frames 81

Outputs JSON to stdout: {"video_url": "...", "status": "completed"}
"""
import sys
import json
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="Generate video via Wan2GP")
    parser.add_argument("--base-url", default="http://localhost:7860")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--frames", type=int, default=81)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=6.0)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    result = generate_video(args)
    print(json.dumps(result))


def generate_video(args):
    """Generate video using gradio_client which handles sessions correctly."""
    try:
        from gradio_client import Client
    except ImportError:
        return {"error": "gradio_client not installed", "status": "error"}

    # Step 0: Connect
    print(f"[Wan2GP] Connecting to {args.base_url}...", file=sys.stderr)
    try:
        client = Client(args.base_url, verbose=False)
    except Exception as e:
        return {"error": f"Connection failed: {e}", "status": "error"}

    # Step 1: Set prompt via process_prompt_and_add_tasks
    # Endpoint signature: wizard_prompt_activated, model_mode, prompt
    # model_mode must be one of: 't2v', 'moviigen', 't2v_fusionix', 't2v_sf'
    print(f"[Wan2GP] Setting prompt: '{args.prompt[:60]}...'", file=sys.stderr)
    try:
        result = client.predict(
            "on",       # wizard_prompt_activated
            "t2v",      # model_mode (text-to-video)
            args.prompt,  # prompt
            api_name="/process_prompt_and_add_tasks",
        )
        print(f"[Wan2GP] Task added: {str(result)[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[Wan2GP] process_prompt failed ({e})", file=sys.stderr)
        return {"error": f"Failed to set prompt: {e}", "status": "error"}

    # Step 2: Init generation
    print("[Wan2GP] Initializing generation...", file=sys.stderr)
    try:
        result = client.predict(api_name="/init_generate")
        print(f"[Wan2GP] Init result: {str(result)[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[Wan2GP] init_generate warning: {e}", file=sys.stderr)

    # Step 3: Prepare and start generation
    print("[Wan2GP] Preparing generation...", file=sys.stderr)
    try:
        result = client.predict(api_name="/prepare_generate_video")
        print(f"[Wan2GP] Prepare result: {str(result)[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[Wan2GP] prepare warning: {e}", file=sys.stderr)

    # Step 4: Poll gallery for output video
    print(f"[Wan2GP] Polling gallery (timeout={args.timeout}s)...", file=sys.stderr)
    start_time = time.time()
    poll_interval = 5

    while time.time() - start_time < args.timeout:
        elapsed = int(time.time() - start_time)
        try:
            # refresh_gallery returns gallery data
            result = client.predict(api_name="/refresh_gallery")
            video_url = extract_video_url(result, args.base_url)
            if video_url:
                print(f"[Wan2GP] Video found at {elapsed}s!", file=sys.stderr)
                return {
                    "video_url": video_url,
                    "url": video_url,
                    "status": "completed",
                    "elapsed_seconds": elapsed,
                }

            if elapsed % 30 == 0 and elapsed > 0:
                print(f"[Wan2GP] Still waiting... {elapsed}s elapsed", file=sys.stderr)
        except Exception as e:
            if elapsed % 30 == 0:
                print(f"[Wan2GP] Poll error ({elapsed}s): {str(e)[:80]}", file=sys.stderr)

        time.sleep(poll_interval)

    return {"error": f"Timeout after {args.timeout}s", "status": "timeout"}


def extract_video_url(data, base_url):
    """Recursively extract video URL from Gradio gallery response."""
    if not data:
        return None

    if isinstance(data, (tuple, list)):
        for item in data:
            url = extract_video_url(item, base_url)
            if url:
                return url
        return None

    if isinstance(data, dict):
        orig_name = data.get("orig_name", "")
        if orig_name.lower().endswith((".mp4", ".webm", ".avi", ".gif", ".mov")):
            url = data.get("url", "")
            if url:
                if url.startswith("/"):
                    return f"{base_url}{url}"
                return url

            path = data.get("path", "")
            if path:
                return f"{base_url}/gradio_api/file={path}"

        for key in ("video", "image", "data", "value"):
            if key in data:
                url = extract_video_url(data[key], base_url)
                if url:
                    return url

    if isinstance(data, str):
        if data.lower().endswith((".mp4", ".webm", ".gif", ".mov")):
            if data.startswith("http"):
                return data
            if data.startswith("/"):
                return f"{base_url}{data}"

    return None


if __name__ == "__main__":
    main()