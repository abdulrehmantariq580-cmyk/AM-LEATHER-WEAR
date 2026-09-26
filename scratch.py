import urllib.request
import csv

url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vROGl1b8ZoEhh8yOk-LLvqFPKJKm7dqRiAmQfBbBqYCq9Aae5igtLzk8u-Oi60JSBkYtEo926M-trS2/pub?output=csv'
response = urllib.request.urlopen(url)
lines = [l.decode('utf-8').strip() for l in response.readlines()]
reader = csv.DictReader(lines)

for row in reader:
    title = row.get('Product Title ', row.get('Product Title', '')).strip()
    fee = row.get('  Shipping Fee (Rs.)  ', row.get('Shipping Fee (Rs.)', '')).strip()
    print(f"Title: {title} | Shipping Fee: '{fee}'")
