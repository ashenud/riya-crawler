import requests
from bs4 import BeautifulSoup
import time
import gspread
from google.oauth2.service_account import Credentials

# Constants
BASE_URL = "https://riyasewana.com/search/cars/2010-0/automatic/price-0-5000000"  # Base URL for scraping car listings
SERVICE_ACCOUNT_FILE = "google_service_account.json"  # Service account file for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']  # Scopes for Google APIs
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwiaj3HWPk1WX43unCrrKXMuvRhCntYW_70Sco5lzbkRwtzdYi4pZfEFXcWasxS-nYG/exec"  # Web app URL for loading images
SPREADSHEET_NAME = "Car Listings"  # Name of the Google Sheet
WORKSHEET_NAME = "Cars"  # Name of the worksheet in the Google Sheet

# Google Sheets setup
# Authenticate and initialize Google Sheets API client
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# User-Agent header for web scraping to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Function to extract data from a single listing page
def extract_detailed_data(link: str) -> dict:
    """
    Scrapes detailed car data from a specific car's link.
    """
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details from {link}: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='moret')
    if not table:
        return {}

    details = {}
    rows = table.find_all('tr')
    for row in rows:
        columns = row.find_all('td')
        if len(columns) == 2:
            header = columns[0].text.strip()
            value = columns[1].text.strip()
            details[header] = value
        elif len(columns) == 4:
            details[columns[0].text.strip()] = columns[1].text.strip()
            details[columns[2].text.strip()] = columns[3].text.strip()

    return details

# Function to extract summary data from a single page
def extract_data(page: int) -> list:
    url = f"{BASE_URL}?page={page}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return []

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
    car_listings = soup.find_all('li', class_='item')

    # Skip the first 4 listings as per requirements
    car_listings = car_listings[4:]

    car_data = []
    # Extract data from each car listing
    for listing in car_listings:
        try:
            name = listing.find('a', title=True).get('title', '').strip()
            link = listing.find('a', title=True).get('href', '').strip()  # Extract unique link
            image_url = "https:" + listing.find('img')['src'].strip()  # Construct full image URL
            place = listing.find('div', class_='boxintxt').text.strip()
            price = listing.find('div', class_='boxintxt b').text.strip()
            mileage = listing.find('div', class_='boxintxt', string=lambda x: x and 'km' in x).text.strip()
            date_added = listing.find('div', class_='boxintxt s').text.strip()

            # Fetch additional details from the listing page
            details = extract_detailed_data(link)

            car_data.append({
                'Name': name,
                'Link': link,  # Link used as a unique identifier
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
            # Skip listings with missing fields
            continue

    return car_data

# Function to save data to Google Sheets
def save_to_google_sheets(data: list):
    """
    Saves the scraped data to the specified Google Sheet.
    Updates only new records using the 'Link' field as a unique identifier.
    """
    try:
        # Open the spreadsheet and worksheet
        spreadsheet = gc.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")
        return

    # Fetch existing data to avoid duplicates
    existing_data = worksheet.get_all_records()
    existing_links = {row['Link'] for row in existing_data}

    # Filter out data that already exists
    new_data = [row for row in data if row['Link'] not in existing_links]

    if new_data:
        # Prepare rows for batch insertion
        rows = [[row['Name'], row['Link'], row['Image URL'], row['Place'], row['Price'], row['Mileage'], row['Date Added'], row['Contact'], row['Make'], row['Model'], row['YOM'], row['Gear'], row['Fuel Type'], row['Details']] for row in new_data]
        worksheet.append_rows(rows)  # Append new rows
        print(f"Added {len(new_data)} new entries to Google Sheets.")
    else:
        print("No new data to add.")

# Function to trigger the Google Apps Script Web App for loading image URLs
def call_load_image_from_url_web_app():
    """
    Triggers a Google Apps Script Web App to load images from URLs in the spreadsheet.
    """
    try:
        response = requests.get(WEB_APP_URL)
        response.raise_for_status()  # Ensure successful request
        print(f"Load image from URL executed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Web App: {e}")

# Main function to scrape multiple pages
def main():
    """
    Scrapes car data from multiple pages, updates Google Sheets,
    and triggers the image loader web app.
    """
    all_car_data = []

    for page in range(1, 10):  # Adjust the range as needed
        print(f"Scraping page {page}...")
        car_data = extract_data(page)
        if not car_data:
            print(f"No data found for page {page}, stopping scrape.")
            break
        all_car_data.extend(car_data)
        time.sleep(1)  # Delay to avoid overwhelming the server

    if all_car_data:
        save_to_google_sheets(all_car_data)
        call_load_image_from_url_web_app()
        print("Scraped data saved to Google Sheets.")
    else:
        print("No data scraped.")

if __name__ == "__main__":
    main()
