"""
Genereer een Google Product Feed met statische product-URLs (geen hash-URLs).
Deze feed dient als aanvullende feed in Merchant Center.
Bevat ALLE verplichte velden voor Google Merchant Center goedkeuring.

Gebruik: python3 generate_feed.py
"""
import xml.etree.ElementTree as ET
import subprocess
import tempfile
import re
import os
import datetime

FEED_URL = "https://zwemcadeau.myspreadshop.net/100570287/products.rss?pushState=false&targetPlatform=facebook"
BASE_URL = "https://zwemcadeau.nl"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products-feed.xml")
ns = {"g": "http://base.google.com/ns/1.0"}

# 1. Download de Spreadshop RSS feed (71MB — curl is sneller dan urllib)
print("Downloading feed...")
with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
    tmp_path = tmp.name
subprocess.run(
    ["curl", "-s", "--max-time", "120", "-o", tmp_path, FEED_URL],
    check=True
)
print(f"Downloaded to {tmp_path}")

# 2. Parse en bouw design → slug mapping
tree = ET.parse(tmp_path)
root = tree.getroot()

design_slugs = {}
item_count = 0
for item in root.findall(".//item"):
    title_el = item.find("g:title", ns)
    if title_el is None:
        continue
    item_count += 1
    title = title_el.text
    design = title.rsplit(" - ", 1)[0].strip()
    slug = re.sub(r"[^a-z0-9]+", "-", design.lower()).strip("-")
    design_slugs[design] = slug

print(f"Total items in source: {item_count}")
print(f"Unique designs: {len(design_slugs)}")

# 3. Helper functies
def get_text(el, tag, default=""):
    found = el.find(f"g:{tag}", ns)
    if found is not None and found.text:
        return found.text
    return default

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# 4. Verzamel alle varianten per design (net als generate_products.py)
from collections import defaultdict
design_variants = defaultdict(list)

for item in root.findall(".//item"):
    title_el = item.find("g:title", ns)
    if title_el is None:
        continue
    title = title_el.text
    design = title.rsplit(" - ", 1)[0].strip()

    iid = esc(get_text(item, "id"))
    igid = esc(get_text(item, "item_group_id"))
    desc = esc(get_text(item, "description"))
    img = esc(get_text(item, "image_link"))
    price_str = get_text(item, "price")
    price_num = float(price_str.replace(" EUR", "").replace(",", "."))
    avail = get_text(item, "availability").replace(" ", "_")
    cond = get_text(item, "condition", "new")
    brand = esc(get_text(item, "brand", "SPREAD"))
    gpc = get_text(item, "google_product_category")
    idex = get_text(item, "identifier_exists", "false")

    design_variants[design].append({
        "id": iid,
        "item_group_id": igid,
        "title": title,
        "description": desc,
        "image": img,
        "price_str": price_str,
        "price_num": price_num,
        "availability": avail,
        "condition": cond,
        "brand": brand,
        "google_product_category": gpc,
        "identifier_exists": idex,
    })

# 5. Genereer feed — goedkoopste variant per design (match met productpagina)
today = datetime.date.today().isoformat()
lines = []
lines.append('<?xml version="1.0" encoding="UTF-8"?>')
lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
lines.append("<channel>")
lines.append("<title>Zwemcadeau</title>")
lines.append("<link>https://zwemcadeau.nl</link>")
lines.append("<description>Zwemcadeau producten</description>")

feed_items = 0

for design, variants in sorted(design_variants.items()):
    best = min(variants, key=lambda v: v["price_num"])
    slug = design_slugs.get(design, "product")
    feed_items += 1

    lines.append("<item>")
    lines.append(f"<g:id>{best['id']}</g:id>")
    if best['item_group_id']:
        lines.append(f"<g:item_group_id>{best['item_group_id']}</g:item_group_id>")
    lines.append(f"<g:title>{esc(best['title'])}</g:title>")
    lines.append(f"<g:description>{best['description']}</g:description>")
    lines.append(f"<g:link>{BASE_URL}/products/{slug}.html</g:link>")
    lines.append(f"<g:image_link>{best['image']}</g:image_link>")
    lines.append(f"<g:price>{best['price_str']}</g:price>")
    lines.append(f"<g:availability>{best['availability']}</g:availability>")
    lines.append(f"<g:condition>{best['condition']}</g:condition>")
    if best['brand']:
        lines.append(f"<g:brand>{best['brand']}</g:brand>")
    if best['google_product_category']:
        lines.append(f"<g:google_product_category>{best['google_product_category']}</g:google_product_category>")
    lines.append(f"<g:identifier_exists>{best['identifier_exists']}</g:identifier_exists>")
    lines.append("</item>")

lines.append("</channel>")
lines.append("</rss>")

with open(OUTPUT, "w") as f:
    f.write("\n".join(lines))

# Opruimen
os.unlink(tmp_path)

print(f"Feed saved: {OUTPUT}")
print(f"Items: {feed_items}")
print(f"Size: {os.path.getsize(OUTPUT)} bytes")
print("Velden: id, item_group_id, title, description, link, image_link, price, availability(in_stock), condition(new), brand, google_product_category, identifier_exists(false)")
