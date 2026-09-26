# scrape every tracked product once and save the result. this is what the
# scheduler will run every 2 hours.
from db import get_products, save_scrape
from scraper import scrape_price


def main():
    products = get_products()
    print(f"scraping {len(products)} tracked products...")
    for p in products:
        r = scrape_price(p["store_item_id"], option=p["option_label"], headless=True)
        save_scrape(p["id"], r)
        print(f"  {p['name']} ({p['option_label']}): {r['outcome']} "
              f"price={r['price']} stock={r['stock']}")


if __name__ == "__main__":
    main()
