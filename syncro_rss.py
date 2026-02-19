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


def product_sort_key(item: BeautifulSoup, link: str) -> int:
    link_key = article_sort_key(link)
    if link_key > 0:
        return link_key

    bp = item.select_one(".bp_content[idProduit]")
    if bp:
        raw_id = bp.get("idProduit")
        if raw_id and str(raw_id).isdigit():
            # Keep this below explicit article IDs to avoid odd ordering.
            return int(raw_id) - 1_000_000
    return -1_000_000_000


def get_remote_size(url: str) -> int:
    try:
        res = requests.head(url, allow_redirects=True, timeout=10)
        size = res.headers.get("Content-Length")
        if size and size.isdigit():
            return int(size)
    except Exception:
        pass
    return 1


def extract_release_info_line(soup: BeautifulSoup) -> str:
    mapping = {
        "label": "",
        "format": "",
        "country": "",
        "released": "",
        "style": "",
    }

    for label_node in soup.select(".label_carac"):
        label = " ".join(label_node.stripped_strings).strip().lower().rstrip(":")
        value_node = label_node.find_next_sibling(class_="label_valeur")
        if not value_node:
            continue
        value = " ".join(value_node.stripped_strings).strip()
        if not value:
            continue
        if label in mapping and not mapping[label]:
            mapping[label] = value

    parts = [mapping[k] for k in ["label", "format", "country", "released", "style"] if mapping[k]]
    return " | ".join(parts)


def fetch_article_description(session: requests.Session, link: str, headers: dict) -> str:
    try:
        res = session.get(link, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(res.text, "html.parser")

    release_info_line = extract_release_info_line(soup)

    # Preferred block: long release description panel.
    long_desc = soup.select_one("#div_description_longue .hide_info_annexe")
    if long_desc:
        text = " ".join(long_desc.stripped_strings)
        if text:
            if release_info_line:
                return f"{release_info_line}\n\n{text}"
            return text

    # Fallback: build a meaningful summary from "Release Information".
    if release_info_line:
        return release_info_line

    # Fallback to OG description if present.
    og_desc = soup.select_one('meta[property="og:description"]')
    if og_desc:
        content = (og_desc.get("content") or "").strip()
        if content:
            if release_info_line:
                return f"{release_info_line}\n\n{content}"
            return content

    return "No release description available."


def split_meta_and_body(text: str) -> tuple[str, str]:
    parts = text.split("\n\n", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return text.strip(), ""


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
    seen_links = set()
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
            if link in seen_links:
                continue
            seen_links.add(link)

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
                    "sort_key": product_sort_key(item, link),
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
            meta_line, body_text = split_meta_and_body(entry["description"])
            body_html = f"<p>{body_text}</p>" if body_text else ""
            fe.content(
                f"<p><strong>{meta_line}</strong></p>{body_html}",
                type="html",
            )
        fe.pubDate(datetime.now().astimezone())

    fg.rss_file("rss.xml")
    print("Fichier rss.xml genere avec succes.")


if __name__ == "__main__":
    generate_feed()
