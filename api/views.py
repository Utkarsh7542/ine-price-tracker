import csv
import io
import json

import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import db

STORE = "https://demo.inelabteamdev.com"

# the store has no real search, so we pull the catalog once and keep it in
# memory, then filter names ourselves.
_catalog = []


def load_catalog():
    global _catalog
    if _catalog:
        return _catalog
    seen = {}
    for page in range(1, 30):
        try:
            data = requests.get(f"{STORE}/api/v2/listings",
                                params={"page": page, "limit": 60}, timeout=15).json()
        except Exception:
            break
        for it in data.get("results", []):
            seen[it["id"]] = {"id": it["id"], "name": it["name"],
                              "brand": it["brand"], "category": it["category"]}
        if len(seen) >= 950:
            break
    _catalog = list(seen.values())
    return _catalog


def home(request):
    return JsonResponse({"ok": True, "service": "ine price tracker api"})


def products(request):
    return JsonResponse(db.get_products(), safe=False)


def search(request):
    q = request.GET.get("q", "").strip().lower()
    if not q:
        return JsonResponse([], safe=False)
    matches = [it for it in load_catalog() if q in it["name"].lower()]
    return JsonResponse(matches[:25], safe=False)


def options(request):
    item_id = request.GET.get("item_id")
    try:
        data = requests.get(f"{STORE}/api/v2/items/{item_id}", timeout=15).json()
        return JsonResponse({"name": data.get("name"),
                             "options": [o["label"] for o in data.get("options", [])]})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)


@csrf_exempt
def track(request):
    body = json.loads(request.body or "{}")
    p = db.add_product(int(body["store_item_id"]), body["name"], body["option_label"])
    return JsonResponse(p)


@csrf_exempt
def untrack(request):
    body = json.loads(request.body or "{}")
    db.remove_product(int(body["id"]))
    return JsonResponse({"ok": True})


def history(request):
    product_id = int(request.GET.get("product_id"))
    return JsonResponse(db.get_history(product_id), safe=False)


def export_csv(request):
    rows = db.get_full_history()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["store_item_id", "product_name", "option",
                "timestamp_utc", "price", "stock", "outcome"])
    for r in rows:
        tp = r.get("tracked_products") or {}
        w.writerow([
            tp.get("store_item_id"), tp.get("name"), tp.get("option_label"),
            r["scraped_at"],
            "" if r["price"] is None else r["price"],
            "" if r["stock"] is None else r["stock"],
            r["outcome"],
        ])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=scrape_history.csv"
    return resp
