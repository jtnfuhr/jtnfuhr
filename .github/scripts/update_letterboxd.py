import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

url = "https://letterboxd.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)
ns = {"letterboxd": "https://letterboxd.com"}
items = root.findall("./channel/item")

cells = []
for item in items:
    title_el = item.find("letterboxd:filmTitle", ns)
    if title_el is None:
        continue

    title = title_el.text
    year_el = item.find("letterboxd:filmYear", ns)
    year = year_el.text if year_el is not None else ""
    link = item.find("link").text
    desc = item.find("description").text or ""

    # Extract and upgrade poster resolution
    img_match = re.search(r'<img[^>]+src="([^"]+)"', desc)
    poster = img_match.group(1) if img_match else ""
    poster = re.sub(r"-0-\d+-0-\d+-crop", "-0-300-0-450-crop", poster)

    # Format rating stars
    rating_el = item.find("letterboxd:memberRating", ns)
    stars_html = ""
    if rating_el is not None and rating_el.text:
        val = float(rating_el.text)
        full = int(val)
        half = 1 if (val % 1) >= 0.5 else 0
        stars_str = ("★" * full) + ("½" if half else "")
        stars_html = f"<br><code>{stars_str}</code>"

    # Rewatch badge
    rewatch_el = item.find("letterboxd:rewatch", ns)
    rewatch_badge = " 🔁" if (rewatch_el is not None and rewatch_el.text == "Yes") else ""

    # Watched date
    date_el = item.find("letterboxd:watchedDate", ns)
    date_str = ""
    if date_el is not None and date_el.text:
        dt = datetime.strptime(date_el.text, "%Y-%m-%d")
        formatted_date = dt.strftime("%b %d, %Y")
        date_str = f"<br><sub>Watched {formatted_date}{rewatch_badge}</sub>"

    cell = (
        f'    <td align="center" valign="top" width="210">\n'
        f'      <a href="{link}">\n'
        f'        <img src="{poster}" width="150" alt="{title}" />\n'
        f'      </a>\n'
        f'      <br>\n'
        f'      <a href="{link}"><b>{title}</b></a> <sub>({year})</sub>'
        f'{stars_html}'
        f'{date_str}\n'
        f'    </td>'
    )
    cells.append(cell)

    if len(cells) == 3:
        break

html_block = (
    '<div align="center">\n'
    '  <table>\n'
    '    <tr>\n' +
    '\n'.join(cells) + '\n'
    '    </tr>\n'
    '  </table>\n'
    '</div>'
)

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

pattern = r"(<!-- LETTERBOXD-LIST:START -->).*?(<!-- LETTERBOXD-LIST:END -->)"
if not re.search(pattern, readme, flags=re.DOTALL):
    raise ValueError("Could not find <!-- LETTERBOXD-LIST:START --> and <!-- LETTERBOXD-LIST:END --> in README.md")

replacement = f"\\1\n{html_block}\n\\2"
updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)

print("Successfully updated README.md with", len(cells), "movies.")
