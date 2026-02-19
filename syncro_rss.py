import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

URL = "https://www.syncrophone.fr/news/"
BASE = "https://www.syncrophone.fr"

SELECTORS = {
    "item": ".jq-products-list .product_box",
    "title": "h3.bp_designation a",
    "link": "h3.bp_designation a",
    "description": ".bp_marque a",
    "image": ".bp_image img",
}


def to_absolute(url: str) -> str:
    if url.startswith("http"):
        return url
    return BASE + (url if url.startswith("/") else "/" + url)


def generate_feed() -> None:
    print(f"Extraction des news depuis {URL}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/110.0.0.0 Safari/537.36"
        )
    }

    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")

    fg = FeedGenerator()
    fg.id(URL)
    fg.title("Syncrophone - Flux Personnalise")
    fg.link(href=URL, rel="alternate")
    fg.description("Flux RSS genere via Python Script")
    fg.language("fr")

    items = soup.select(SELECTORS["item"])
    print(f"Articles detectes : {len(items)}")

    for item in items:
        try:
            title_tag = item.select_one(SELECTORS["title"])
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            link_tag = item.select_one(SELECTORS["link"])
            if not link_tag or "href" not in link_tag.attrs:
                continue
            link = to_absolute(link_tag["href"])

            desc_tag = item.select_one(SELECTORS["description"])
            description = desc_tag.get_text(strip=True) if desc_tag else "Pas de description."

            img_tag = item.select_one(SELECTORS["image"])
            img_url = None
            if img_tag:
                raw = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-lazy")
                if raw:
                    img_url = to_absolute(raw)

            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.description(description)
            if img_url:
                fe.enclosure(img_url, 0, "image/jpeg")
            fe.pubDate(datetime.now().astimezone())
        except Exception:
            continue

    fg.rss_file("rss.xml")
    print("Fichier rss.xml genere avec succes.")


if __name__ == "__main__":
    generate_feed()
