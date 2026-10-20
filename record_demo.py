"""Records the Streamlit demo as 4K frames (1920x1080 @2x) with system Chrome, then writes an ffmpeg concat list."""
import sys, time, pathlib
from playwright.sync_api import sync_playwright

TOPIC = sys.argv[1]
OUT = pathlib.Path(sys.argv[2]); FR = OUT / "frames"; FR.mkdir(parents=True, exist_ok=True)
frames = []  # (filename, duration seconds)

def shot(page, dur=None, last=[None]):
    now = time.time()
    if frames and dur is None:   # real elapsed since previous frame
        frames[-1] = (frames[-1][0], now - last[0])
    n = f"f{len(frames):05d}.jpg"
    page.screenshot(path=str(FR / n), type="jpeg", quality=88)
    frames.append((n, dur if dur is not None else 0.5)); last[0] = time.time()

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="dark")
    page = ctx.new_page()
    page.goto("http://localhost:8511")
    box = page.locator('textarea[data-testid="stChatInputTextArea"]')
    box.wait_for(timeout=60000); time.sleep(3)
    shot(page, 2.5)
    page.screenshot(path=str(OUT / "01-home.png"))
    box.click()
    for ch in TOPIC:
        page.keyboard.type(ch); shot(page, 0.07)
    shot(page, 0.8)
    page.keyboard.press("Enter")
    t0 = time.time()
    shot(page, 0.5)
    while True:
        shot(page)  # real-time duration
        if time.time() - t0 > 600: break
        if time.time() - t0 > 15 and page.locator('[data-testid="stStatusWidget"]').count() == 0 \
           and page.locator('[data-testid="stChatMessage"], [data-testid="stMarkdownContainer"]').count() > 3 \
           and "Phase 3" in page.inner_text("body") and page.locator('text=References').count() >= 0:
            # stop once running-indicator is gone
            if not page.locator('[data-testid="stStatusWidget"]').is_visible():
                break
    time.sleep(2); shot(page, 3.0)
    page.screenshot(path=str(OUT / "03-report.png"))
    (OUT / "report.txt").write_text(page.inner_text("body"), encoding="utf8")
    print("finished in", int(time.time() - t0), "s,", len(frames), "frames")
    ctx.close(); b.close()

with open(OUT / "frames.txt", "w") as f:
    for n, d in frames:
        f.write(f"file 'frames/{n}'\nduration {max(d, 0.03):.3f}\n")
    f.write(f"file 'frames/{frames[-1][0]}'\n")
