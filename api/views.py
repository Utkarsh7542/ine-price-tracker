import csv
import io
import json
import os

import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import db

STORE = "https://demo.inelabteamdev.com"
GH_TOKEN = os.environ.get("GITHUB_TOKEN")
GH_REPO = os.environ.get("GITHUB_REPO", "Utkarsh7542/ine-price-tracker")


def home(request):
    return JsonResponse({"ok": True, "service": "ine price tracker api"})


def products(request):
    return JsonResponse(db.get_products(), safe=False)


def search(request):
    # catalog is cached in supabase (see build_catalog.py), so this is a quick
    # name lookup instead of hitting the store live on every search.
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    return JsonResponse(db.search_catalog(q), safe=False)


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


@csrf_exempt
def scrape_now(request):
    # kick off a github actions run so newly tracked products get data now
    # instead of waiting for the next 2-hourly schedule
    if not GH_TOKEN:
        return JsonResponse({"error": "no github token set"}, status=500)
    r = requests.post(
        f"https://api.github.com/repos/{GH_REPO}/actions/workflows/scrape.yml/dispatches",
        headers={"Authorization": f"Bearer {GH_TOKEN}",
                 "Accept": "application/vnd.github+json"},
        json={"ref": "main"}, timeout=15,
    )
    if r.status_code == 204:
        return JsonResponse({"ok": True})
    return JsonResponse({"error": r.text}, status=502)


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
