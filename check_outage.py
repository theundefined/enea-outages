#!/usr/bin/env python3

import urllib.request
from bs4 import BeautifulSoup

def check_outage():
    """
    Checks for a power outage on a specific street from the Enea Operator website.
    """
    url = "https://wylaczenia-eneaoperator.pl/index.php?page=awarie&oddzial=Pozna%C5%84"
    street_name = "Firlika"

    try:
        with urllib.request.urlopen(url) as response:
            html = response.read()
    except urllib.error.URLError as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(html, 'html.parser')

    # Find all div elements with the class 'unpl block info'
    outage_blocks = soup.find_all('div', {'class': 'unpl block info'})

    if not outage_blocks:
        print("Could not find any outage blocks on the page.")
        return

    found = False
    for block in outage_blocks:
        description = block.find('p', {'class': 'description'})
        if description and street_name in description.get_text():
            found = True
            area = block.find('h4', {'class': 'title_'}).get_text(strip=True)
            date_info = block.find('p', {'class': 'bold subtext'}).get_text(strip=True)
            
            print(f"Found outage information for {street_name}:")
            print(f"  Obszar: {area}")
            print(f"  Szczegóły: {description.get_text(strip=True)}")
            print(f"  Data: {date_info}")
            print("-" * 20)

    if not found:
        print(f"No outage information found for {street_name}.")

if __name__ == "__main__":
    check_outage()
