import requests
import json
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

# --- CONFIGURATION POUR SYNCROPHONE ---
AJAX_URL = "https://www.syncrophone.fr/ajax/load_page.php"
BASE = "https://www.syncrophone.fr"

def generate_feed():
    print(f"Extraction des news via AJAX...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.syncrophone.fr/news'
    }
    
    # Payload exacte de la requête AJAX
    payload = {
        'pages[0][id]': '60050',
        'pages[0][language]': '1'
    }
    
    try:
        res = requests.post(AJAX_URL, data=payload, headers=headers, timeout=15)
        res.raise_for_status()
        
        # Parse le JSON retourné
        data = json.loads(res.text)
        
        # La clé est ".load-page[data-id=\"60050\"][data-language=\"1\"]"
        html_content = None
        for key, value in data.items():
            if 'load-page' in key:
                html_content = value
                break
        
        if not html_content:
            print("❌ Aucune clé 'load-page' trouvée dans le JSON")
            html_content = ""
        
        # Parse le HTML extrait
        soup = BeautifulSoup(html_content, 'html.parser')
        
        fg = FeedGenerator()
        fg.id(BASE + '/news')
        fg.title('Syncrophone - Flux RSS')
        fg.link(href=BASE + '/news', rel='alternate')
        fg.description('Dernières news de Syncrophone.fr')
        fg.language('fr')
        
        # SÉLECTEUR SPÉCIFIQUE À SYNCROPHONE
        items = soup.select('div.product_box')
        print(f"Trouvé : {len(items)} articles")
        
        # SÉCURITÉ : Si 0 article trouvé
        if len(items) == 0:
            fe = fg.add_entry()
            fe.id(BASE + '/news#erreur')
            fe.title("⚠️ Aucun article détecté")
            fe.link(href=BASE + '/news')
            fe.description(f"HTML extrait: {len(html_content)} caractères. Aucun div.product_box trouvé.")
            fe.pubDate(datetime.now().astimezone())
            
        for item in items:
            try:
                # 1. ARTISTE + TITRE
                artiste_tag = item.select_one('span.artiste')
                titre_tag = item.select_one('span.titre')
                
                if not artiste_tag or not titre_tag:
                    continue
                
                artiste = artiste_tag.get_text(strip=True)
                titre = titre_tag.get_text(strip=True)
                title = f"{artiste} - {titre}"
                
                # 2. LIEN
                link_tag = item.select_one('h3.bp_designation a')
                if not link_tag:
                    continue
                    
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = BASE + (link if link.startswith('/') else '/' + link)
                
                # 3. LABEL
                label_tag = item.select_one('div.bp_marque a')
                label = label_tag.get_text(strip=True) if label_tag else ""
                
                # 4. PRIX
                prix_tag = item.select_one('div.bp_prix')
                prix = prix_tag.get_text(strip=True) if prix_tag else ""
                
                # 5. IMAGE (data-lazy prioritaire)
                img_tag = item.select_one('img')
                img_url = None
                if img_tag:
                    img_url = img_tag.get('data-lazy') or img_tag.get('src')
                    if img_url and not img_url.startswith('http'):
                        img_url = BASE + (img_url if img_url.startswith('/') else '/' + img_url)
                
                # 6. PISTES MP3
                pistes = []
                for piste in item.select('li.mp3_tracks a.piste-mp3'):
                    piste_nom = piste.get_text(strip=True)
                    if piste_nom:
                        pistes.append(piste_nom)
                
                # Description courte
                description_parts = []
                if label:
                    description_parts.append(f"Label: {label}")
                if prix:
                    description_parts.append(f"Prix: {prix}")
                
                description = " | ".join(description_parts) if description_parts else title
                
                # Création de l'entry
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.description(description)
                
                # Contenu enrichi pour Feedly (avec content:encoded)
                full_content = "<div>"
                
                if img_url:
                    fe.enclosure(img_url, 0, 'image/jpeg')
                    full_content += f"<img src='{img_url}' style='max-width:100%; margin-bottom:15px;' /><br/>"
                
                if label:
                    full_content += f"<p><strong>Label:</strong> {label}</p>"
                
                if prix:
                    full_content += f"<p><strong>Prix:</strong> {prix}</p>"
                
                if pistes:
                    full_content += "<p><strong>Tracklist:</strong></p><ul>"
                    for piste in pistes:
                        full_content += f"<li>{piste}</li>"
                    full_content += "</ul>"
                
                full_content += "</div>"
                
                fe.content(full_content, type='html')
                fe.pubDate(datetime.now().astimezone())
                
                print(f"✓ Ajouté: {title}")
                
            except Exception as e:
                print(f"Erreur sur un article: {e}")
                continue
                
        fg.rss_file('rss.xml')
        print(f"✅ Fichier rss.xml généré avec succès ({len(items)} articles)")
        
    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_feed()
