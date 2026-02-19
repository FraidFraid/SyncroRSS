import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

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


def article_sort_key(link: str) -> int:
    match = re.search(r"-a(\d+)\.html$", link)
    if match:
        return int(match.group(1))
    return 0


def get_remote_size(url: str) -> int:
    try:
        res = requests.head(url, allow_redirects=True, timeout=10)
        size = res.headers.get("Content-Length")
        if size and size.isdigit():
            return int(size)
    except Exception:
        pass
    return 1


def fetch_article_description(session: requests.Session, link: str, headers: dict) -> str:
    try:
        res = session.get(link, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(res.text, "html.parser")

    # Main product description block on Syncrophone article pages.
    main_desc = soup.select_one('.fa_description[itemprop="description"]')
    if main_desc:
        text = " ".join(main_desc.stripped_strings)
        if text:
            return text

    # Fallback to OG description if present.
    og_desc = soup.select_one('meta[property="og:description"]')
    if og_desc:
        content = (og_desc.get("content") or "").strip()
        if content:
            return content

    return ""


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
    fg.title("Syncrophone - News")
    fg.link(href=URL, rel="alternate")
    fg.description("Flux RSS genere via Python Script")
    fg.language("fr")

    items = soup.select(SELECTORS["item"])
    print(f"Articles detectes : {len(items)}")

    parsed_items = []
    session = requests.Session()
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
            article_description = fetch_article_description(session, link, headers)
            if article_description:
                description = article_description

            img_tag = item.select_one(SELECTORS["image"])
            img_url = None
            if img_tag:
                raw = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-lazy")
                if raw:
                    img_url = to_absolute(raw)

            parsed_items.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "img_url": img_url,
                    "sort_key": article_sort_key(link),
                }
            )
        except Exception:
            continue

    parsed_items.sort(key=lambda x: x["sort_key"], reverse=True)

    for entry in parsed_items:
        fe = fg.add_entry()
        fe.id(entry["link"])
        fe.title(entry["title"])
        fe.link(href=entry["link"])
        fe.description(entry["description"])
        if entry["img_url"]:
            img_size = get_remote_size(entry["img_url"])
            fe.enclosure(entry["img_url"], img_size, "image/jpeg")
            fe.content(
                f'<![CDATA[<p><img src="{entry["img_url"]}" alt="{entry["title"]}"/></p><p>{entry["description"]}</p>]]>',
                type="CDATA",
            )
        fe.pubDate(datetime.now().astimezone())

    fg.rss_file("rss.xml")
    print("Fichier rss.xml genere avec succes.")


if __name__ == "__main__":
    generate_feed()
