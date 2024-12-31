import requests
from bs4 import BeautifulSoup
import time
import gspread
from google.oauth2.service_account import Credentials

# Constants
BASE_URL = "https://riyasewana.com/search"
SERVICE_ACCOUNT_FILE = "google_service_account.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwiaj3HWPk1WX43unCrrKXMuvRhCntYW_70Sco5lzbkRwtzdYi4pZfEFXcWasxS-nYG/exec"
SPREADSHEET_NAME = "Car Listings"
WORKSHEET_NAME = "Cars"

# Google Sheets setup
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# User-Agent header for web scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Function to extract data from a single page
def extract_data(page: int) -> list:
    url = f"{BASE_URL}?page={page}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an error for bad HTTP responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    car_listings = soup.find_all('li', class_='item')

    car_data = []
    for listing in car_listings:
        try:
            name = listing.find('a', title=True).get('title', '').strip()
            link = listing.find('a', title=True).get('href', '').strip()  # Extract link
            image_url = "https:" + listing.find('img')['src'].strip()  # Extract image URL and complete the URL
            place = listing.find('div', class_='boxintxt').text.strip()
            price = listing.find('div', class_='boxintxt b').text.strip()
            mileage = listing.find('div', class_='boxintxt', string=lambda x: x and 'km' in x).text.strip()
            date_added = listing.find('div', class_='boxintxt s').text.strip()

            car_data.append({
                'Name': name,
                'Link': link,  # Add link to data
                'Image URL': image_url,
                'Place': place,
                'Price': price,
                'Mileage': mileage,
                'Date Added': date_added
            })
        except AttributeError:
            # Skip any listings with missing fields
            continue

    return car_data

# Function to save data to Google Sheets
def save_to_google_sheets(data: list):
    try:
        spreadsheet = gc.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")
        return

    # Add headers and batch data in one go
    headers = ['Name', 'Link', 'Image URL', 'Place', 'Price', 'Mileage', 'Date Added']
    worksheet.clear()  # Optionally clear existing data before adding new data
    worksheet.append_row(headers)

    # Prepare rows in a batch format (list of lists)
    rows = [[row['Name'], row['Link'], row['Image URL'], row['Place'], row['Price'], row['Mileage'], row['Date Added']] for row in data]
    worksheet.append_rows(rows)  # Batch append rows

    print(f"Data saved to Google Sheet '{SPREADSHEET_NAME}' in worksheet '{WORKSHEET_NAME}'.")

# Function to trigger the Google Apps Script Web App for loading image URLs
def call_load_image_from_url_web_app():
    try:
        response = requests.get(WEB_APP_URL)
        response.raise_for_status()  # Check for successful response
        print(f"Load image from URL executed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Web App: {e}")

# Main function to scrape multiple pages
def main():
    all_car_data = []

    for page in range(1, 5):  # Adjust the range for more pages
        print(f"Scraping page {page}...")
        car_data = extract_data(page)
        if not car_data:
            print(f"No data found for page {page}, stopping scrape.")
            break
        all_car_data.extend(car_data)
        time.sleep(1)  # Add delay to prevent overwhelming the server

    if all_car_data:
        save_to_google_sheets(all_car_data)
        call_load_image_from_url_web_app()
        print(f"Scraped data saved to Google Sheets.")
    else:
        print("No data scraped.")

if __name__ == "__main__":
    main()
