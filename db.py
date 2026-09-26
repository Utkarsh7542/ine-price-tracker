# small wrapper around supabase so the rest of the code doesn't have to know
# how the db works. reads the url + key from a .env file (never committed).

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def add_product(store_item_id, name, option_label):
    # upsert -> tracking the same product+option twice won't make duplicates
    res = sb.table("tracked_products").upsert(
        {"store_item_id": store_item_id, "name": name, "option_label": option_label},
        on_conflict="store_item_id,option_label",
    ).execute()
    return res.data[0]


def get_products():
    return sb.table("tracked_products").select("*").order("id").execute().data


def save_scrape(product_id, r):
    # one row per scrape. price/stock stay empty (None) when it failed.
    sb.table("scrape_log").insert({
        "product_id": product_id,
        "outcome": r["outcome"],
        "price": r["price"],
        "mrp": r["mrp"],
        "stock": r["stock"],
        "currency": r["currency"],
        "tries": r["tries"],
    }).execute()
