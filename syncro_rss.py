import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import os

# --- CONFIGURATION POUR SYNCROPHONE ---
URL = "https://www.syncrophone.fr/news"
BASE = "https://www.syncrophone.fr"

SELECTORS = {
    'item': "article.product-miniature, .product-miniature, .ajax_block_product, .item",
    'title': ".product-title, .product-name, h2, h3",
    'link': "a.thumbnail, a.product-thumbnail, .product-title a, a",
    'description': ".product-price-and-shipping, .product-description, .price",
    'image': "img"
}

def generate_feed():
    print(f"Extraction des news depuis {URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        fg = FeedGenerator()
        fg.id(URL)
        fg.title('Syncrophone - Flux RSS')
        fg.link(href=URL, rel='alternate')
        fg.description('Dernières news de Syncrophone.fr')
        fg.language('fr')
        
        items = soup.select(SELECTORS['item'])
        print(f"Trouvé : {len(items)} articles")
        
        # SÉCURITÉ : Si 0 article trouvé, on génère un faux article d'alerte pour prévenir l'utilisateur dans Feedly
        if len(items) == 0:
            fe = fg.add_entry()
            fe.id(URL + "#erreur")
            fe.title("⚠️ Aucun article détecté (Problème de sélecteurs)")
            fe.link(href=URL)
            fe.description("Le script Python s'est bien lancé, mais les sélecteurs CSS n'ont trouvé aucun produit sur la page. Mettez à jour les sélecteurs dans votre code.")
            fe.pubDate(datetime.now().astimezone())
            
        for item in items:
            try:
                # 1. Titre
                title_tag = item.select_one(SELECTORS['title'])
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                
                # 2. Lien
                link_tag = item.select_one(SELECTORS['link'])
                if not link_tag: continue
                link = link_tag['href']
                if not link.startswith('http'): link = BASE + (link if link.startswith('/') else '/' + link)
                
                # 3. Description
                desc_tag = item.select_one(SELECTORS['description'])
                desc_html = desc_tag.decode_contents() if desc_tag else ""
                desc_text = desc_tag.get_text(strip=True) if desc_tag else ""
                
                # 4. Image
                img_tag = item.select_one(SELECTORS['image'])
                img_url = None
                if img_tag:
                    img_url = img_tag.get('src') or img_tag.get('data-src')
                    if img_url and not img_url.startswith('http'):
                        img_url = BASE + (img_url if img_url.startswith('/') else '/' + img_url)
                
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.description(desc_text)
                
                full_content = f"<div>"
                if img_url:
                    fe.enclosure(img_url, 0, 'image/jpeg')
                    full_content += f"<img src='{img_url}' style='max-width:100%; margin-bottom:15px;' /><br/>"
                
                full_content += f"<div style='font-size:14px; line-height:1.6;'>{desc_html}</div></div>"
                
                fe.content(full_content, type='html')
                fe.pubDate(datetime.now().astimezone())
                
            except Exception as e:
                continue

        fg.rss_file('rss.xml')
        print("Fichier rss.xml généré avec succès.")
    except Exception as e:
        print(f"Erreur fatale : {e}")

if __name__ == "__main__":
    generate_feed()
