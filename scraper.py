# scraper for the INE store.
#
# the price is hidden behind two tricks: a "hover the box first" human check,
# and a puzzle that sometimes fails on purpose. so we drive a real browser,
# get past both, and read the real price straight out of the page (the price
# text on screen has fake numbers + invisible characters, so we can't trust it).
#
# scrape_price() returns a plain dict, so the db / api can just use it.

import random
import re
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

STORE = "https://demo.inelabteamdev.com"

# hides the "i'm a bot" flag before the page's code runs
no_webdriver = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"

# red dot that trails the mouse - only used when we want to watch (the demo video)
cursor_dot = """
const d=document.createElement('div');
d.style.cssText='position:fixed;z-index:99999;width:16px;height:16px;border-radius:50%;background:rgba(255,40,40,.55);border:2px solid #ff2828;pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px';
addEventListener('DOMContentLoaded',()=>document.body.appendChild(d));
addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px';});
addEventListener('mousedown',()=>d.style.background='rgba(40,140,255,.8)');
addEventListener('mouseup',()=>d.style.background='rgba(255,40,40,.55)');
"""

# pulls the real price object out of react's memory
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


def start_chrome(pw, headless):
    flags = ["--disable-blink-features=AutomationControlled"]
    slow = 0 if headless else 40
    try:
        return pw.chromium.launch(headless=headless, channel="chrome", args=flags, slow_mo=slow)
    except Exception:
        return pw.chromium.launch(headless=headless, args=flags, slow_mo=slow)


def popup_showing(page):
    return page.locator(".consent-scrim").count() > 0


def kill_popup(page):
    if not popup_showing(page):
        return
    try:
        page.locator('.consent-scrim button[aria-label="Allow cookies"]').click(timeout=2000)
        page.locator(".consent-scrim").first.wait_for(state="detached", timeout=3000)
    except Exception:
        pass


def wait_no_popup(page):
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


def pick_option(page, option):
    # options are chips; click the one whose text matches what we want to track
    wait_no_popup(page)
    try:
        page.locator("button.opt-chip", has_text=option).first.click(timeout=3000)
        time.sleep(0.5)
    except Exception:
        print("  note: couldn't pick option", repr(option))


def wake_button(page, btn):
    # button is dead until the mouse moves over the price box ~8 times and
    # lingers ~600ms, so wiggle the mouse around inside it
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
    # clear popup, wake button, click. a failed click is usually a late popup,
    # so clear it and try again (this does NOT use up a real retry)
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


def scrape_price(item_id, option=None, headless=True, max_tries=12, watch=False):
    """go to a product, pick the option, get past the guard, read the price.
    returns a dict; on total failure price/stock are None and outcome='failed'."""
    row = {
        "item_id": item_id,
        "option": option,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "price": None, "mrp": None, "stock": None, "currency": None,
        "seller": None, "outcome": "failed", "tries": 0,
    }
    with sync_playwright() as pw:
        browser = start_chrome(pw, headless)
        ctx = browser.new_context(viewport={"width": 1366, "height": 850},
                                  locale="en-IN", timezone_id="Asia/Kolkata")
        ctx.add_init_script(no_webdriver)
        if watch:
            ctx.add_init_script(cursor_dot)
        page = ctx.new_page()
        try:
            page.goto(f"{STORE}/item/{item_id}", wait_until="domcontentloaded")
            if option:
                pick_option(page, option)
            for t in range(1, max_tries + 1):
                row["tries"] = t
                if not click_check_price(page):
                    continue
                result, quote = wait_for_price(page)
                if result == "ok":
                    row.update(price=quote["shown"], mrp=quote["mrp"], stock=quote["stock"],
                               currency=quote["currency"], seller=quote.get("seller"),
                               outcome=("success" if t == 1 else "retried"))
                    return row
                time.sleep(random.uniform(0.6, 1.4))
            return row
        finally:
            browser.close()


# quick manual test: scrape a few products so I can see it works in general.
# run: python scraper.py
if __name__ == "__main__":
    jobs = [
        (2290, "Neutral white"),   # Redwick LED Strip Core, specific option
        (2665, None),              # Orbisk Dumbbell Set Duo, default option
        (2188, None),              # Veloria Resistance Bands Edge, default option
    ]
    for item_id, option in jobs:
        r = scrape_price(item_id, option=option, headless=False, watch=True)
        print(f"[{r['outcome']:8}] item {r['item_id']} ({r['option'] or 'default'}): "
              f"price={r['price']} stock={r['stock']} {r['currency'] or ''}  (tries={r['tries']})")
