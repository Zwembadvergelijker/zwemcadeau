import xml.etree.ElementTree as ET
from collections import defaultdict
import urllib.request
import json
import datetime

url = "https://zwemcadeau.myspreadshop.net/100570287/products.rss?pushState=false&targetPlatform=facebook"
resp = urllib.request.urlopen(url, timeout=15)
xml_data = resp.read().decode('utf-8')

root = ET.fromstring(xml_data)
ns = {'g': 'http://base.google.com/ns/1.0'}

products = defaultdict(list)
total_items = 0

for item in root.findall('.//item'):
    total_items += 1
    item_id = item.find('g:id', ns)
    group_id = item.find('g:item_group_id', ns)
    title = item.find('g:title', ns)
    link = item.find('g:link', ns)
    image = item.find('g:image_link', ns)
    price = item.find('g:price', ns)
    
    gid = group_id.text if group_id is not None else 'unknown'
    products[gid].append({
        'id': item_id.text if item_id is not None else '',
        'title': title.text if title is not None else '',
        'link': link.text if link is not None else '',
        'image': image.text if image is not None else '',
        'price': price.text if price is not None else '',
    })

# Unieke producten
unique_products = []
for gid, variants in products.items():
    v = variants[0]
    title_parts = v['title'].rsplit(' - ', 1)
    base_title = title_parts[0] if len(title_parts) > 1 else v['title']
    unique_products.append({
        'group_id': gid,
        'title': base_title,
        'link': v['link'],
        'image': v['image'],
        'price': v['price'],
        'variant_count': len(variants),
    })

print(f"Totaal items: {total_items}")
print(f"Unieke producten: {len(unique_products)}")

# Genereer sitemap
today = datetime.date.today().isoformat()
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += '  <url>\n'
sitemap += '    <loc>https://zwemcadeau.nl/</loc>\n'
sitemap += f'    <lastmod>{today}</lastmod>\n'
sitemap += '    <changefreq>weekly</changefreq>\n'
sitemap += '    <priority>1.0</priority>\n'
sitemap += '  </url>\n'
for p in unique_products:
    sitemap += '  <url>\n'
    sitemap += f'    <loc>{p["link"]}</loc>\n'
    sitemap += f'    <lastmod>{today}</lastmod>\n'
    sitemap += '    <changefreq>monthly</changefreq>\n'
    sitemap += '    <priority>0.8</priority>\n'
    sitemap += '  </url>\n'
sitemap += '</urlset>\n'

with open('/opt/data/zwemcadeau/sitemap.xml', 'w') as f:
    f.write(sitemap)

# Genereer JSON-LD voor de homepage
jsonld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": "https://zwemcadeau.nl/#website",
            "url": "https://zwemcadeau.nl",
            "name": "Zwemcadeau",
            "inLanguage": "nl-NL"
        },
        {
            "@type": "Organization",
            "@id": "https://zwemcadeau.nl/#organization",
            "name": "Zwemcadeau",
            "url": "https://zwemcadeau.nl",
            "description": "Zwemcadeaus en zwemaccessoires — T-shirts, mokken, badhanddoeken en meer met zwemthema",
        }
    ]
}

# Voeg eerste 20 producten toe als ItemList
jsonld["@graph"].append({
    "@type": "ItemList",
    "itemListElement": [],
    "numberOfItems": len(unique_products),
    "name": "Zwemcadeau producten"
})

for i, p in enumerate(unique_products[:20]):
    jsonld["@graph"][2]["itemListElement"].append({
        "@type": "ListItem",
        "position": i + 1,
        "item": {
            "@type": "Product",
            "name": p['title'],
            "url": p['link'],
            "image": p['image'],
            "offers": {
                "@type": "Offer",
                "price": p['price'].replace(' EUR', ''),
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        }
    })

with open('/opt/data/zwemcadeau/jsonld-products.json', 'w') as f:
    json.dump(jsonld, f, indent=2, ensure_ascii=False)

print(f"sitemap.xml: {len(unique_products) + 1} URLs")
print(f"jsonld-products.json: gegenereerd")

# Toon eerste 3 producten
for p in unique_products[:3]:
    print(f"  {p['title'][:70]}")
    print(f"    {p['price']}")
