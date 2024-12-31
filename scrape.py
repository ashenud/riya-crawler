import requests
from bs4 import BeautifulSoup
import csv
import time

# Define the base URL
BASE_URL = "https://riyasewana.com/search"

# Function to extract data from a single page
def extract_data(page):
    url = f"{BASE_URL}?page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
            place = listing.find('div', class_='boxintxt').text.strip()
            price = listing.find('div', class_='boxintxt b').text.strip()
            mileage = listing.find('div', class_='boxintxt', text=lambda x: x and 'km' in x).text.strip()
            date_added = listing.find('div', class_='boxintxt s').text.strip()

            car_data.append({
                'Name': name,
                'Place': place,
                'Price': price,
                'Mileage': mileage,
                'Date Added': date_added
            })
        except AttributeError:
            # Skip any listings with missing fields
            continue

    return car_data

# Function to write data to a CSV file
def write_to_csv(data, filename="car_listings.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Name', 'Place', 'Price', 'Mileage', 'Date Added'])
        writer.writeheader()
        writer.writerows(data)

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
        write_to_csv(all_car_data)
        print(f"Scraped data saved to car_listings.csv")
    else:
        print("No data scraped.")

if __name__ == "__main__":
    main()
