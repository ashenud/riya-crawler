import requests
from bs4 import BeautifulSoup
import time
import gspread
from google.oauth2.service_account import Credentials

# Constants
BASE_URL = "https://riyasewana.com/search/cars/2010-0/automatic/price-0-5000000"
SERVICE_ACCOUNT_FILE = "google_service_account.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwiaj3HWPk1WX43unCrrKXMuvRhCntYW_70Sco5lzbkRwtzdYi4pZfEFXcWasxS-nYG/exec"
SPREADSHEET_NAME = "Car Listings"
WORKSHEET_NAME = "Cars"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Google Sheets setup
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

def extract_detailed_data(link: str) -> dict:
    try:
        soup = BeautifulSoup(requests.get(link, headers=HEADERS, timeout=10).text, 'html.parser')
        table = soup.find('table', class_='moret')
        if not table: return {}

        details = {}
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) == 2:
                details[cols[0].text.strip()] = cols[1].text.strip()
            elif len(cols) == 4:
                details.update({
                    cols[0].text.strip(): cols[1].text.strip(),
                    cols[2].text.strip(): cols[3].text.strip()
                })
        return details
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {link}: {e}")
        return {}

def extract_data(page: int) -> list:
    url = f"{BASE_URL}?page={page}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    car_listings = soup.find_all('li', class_='item')[4:]  # Skip the first 4 listings

    car_data = []
    for l in car_listings:
        try:
            name = l.find('a', title=True).get('title', '').strip()
            link = l.find('a', title=True).get('href', '').strip()
            image_url = "https:" + l.find('img')['src'].strip()
            place = l.find('div', class_='boxintxt').text.strip()
            price = l.find('div', class_='boxintxt b').text.strip()
            mileage_elem = l.find('div', class_='boxintxt', string=lambda x: x and 'km' in x)
            mileage = mileage_elem.text.strip() if mileage_elem else 'N/A'
            date_added = l.find('div', class_='boxintxt s').text.strip()

            details = extract_detailed_data(link)

            car_data.append({
                'Name': name,
                'Link': link,
                'Image URL': image_url,
                'Place': place,
                'Price': price,
                'Mileage': mileage,
                'Date Added': date_added,
                'Contact': details.get('Contact', ''),
                'Make': details.get('Make', ''),
                'Model': details.get('Model', ''),
                'YOM': details.get('YOM', ''),
                'Gear': details.get('Gear', ''),
                'Fuel Type': details.get('Fuel Type', ''),
                'Details': details.get('Details', ''),
            })
        except AttributeError:
            continue

    return car_data

def save_to_google_sheets(data: list):
    try:
        ws = gc.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        existing_links = {row['Link'] for row in ws.get_all_records()}
        new_rows = [list(row.values()) for row in data if row['Link'] not in existing_links]
        if new_rows:
            ws.append_rows(new_rows)
            print(f"Added {len(new_rows)} entries.")
        else:
            print("No new data to add.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")

def call_load_image_from_url_web_app():
    try:
        res = requests.get(WEB_APP_URL)
        res.raise_for_status()
        print(f"Web App executed: {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Web App: {e}")

def main():
    all_data = []
    for page in range(1, 11):
        print(f"Scraping page {page}...")
        data = extract_data(page)
        if not data:
            print(f"No data on page {page}, stopping.")
            break
        all_data.extend(data)
        time.sleep(1)
    if all_data:
        save_to_google_sheets(all_data)
        call_load_image_from_url_web_app()
    else:
        print("No data scraped.")

if __name__ == "__main__":
    main()
