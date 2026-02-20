import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import os

# --- CONFIGURATION POUR SYNCROPHONE ---
URL = "https://www.syncrophone.fr/news"
BASE = "https://www.syncrophone.fr"

def generate_feed():
    print(f"Extraction des news depuis {URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    
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
        
        # SÉLECTEUR SPÉCIFIQUE À SYNCROPHONE
        items = soup.select('div.product_box')
        print(f"Trouvé : {len(items)} articles")
        
        # SÉCURITÉ : Si 0 article trouvé, on génère un faux article d'alerte
        if len(items) == 0:
            fe = fg.add_entry()
            fe.id(URL + "#erreur")
            fe.title("⚠️ Aucun article détecté (Problème de sélecteurs)")
            fe.link(href=URL)
            fe.description("Le script Python s'est bien lancé, mais les sélecteurs CSS n'ont trouvé aucun produit sur la page. Mettez à jour les sélecteurs dans votre code.")
            fe.pubDate(datetime.now().astimezone())
            
        for item in items:
            try:
                # 1. ARTISTE + TITRE (dans h3.bp_designation)
                artiste_tag = item.select_one('span.artiste')
                titre_tag = item.select_one('span.titre')
                
                if not artiste_tag or not titre_tag:
                    continue
                
                artiste = artiste_tag.get_text(strip=True)
                titre = titre_tag.get_text(strip=True)
                title = f"{artiste} - {titre}"
                
                # 2. LIEN (dans h3 > a)
                link_tag = item.select_one('h3.bp_designation a')
                if not link_tag:
                    continue
                    
                link = link_tag['href']
                if not link.startswith('http'):
                    link = BASE + (link if link.startswith('/') else '/' + link)
                
                # 3. LABEL (bp_marque)
                label_tag = item.select_one('div.bp_marque a')
                label = label_tag.get_text(strip=True) if label_tag else ""
                
                # 4. PRIX
                prix_tag = item.select_one('div.bp_prix')
                prix = prix_tag.get_text(strip=True) if prix_tag else ""
                
                # 5. IMAGE (data-lazy prioritaire sur src)
                img_tag = item.select_one('img')
                img_url = None
                if img_tag:
                    img_url = img_tag.get('data-lazy') or img_tag.get('src')
                    if img_url and not img_url.startswith('http'):
                        img_url = BASE + (img_url if img_url.startswith('/') else '/' + img_url)
                
                # 6. PISTES MP3 (tracklist)
                pistes = []
                for piste in item.select('li.mp3_tracks a.piste-mp3'):
                    piste_nom = piste.get_text(strip=True)
                    if piste_nom:
                        pistes.append(piste_nom)
                
                # Construction de la description
                description_parts = []
                if label:
                    description_parts.append(f"Label: {label}")
                if prix:
                    description_parts.append(f"Prix: {prix}")
                
                description = " | ".join(description_parts)
                
                # Création de l'entry
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title)
                fe.link(href=link)
                fe.description(description)
                
                # Contenu enrichi pour Feedly
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

if __name__ == "__main__":
    generate_feed()
