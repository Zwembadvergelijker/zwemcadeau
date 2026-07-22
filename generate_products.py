"""
Genereer statische productpagina's uit de Spreadshop RSS feed.
Elk uniek design krijgt een eigen HTML pagina met prijs, foto, en JSON-LD.
"""
import xml.etree.ElementTree as ET
import urllib.request
from collections import defaultdict
import datetime
import re
import os

FEED_URL = "https://zwemcadeau.myspreadshop.net/100570287/products.rss?pushState=false&targetPlatform=facebook"
OUTPUT_DIR = "/opt/data/zwemcadeau/products"
BASE_URL = "https://zwemcadeau.nl"

# Download feed
resp = urllib.request.urlopen(FEED_URL, timeout=15)
xml_data = resp.read().decode('utf-8')
root = ET.fromstring(xml_data)
ns = {'g': 'http://base.google.com/ns/1.0'}

# Groepeer op unieke designnaam
designs = defaultdict(list)

for item in root.findall('.//item'):
    title = item.find('g:title', ns).text
    link = item.find('g:link', ns).text
    image = item.find('g:image_link', ns).text
    price = item.find('g:price', ns).text
    desc = item.find('g:description', ns)
    description = desc.text if desc is not None else ''
    
    # Haal design naam (vóór het laatste ' - ')
    parts = title.rsplit(' - ', 1)
    design_name = parts[0].strip()
    variant = parts[1].strip() if len(parts) > 1 else ''
    
    designs[design_name].append({
        'title': title,
        'link': link,
        'image': image,
        'price': price,
        'description': description,
        'variant': variant,
    })

# Maak output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Genereer pagina per design
product_urls = []
today = datetime.date.today().isoformat()

for design_name, variants in sorted(designs.items()):
    # Gebruik variant met laagste prijs als representatief
    best = min(variants, key=lambda v: float(v['price'].replace(' EUR', '').replace(',', '.')))
    
    # Maak slug
    slug = re.sub(r'[^a-z0-9]+', '-', design_name.lower()).strip('-')
    if not slug:
        slug = 'product'
    
    # Gebruik eerste variant als standaard afbeelding en prijs
    price_num = best['price'].replace(' EUR', '')
    price_eur = f"€{price_num}"
    
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{design_name} — Zwemcadeau</title>
    <meta name="description" content="{design_name} — {best['description']}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{BASE_URL}/products/{slug}.html">
    
    <!-- Open Graph -->
    <meta property="og:type" content="product">
    <meta property="og:title" content="{design_name} — Zwemcadeau">
    <meta property="og:description" content="{best['description']}">
    <meta property="og:image" content="{best['image']}">
    <meta property="og:url" content="{BASE_URL}/products/{slug}.html">
    <meta property="product:price:amount" content="{price_num}">
    <meta property="product:price:currency" content="EUR">
    
    <!-- JSON-LD Product schema -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "{design_name}",
        "description": "{best['description']}",
        "image": "{best['image']}",
        "url": "{BASE_URL}/products/{slug}.html",
        "category": "Apparel & Accessories",
        "offers": {{
            "@type": "Offer",
            "price": "{price_num}",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock",
            "url": "{best['link']}"
        }}
    }}
    </script>
    
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f8fb;
            color: #1a1a2e;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 32px 16px;
            text-align: center;
        }}
        .back {{ 
            display: inline-block;
            margin-bottom: 24px;
            color: #29abe2;
            text-decoration: none;
            font-size: 0.95rem;
        }}
        .back:hover {{ text-decoration: underline; }}
        .product-image {{
            max-width: 400px;
            width: 100%;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 24px;
        }}
        h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 8px;
        }}
        .price {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #29abe2;
            margin-bottom: 20px;
        }}
        .buy-btn {{
            display: inline-block;
            background: #29abe2;
            color: #fff;
            padding: 14px 36px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 600;
            transition: background 0.2s;
        }}
        .buy-btn:hover {{ background: #1e8ec4; }}
        .variants {{
            margin-top: 32px;
            font-size: 0.9rem;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">← Terug naar Zwemcadeau</a>
        <img src="{best['image']}" alt="{design_name}" class="product-image" />
        <h1>{design_name}</h1>
        <p class="price">Vanaf {price_eur}</p>
        <a href="{best['link']}" class="buy-btn">Bekijk en bestel</a>
        <p class="variants">Beschikbaar in {len(variants)} varianten (maten/kleuren)</p>
    </div>
</body>
</html>"""
    
    filepath = os.path.join(OUTPUT_DIR, f"{slug}.html")
    with open(filepath, 'w') as f:
        f.write(html)
    
    product_urls.append(f"{BASE_URL}/products/{slug}.html")

# Genereer sitemap
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += '  <url>\n'
sitemap += '    <loc>https://zwemcadeau.nl/</loc>\n'
sitemap += f'    <lastmod>{today}</lastmod>\n'
sitemap += '    <changefreq>weekly</changefreq>\n'
sitemap += '    <priority>1.0</priority>\n'
sitemap += '  </url>\n'
for url in product_urls:
    sitemap += '  <url>\n'
    sitemap += f'    <loc>{url}</loc>\n'
    sitemap += f'    <lastmod>{today}</lastmod>\n'
    sitemap += '    <changefreq>monthly</changefreq>\n'
    sitemap += '    <priority>0.8</priority>\n'
    sitemap += '  </url>\n'
sitemap += '</urlset>\n'

with open('/opt/data/zwemcadeau/sitemap.xml', 'w') as f:
    f.write(sitemap)

print(f"Designs: {len(designs)}")
print(f"Productpagina's: {len(product_urls)}")
print(f"Sitemap URLs: {len(product_urls) + 1}")
print(f"Done — /opt/data/zwemcadeau/products/")
