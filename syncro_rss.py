import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import os

# --- CONFIGURATION POUR SYNCROPHONE ---
URL = "https://www.syncrophone.fr/news"
BASE = "https://www.syncrophone.fr"

SELECTORS = {
    'item': ".news-item, .post-item, article",
    'title': "h2, h3, .title, .post-title",
    'link': "a",
    'description': ".description, .summary, p, .post-content",
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
                
                # 3. Description (Améliorée pour Feedly)
                desc_tag = item.select_one(SELECTORS['description'])
                if desc_tag:
                    # Garde le formatage HTML (sauts de ligne, etc.)
                    desc_html = desc_tag.decode_contents() 
                    # Version texte simple pour le résumé
                    desc_text = desc_tag.get_text(strip=True) 
                else:
                    desc_html = ""
                    desc_text = ""
                
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
                
                # fe.description est utilisé comme résumé court dans Feedly
                fe.description(desc_text)
                
                # FORMATAGE FEEDLY: fe.content gère le corps complet de l'article
                full_content = f"<div>"
                if img_url:
                    fe.enclosure(img_url, 0, 'image/jpeg')
                    # On ajoute l'image dans le corps de l'article
                    full_content += f"<img src='{img_url}' style='max-width:100%; margin-bottom:15px;' /><br/>"
                
                full_content += f"<div style='font-size:14px; line-height:1.6;'>{desc_html}</div></div>"
                
                fe.content(full_content, type='html')
                fe.pubDate(datetime.now().astimezone())
                
            except Exception as e:
                print(f"Erreur sur un article : {e}")
                continue

        fg.rss_file('rss.xml')
        print("Fichier rss.xml généré avec succès.")
    except Exception as e:
        print(f"Erreur fatale : {e}")

if __name__ == "__main__":
    generate_feed()
