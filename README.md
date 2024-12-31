Car Listings Web Scraper
========================

Description
-----------

This Python script scrapes car listings from the website [Riyasewana](https://riyasewana.com), focusing on automatic cars priced between 0 and 5,000,000 LKR from the year 2010 onwards. It extracts detailed information from the car listings, including the car's name, image URL, place, price, mileage, and other car details. The extracted data is then saved to a Google Sheets document for easy access and tracking.

You can add filters to the base URL for specific criteria like price, year, and transmission type, as provided by Riyasewana.

Features
--------

-   Scrapes car listings from multiple pages of Riyasewana.
-   Extracts detailed car information, including contact details, make, model, year of manufacture (YOM), gear type, fuel type, and more.
-   Saves the scraped data to Google Sheets for better organization and record-keeping.
-   Automatically avoids duplicate entries based on car links.
-   Calls a web application after saving the data to trigger any necessary image loading.

Requirements
------------

-   Python 3.x
-   Required libraries: `requests`, `BeautifulSoup4`, `gspread`, `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`
-   Google Sheets API credentials (`google_service_account.json`)

Setup
-----

### 1\. Install Python dependencies

Make sure you have the following Python libraries installed:

```
pip install requests beautifulsoup4 gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 2\. Google Sheets API Setup

-   Create a project in Google Cloud Console.
-   Enable the Google Sheets API and the Google Drive API.
-   Create a Service Account and download the JSON credentials file (`google_service_account.json`).
-   Share your Google Sheets document with the service account email.

### 3\. Prepare Google Sheets

Create a Google Sheets document with the following:

-   **Name**: Car Listings
-   **Worksheet Name**: Cars
-   **Headers**: `Name` `Link` `Image URL`  `Place` `Price` `Mileage` `Date Added` `Contact` `Make` `Model` `YOM` `Gear` `Fuel Type`  `Details`

### 4\. Create Google Sheets Apps Script

To load images directly into the Google Sheets cells, you need to create a Google Sheets Apps Script. Follow the steps below:

1.  Open your Google Sheets document.
2.  Click on `Extensions` > `Apps Script`.
3.  Replace the existing code with the following:
    ```
    function loadImageFromURL() {
      var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
      // Define the range of cells to check (for example, column A from row 1 to the last row)
      var range = sheet.getRange("C2:C" + sheet.getLastRow());
      var values = range.getValues();
    
      // Loop through each cell in the range
      for (var i = 0; i < values.length; i++) {
        var cellValue = values[i][0];
    
        // Skip if the cellValue is already in the IMAGE formula format
        if (typeof cellValue === 'string' === false) {
          continue;
        }
    
        range.getCell(i + 1, 1).setFormula('=IMAGE("' + cellValue + '")');
      }
    }
    
    // Web app endpoint
    function doGet() {
      loadImageFromURL();  // Run the loadImageFromURL function
      return ContentService.createTextOutput('Load the images from URLs.');
    }
    ```

1.  Save the script and deploy it as a web app:
    -   Click on `Deploy` > `Test deployments` > `Select type` > `Web app`.
    -   Set the `Execute as` option to "Me" and `Who has access` to "Anyone".
    -   Click `Deploy`.
    -   Copy the web app URL (this will be used in the Python script).

### 5\. Configuration

Make sure to update the following variables in the script with your own values:
```
SERVICE_ACCOUNT_FILE = "google_service_account.json"  # Path to your Google Service Account credentials JSON
BASE_URL = "https://riyasewana.com/search/cars/2010-0/automatic/price-0-5000000"  # Base URL for scraping
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwiaj3HWPk1WX43unCrrKXMuvRhCntYW_70Sco5lbkRwtzdYi4pZfEFXcWasxS-nYG/exec"
SPREADSHEET_NAME = "Car Listings"  # Name of the Google Spreadsheet
WORKSHEET_NAME = "Cars"  # Name of the worksheet within the spreadsheet
```

### 6\. Add Filters to Base URL

The base URL provided in the script can be filtered based on different criteria such as price, year, and transmission type. For example:

-   **Year**: `/search/cars/2010-0/`
-   **Transmission**: `/search/cars/automatic/`
-   **Price**: `/search/cars/price-0-5000000`

You can modify the `BASE_URL` in the script to add additional filters. For example:
```
BASE_URL = "https://riyasewana.com/search/cars/2010-0/automatic/price-1000000-3000000"
```

You can customize the URL further by changing the parameters for different search criteria, as per Riyasewana's search options.

### 7\. Running the Script

Once everything is set up, you can run the script by executing:

```
python3 scrape.py
```

The script will:

1.  Scrape the car listings from the site.
2.  Extract detailed information for each car.
3.  Check for existing listings in the Google Sheets document.
4.  Add new car listings to Google Sheets.
5.  Call the provided web application URL to trigger any additional actions, such as loading images.

### 8\. Output

The script will output the following columns in the Google Sheets document:

-  `Name` `Link` `Image URL`  `Place` `Price` `Mileage` `Date Added` `Contact` `Make` `Model` `YOM` `Gear` `Fuel Type`  `Details`

The script avoids adding duplicate entries by checking the car links before inserting new data.

### 9\. Image Loading in Google Sheets

To load images from the URLs directly into the spreadsheet cells, the script will call the Google Sheets Apps Script that you created earlier. The script will insert the `=IMAGE("<image_url>")` formula into the cells under the "Image URL" column.

### Troubleshooting

-   **Error fetching data**: If you encounter an error fetching the data (like a timeout or connection issue), ensure your internet connection is stable and retry.
-   **Google Sheets not found**: If the script cannot find the Google Sheets document, make sure the `SPREADSHEET_NAME` is correct and the service account has been granted access to the document.
-   **Missing headers**: Ensure the Google Sheets document has the necessary headers in the first row.
-   **Image loading issues**: If images are not being loaded properly, verify that the `WEB_APP_URL` is correct and accessible.

License
-------
This project is open-source and free to use.
