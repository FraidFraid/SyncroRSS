import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import time

# --- CONFIGURATION POUR SYNCROPHONE ---
URL = "https://www.syncrophone.fr/news/"
BASE = "https://www.syncrophone.fr"

def get_product_details(product_url):
    """Récupère la description et le style depuis la page produit"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        res = requests.get(product_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Description
        description = ""
        desc_div = soup.select_one('div.hide_info_annexe')
        if desc_div:
            desc_p = desc_div.select_one('p')
            if desc_p:
                description = desc_p.get_text(strip=True)
        
        # Style
        style = ""
        style_row = None
        for li in soup.select('ul#tableau_carac li.row'):
            label = li.select_one('span.label_carac')
            if label and 'Style' in label.get_text():
                style_row = li
                break
        
        if style_row:
            style_val = style_row.select_one('span.label_valeur')
            if style_val:
                style = style_val.get_text(strip=True)
        
        return description, style
        
    except Exception as e:
        print(f"  ⚠️ Erreur récupération détails: {e}")
        return "", ""

def generate_feed():
    print(f"Extraction des news depuis {URL}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=20, allow_redirects=True)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        fg = FeedGenerator()
        fg.id(URL)
        fg.title('Syncrophone - Flux RSS')
        fg.link(href=URL, rel='alternate')
        fg.description('Dernières news de Syncrophone.fr')
        fg.language('fr')
        
        items = soup.select('div.product_box')
        print(f"Trouvé : {len(items)} articles")
        
        if len(items) == 0:
            fe = fg.add_entry()
            fe.id(URL + '#erreur')
            fe.title("⚠️ Aucun article détecté")
            fe.link(href=URL)
            fe.description(f"Le script a récupéré {len(res.text)} caractères mais aucun div.product_box trouvé.")
            fe.pubDate(datetime.now().astimezone())
            
        for idx, item in enumerate(items, 1):
            try:
                # 1. TITRE
                artiste_tag = item.select_one('span.artiste')
                titre_tag = item.select_one('span.titre')
                
                if artiste_tag and titre_tag:
                    artiste = artiste_tag.get_text(strip=True)
                    titre = titre_tag.get_text(strip=True)
                    title = f"{artiste} - {titre}"
                else:
                    link_tag = item.select_one('h3.bp_designation a')
                    if not link_tag:
                        continue
                    title = link_tag.get_text(strip=True)
                
                # 2. LIEN
                link_tag = item.select_one('h3.bp_designation a')
                if not link_tag:
                    continue
                    
                link = link_tag.get('href', '')
                if not link.startswith('http'):
                    link = BASE + (link if link.startswith('/') else '/' + link)
                
                print(f"[{idx}/{len(items)}] Traitement: {title}")
                
                # 3. LABEL
                label_tag = item.select_one('div.bp_marque a')
                label = label_tag.get_text(strip=True) if label_tag else ""
                
                # 4. PRIX
                prix_tag = item.select_one('div.bp_prix')
                prix = prix_tag.get_text(strip=True) if prix_tag else ""
                
                # 5. IMAGE
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
                
                # 7. RÉCUPÉRATION DESCRIPTION + STYLE depuis la page produit
                print(f"  → Récupération détails depuis {link}")
                description, style = get_product_details(link)
                time.sleep(0.5)  # Pause de 500ms entre chaque requête pour ne pas surcharger le serveur
                
                # Description courte pour le flux
                description_parts = []
                if label:
                    description_parts.append(f"Label: {label}")
                if prix:
                    description_parts.append(f"Prix: {prix}")
                if style:
                    description_parts.append(f"Style: {style}")
                
                short_description = " | ".join(description_parts) if description_parts else title
                
                # Création de l'entry
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.description(short_description)
                
                # Contenu enrichi pour Feedly
                full_content = "<div>"
                
                if img_url:
                    fe.enclosure(img_url, 0, 'image/jpeg')
                    full_content += f"<img src='{img_url}' style='max-width:100%; margin-bottom:15px;' /><br/>"
                
                if label:
                    full_content += f"<p><strong>Label:</strong> {label}</p>"
                
                if prix:
                    full_content += f"<p><strong>Prix:</strong> {prix}</p>"
                
                if style:
                    full_content += f"<p><strong>Style:</strong> {style}</p>"
                
                # DESCRIPTION COMPLÈTE
                if description:
                    full_content += f"<div style='margin-top:15px; margin-bottom:15px; padding:10px; background:#f5f5f5; border-left:3px solid #333;'>{description}</div>"
                
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
                print(f"❌ Erreur sur un article: {e}")
                continue
                
        fg.rss_file('rss.xml')
        print(f"\n✅ Fichier rss.xml généré avec succès ({len(items)} articles)")
        
    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_feed()
