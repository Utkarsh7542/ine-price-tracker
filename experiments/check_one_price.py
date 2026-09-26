# quick script to grab one price off the INE store, just to make sure the
# whole click-through works before I build the real thing on top of it.

import random
import re
import time
from playwright.sync_api import sync_playwright

URL = "https://demo.inelabteamdev.com/item/2290"
MAX_TRIES = 12

# runs before the page's own code loads. hides the flag that says "i'm a bot".
no_webdriver = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"

# red dot that follows the mouse so i can actually watch it move + click
cursor_dot = """
const d=document.createElement('div');
d.style.cssText='position:fixed;z-index:99999;width:16px;height:16px;border-radius:50%;background:rgba(255,40,40,.55);border:2px solid #ff2828;pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px';
addEventListener('DOMContentLoaded',()=>document.body.appendChild(d));
addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px';});
addEventListener('mousedown',()=>d.style.background='rgba(40,140,255,.8)');
addEventListener('mouseup',()=>d.style.background='rgba(255,40,40,.55)');
"""

# the price shown on screen is full of fake numbers + invisible characters, so
# reading the text doesn't work. this digs the real price object out of react.
read_quote = r"""
() => {
  const p = document.querySelector('.offer-panel');
  if (!p) return null;
  const k = Object.keys(p).find(k => k.startsWith('__reactFiber$'));
  if (!k) return null;
  let n = p[k], hops = 0;
  while (n && hops < 80) {
    let h = n.memoizedState, c = 0;
    while (h && c < 40) {
      const v = h.memoizedState;
      if (v && v.quote && typeof v.quote === 'object' && 'shown' in v.quote)
        return { phase: v.phase, quote: v.quote };
      h = h.next; c++;
    }
    n = n.return; hops++;
  }
  return null;
}
"""


def start_chrome(pw):
    flags = ["--disable-blink-features=AutomationControlled"]
    try:
        # use my real chrome, looks more legit than the bundled one
        return pw.chromium.launch(headless=False, channel="chrome", args=flags, slow_mo=40)
    except Exception:
        return pw.chromium.launch(headless=False, args=flags, slow_mo=40)


def popup_showing(page):
    return page.locator(".consent-scrim").count() > 0


def kill_popup(page):
    # if the cookie popup's dark cover is there, click Allow and wait for it to go
    if not popup_showing(page):
        return
    try:
        page.locator('.consent-scrim button[aria-label="Allow cookies"]').click(timeout=2000)
        page.locator(".consent-scrim").first.wait_for(state="detached", timeout=3000)
        print("  cleared the cookie popup")
    except Exception:
        pass


def wait_no_popup(page):
    # never touch the page while the popup is covering it
    for _ in range(20):
        if not popup_showing(page):
            return
        kill_popup(page)
        time.sleep(0.3)


def enabled(loc):
    try:
        return loc.is_enabled(timeout=500)
    except Exception:
        return False


def wake_button(page, btn):
    # the button is dead until you move the mouse over the price box ~8 times
    # and hang around for ~600ms, so wiggle the mouse over it
    box = page.locator(".offer-panel").bounding_box()
    if not box:
        return
    for i in range(24):
        x = box["x"] + 15 + random.uniform(0, max(1, box["width"] - 30))
        y = box["y"] + 8 + random.uniform(0, max(1, box["height"] - 16))
        page.mouse.move(x, y, steps=random.randint(4, 9))
        time.sleep(random.uniform(0.05, 0.12))
        if i >= 8 and enabled(btn):
            break
    time.sleep(0.4)


def click_check_price(page):
    # clear the popup, wake the button, click it. a failed click is almost
    # always a popup that showed up late, so clear it and try the click again.
    for _ in range(3):
        wait_no_popup(page)
        btn = page.get_by_role("button", name=re.compile("check today|retry|check again", re.I)).first
        if not enabled(btn):
            wake_button(page, btn)
        try:
            btn.click(timeout=5000)
            return True
        except Exception:
            kill_popup(page)
    return False


def wait_for_price(page, secs=12):
    stop = time.time() + secs
    while time.time() < stop:
        state = page.evaluate(read_quote)
        if state and state.get("phase") == "success" and state.get("quote"):
            return "ok", state["quote"]
        body = page.locator("body").inner_text()
        if "challenge_failed" in body or "Couldn" in body:
            return "failed", None
        time.sleep(0.3)
    return "timeout", None


def main():
    with sync_playwright() as pw:
        browser = start_chrome(pw)
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 850},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        ctx.add_init_script(no_webdriver)
        ctx.add_init_script(cursor_dot)
        page = ctx.new_page()

        print("opening", URL)
        page.goto(URL, wait_until="domcontentloaded")

        for tries in range(1, MAX_TRIES + 1):
            if not click_check_price(page):
                print(f"  try {tries}: couldn't click the button")
                continue
            result, quote = wait_for_price(page)
            if result == "ok":
                print("\ngot it" if tries == 1 else f"\ngot it after {tries} tries")
                print("  price :", quote["shown"], quote["currency"])
                print("  mrp   :", quote["mrp"], quote["currency"])
                print("  stock :", quote["stock"])
                print("  seller:", quote.get("seller"))
                time.sleep(8)
                browser.close()
                return
            print(f"  try {tries}: {result}")
            time.sleep(random.uniform(0.6, 1.4))

        print("gave up after", MAX_TRIES, "tries")
        browser.close()


main()
