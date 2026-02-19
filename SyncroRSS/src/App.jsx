import React, { useState, useEffect } from 'react';
import { Terminal, Github, Rss, Copy, Check, Settings, Info, Search, Code, Image as ImageIcon, Type, Link as LinkIcon, RefreshCw } from 'lucide-react';

const App = () => {
  const [activeTab, setActiveTab] = useState('config');
  const [copied, setCopied] = useState(false);

  const [selectors, setSelectors] = useState({
    item: '.news-item, .post-item, article',
    title: 'h2, h3, .title, .post-title',
    link: 'a',
    description: '.description, .summary, p, .post-content',
    image: 'img'
  });

  const [pythonScript, setPythonScript] = useState('');
  const diagnosticChecks = [
    { path: 'syncro_rss.py', reason: 'Script Python de generation RSS a la racine.' },
    { path: '.github/workflows/main.yml', reason: 'Workflow GitHub Actions detecte automatiquement.' },
    { path: 'rss.xml', reason: 'Fichier genere/committe par l Action apres execution.' }
  ];

  useEffect(() => {
    const script = `import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

# --- CONFIGURATION PERSONNALISÉE ---
URL = "https://www.syncrophone.fr/news"
BASE = "https://www.syncrophone.fr"

# Vos sélecteurs CSS
SELECTORS = {
    'item': "${selectors.item}",
    'title': "${selectors.title}",
    'link': "${selectors.link}",
    'description': "${selectors.description}",
    'image': "${selectors.image}"
}

def generate_feed():
    print(f"Extraction des news depuis {URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')

    fg = FeedGenerator()
    fg.id(URL)
    fg.title('Syncrophone - Flux Personnalisé')
    fg.link(href=URL, rel='alternate')
    fg.description('Flux RSS généré via Python Script')
    fg.language('fr')

    items = soup.select(SELECTORS['item'])
    print(f"Articles détectés : {len(items)}")

    for item in items:
        try:
            title_tag = item.select_one(SELECTORS['title'])
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            link_tag = item.select_one(SELECTORS['link'])
            if not link_tag:
                continue
            link = link_tag['href']
            if not link.startswith('http'):
                link = BASE + (link if link.startswith('/') else '/' + link)

            desc_tag = item.select_one(SELECTORS['description'])
            description = desc_tag.get_text(strip=True) if desc_tag else "Pas de description."

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
            fe.description(description)
            if img_url:
                fe.enclosure(img_url, 0, 'image/jpeg')

            fe.pubDate(datetime.now().astimezone())

        except Exception:
            continue

    fg.rss_file('rss.xml')
    print("Fichier rss.xml généré avec succès.")

if __name__ == "__main__":
    generate_feed()`;

    setPythonScript(script);
  }, [selectors]);

  const githubWorkflow = `name: Update RSS Feed
on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests beautifulsoup4 feedgen
      - name: Generate RSS
        run: python syncro_rss.py
      - name: Commit and push rss.xml
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add rss.xml
          git diff --cached --quiet || git commit -m "chore: update rss feed"
          git push`;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSelectorChange = (key, value) => {
    setSelectors((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-900">
      <div className="max-w-6xl mx-auto">
        <header className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Rss className="text-orange-500 w-8 h-8" />
              RSS Customizer <span className="text-slate-400 font-light">| Syncrophone</span>
            </h1>
            <p className="text-slate-500 mt-1">Configurez vos sélecteurs CSS et générez votre script sur mesure.</p>
          </div>
          <div className="flex bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
            {[
              { id: 'config', icon: Settings, label: 'Configuration' },
              { id: 'script', icon: Code, label: 'Script Python' },
              { id: 'deploy', icon: Github, label: 'GitHub' },
              { id: 'diagnostic', icon: RefreshCw, label: 'Diagnostic' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-orange-500 text-white shadow-md' : 'text-slate-600 hover:bg-slate-50'}`}
              >
                <tab.icon size={16} /> {tab.label}
              </button>
            ))}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
                <Search size={20} className="text-orange-500" />
                Sélecteurs CSS
              </h2>

              <div className="space-y-5">
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-2">
                    <Terminal size={14} /> Conteneur de l'article
                  </label>
                  <input
                    type="text"
                    value={selectors.item}
                    onChange={(e) => handleSelectorChange('item', e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                    placeholder=".news-item"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-2">
                    <Type size={14} /> Titre
                  </label>
                  <input
                    type="text"
                    value={selectors.title}
                    onChange={(e) => handleSelectorChange('title', e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-2">
                    <LinkIcon size={14} /> Lien (URL)
                  </label>
                  <input
                    type="text"
                    value={selectors.link}
                    onChange={(e) => handleSelectorChange('link', e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-2">
                    <Code size={14} /> Description
                  </label>
                  <input
                    type="text"
                    value={selectors.description}
                    onChange={(e) => handleSelectorChange('description', e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-2">
                    <ImageIcon size={14} /> Image
                  </label>
                  <input
                    type="text"
                    value={selectors.image}
                    onChange={(e) => handleSelectorChange('image', e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="mt-8 p-4 bg-orange-50 rounded-xl border border-orange-100 text-sm text-orange-800 italic">
                <p>
                  <strong>Astuce :</strong> Faites un clic-droit sur un élément du site, puis "Inspecter" pour trouver le nom de sa classe CSS.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-8">
            <div className="bg-slate-900 rounded-2xl shadow-xl overflow-hidden border border-slate-800">
              {activeTab === 'config' || activeTab === 'script' ? (
                <>
                  <div className="bg-slate-800 px-6 py-3 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1.5 mr-4">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      </div>
                      <span className="text-slate-400 text-xs font-mono">syncro_rss.py (Généré dynamiquement)</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(pythonScript)}
                      className="flex items-center gap-2 text-xs bg-slate-700 hover:bg-slate-600 text-white py-1.5 px-4 rounded-lg transition-all active:scale-95"
                    >
                      {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                      {copied ? 'Copié !' : 'Copier le script'}
                    </button>
                  </div>
                  <div className="p-6 overflow-auto max-h-[600px] custom-scrollbar">
                    <pre className="text-sm font-mono text-slate-300 leading-relaxed">{pythonScript}</pre>
                  </div>
                </>
              ) : activeTab === 'deploy' ? (
                <div className="bg-white p-8 min-h-[500px]">
                  <h3 className="text-xl font-bold mb-4 text-slate-900 flex items-center gap-2">
                    <Github className="text-slate-900" /> Déploiement GitHub Actions
                  </h3>
                  <p className="text-slate-600 mb-6">Utilisez ce code pour automatiser la mise à jour de votre flux RSS toutes les heures.</p>

                  <div className="space-y-6">
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                      <p className="text-sm font-bold text-slate-700 mb-2">
                        1. Fichier : <code className="text-orange-600">.github/workflows/main.yml</code>
                      </p>
                      <div className="relative group">
                        <button
                          onClick={() => copyToClipboard(githubWorkflow)}
                          className="absolute right-2 top-2 p-2 bg-white rounded-md shadow-sm border border-slate-200 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Copy size={14} />
                        </button>
                        <pre className="text-[11px] font-mono text-slate-600 overflow-x-auto p-4 bg-white rounded-lg border border-slate-100">
                          {githubWorkflow}
                        </pre>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
                        <h4 className="font-bold text-blue-900 text-sm mb-1">Stockage</h4>
                        <p className="text-xs text-blue-700">
                          Le fichier <code className="text-[10px]">rss.xml</code> sera généré à la racine de votre dépôt.
                        </p>
                      </div>
                      <div className="p-4 bg-green-50 border border-green-100 rounded-xl">
                        <h4 className="font-bold text-green-900 text-sm mb-1">Activation</h4>
                        <p className="text-xs text-green-700">
                          Activez "GitHub Pages" dans les réglages du dépôt pour obtenir l'URL publique.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white p-8 min-h-[500px]">
                  <h3 className="text-xl font-bold mb-4 text-slate-900 flex items-center gap-2">
                    <RefreshCw className="text-slate-900" /> Mode Diagnostic
                  </h3>
                  <p className="text-slate-600 mb-6">Verifiez que les fichiers critiques sont bien a la racine du depot GitHub.</p>
                  <div className="space-y-4">
                    {diagnosticChecks.map((check) => (
                      <div key={check.path} className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                        <p className="text-sm font-bold text-slate-800">
                          <code className="text-orange-600">{check.path}</code>
                        </p>
                        <p className="text-xs text-slate-600 mt-1">{check.reason}</p>
                      </div>
                    ))}
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900">
                      Si la branche <code>gh-pages</code> n apparait pas, lancez d abord l Action <code>Update RSS Feed</code> depuis l onglet Actions, puis
                      verifiez que le workflow passe en vert.
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-start gap-3 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <Info className="text-blue-500 shrink-0 mt-0.5" size={18} />
              <div className="text-xs text-slate-500 leading-relaxed">
                <strong>Mode d'emploi :</strong> Modifiez les sélecteurs à gauche si vous remarquez que le script ne trouve pas tous les articles. Le script utilise la librairie{' '}
                <code className="bg-slate-100 px-1">BeautifulSoup</code> qui est extrêmement flexible pour cibler n'importe quelle partie du site Syncrophone.
              </div>
            </div>
          </div>
        </div>
      </div>

      <style
        dangerouslySetInnerHTML={{
          __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0f172a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
      `
        }}
      />
    </div>
  );
};

export default App;
