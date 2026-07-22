"""
Genereer een Google Product Feed met statische product-URLs (geen hash-URLs).
Deze feed dient als aanvullende feed in Merchant Center.
"""
import xml.etree.ElementTree as ET
import urllib.request
from collections import defaultdict
import re
import datetime

FEED_URL = "https://zwemcadeau.myspreadshop.net/100570287/products.rss?pushState=false&targetPlatform=facebook"
BASE_URL = "https://zwemcadeau.nl"

resp = urllib.request.urlopen(FEED_URL, timeout=15)
xml_data = resp.read().decode('utf-8')
root = ET.fromstring(xml_data)
ns = {'g': 'http://base.google.com/ns/1.0'}

# Bouw design → slug mapping
design_slugs = {}
for item in root.findall('.//item'):
    title = item.find('g:title', ns).text
    design = title.rsplit(' - ', 1)[0].strip()
    slug = re.sub(r'[^a-z0-9]+', '-', design.lower()).strip('-')
    design_slugs[design] = slug

# Genereer eigen feed XML
today = datetime.date.today().isoformat()
feed = '<?xml version="1.0" encoding="UTF-8"?>\n'
feed += '<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">\n'
feed += '<channel>\n'
feed += '  <title>Zwemcadeau</title>\n'
feed += '  <link>https://zwemcadeau.nl</link>\n'
feed += '  <description>Zwemcadeau producten</description>\n'

for item in root.findall('.//item'):
    title = item.find('g:title', ns).text
    description = item.find('g:description', ns)
    desc = description.text if description is not None else ''
    image = item.find('g:image_link', ns).text
    price = item.find('g:price', ns).text
    item_id = item.find('g:id', ns).text
    availability = item.find('g:availability', ns).text
    
    design = title.rsplit(' - ', 1)[0].strip()
    slug = design_slugs.get(design, 'product')
    
    # Vervang hash-URL door statische URL
    static_url = f"{BASE_URL}/products/{slug}.html"
    
    feed += '  <item>\n'
    feed += f'    <g:id>{item_id}</g:id>\n'
    feed += f'    <g:title>{title}</g:title>\n'
    feed += f'    <g:description>{desc}</g:description>\n'
    feed += f'    <g:link>{static_url}</g:link>\n'
    feed += f'    <g:image_link>{image}</g:image_link>\n'
    feed += f'    <g:price>{price}</g:price>\n'
    feed += f'    <g:availability>{availability}</g:availability>\n'
    feed += '  </item>\n'

feed += '</channel>\n'
feed += '</rss>'

filepath = '/opt/data/zwemcadeau/products-feed.xml'
with open(filepath, 'w') as f:
    f.write(feed)

# Tel items
item_count = len(root.findall('.//item'))
print(f"Feed gegenereerd: {filepath}")
print(f"Producten: {item_count}")
print(f"Unieke designs: {len(design_slugs)}")
