import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

# Replace 'your_url_here' with the URL of the webpage you want to scrape
url = 'https://open.spotify.com/'

# Function to click the button after waiting for 3 seconds
def click_button_with_delay(url):
    # Configure Firefox options
    options = Options()
    options.headless = False  # Set to True if you don't want to see the browser window

    # Initialize Firefox WebDriver
    driver = webdriver.Firefox(options=options)
    
    # Open the URL in Firefox
    driver.get(url)
    
    # Wait for the page to load (you might need to adjust the waiting time based on your internet speed)
    time.sleep(50000000)
    
    # Extract the HTML content
    html_content = driver.page_source
    
    # Print the HTML content of the webpage
    print("HTML content of the webpage:")
    print(html_content)
    
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the button element
    button = soup.find('button', {'class': 'mnipjT4SLDMgwiDCEnRC'})
    
    # Extract the value of the 'data-testid' attribute
    data_test_id = button.get('data-testid', '') if button else None
    
    # Extract the value of the 'aria-label' attribute
    aria_label = button.get('aria-label', '') if button else None
    
    # Print the extracted attributes (optional)
    print("data-testid:", data_test_id)
    print("aria-label:", aria_label)
    
    # Close the browser window
    driver.quit()

# Call the function to click the button after a delay
click_button_with_delay(url)
