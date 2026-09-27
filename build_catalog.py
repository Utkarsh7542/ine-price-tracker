# grab the whole store catalog once and save it to supabase so search is fast.
# run this once.
import time
import requests
from db import sb

STORE = "https://demo.inelabteamdev.com"

seen = {}
page = 1
start = time.time()
while len(seen) < 960 and page <= 200 and time.time() - start < 90:
    try:
        data = requests.get(f"{STORE}/api/v2/listings",
                            params={"page": page, "limit": 60}, timeout=15).json()
    except Exception:
        break
    for it in data.get("results", []):
        seen[it["id"]] = {"id": it["id"], "name": it["name"],
                          "brand": it["brand"], "category": it["category"]}
    page += 1
    if page % 20 == 0:
        print(f"  {len(seen)} products so far...")

rows = list(seen.values())
print(f"got {len(rows)} products, saving to supabase...")
for i in range(0, len(rows), 200):
    sb.table("catalog").upsert(rows[i:i + 200], on_conflict="id").execute()
print("done")
