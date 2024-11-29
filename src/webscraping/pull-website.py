from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

ID_LIST_FILE = ""
UNFINISHED_URL_FILE = ""

def scroll_to_bottom(driver):
    """
    Scrolls to the bottom of a webpage to load all dynamic content.

    Parameters:
        driver (webdriver): The Selenium WebDriver instance controlling the browser.

    Notes:
        - The function repeatedly scrolls down until the page height no longer changes, 
          indicating that all content has been loaded.
        - A delay is included to allow new content to load dynamically.
    """
    # Get current page height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for the page to load new content
        time.sleep(2)  # Adjust the time as needed

        # Calculate new page height and compare with previous height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break  # If the height hasn't changed, we are at the bottom of the page.
        last_height = new_height

# Call the function to scroll to the bottom of the page

def scrolling_loop():
    """
    Scrolls through a webpage and attempts to click the "Show more" button repeatedly.

    Notes:
        - The function waits for the "Show more" button to appear and become clickable. 
          Once clicked, it waits for new content to load before scrolling further.
        - If the button cannot be found for 10 consecutive attempts, the loop exits.
        - Used to dynamically expand content-heavy pages.
    """
    cont = 0 # Counter to track failed attempts to find the "Show more" button
    while True:
        try:  
            # Wait until the "Show more" button is present and visible
            show_more_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.section__link-out[role='link']"))
            )
            scroll_to_bottom(driver)
            # Click on the "Show more" button
            driver.execute_script("arguments[0].click();", show_more_button)

            # Please wait a while to allow the content to load.
            time.sleep(1)
            scroll_to_bottom(driver)
            cont = 0 # Reset the counter after a successful action
        except Exception as e:
            # If we don't find the button, we exit the loop.
            cont += 1
            if cont == 10:
                break
            print(e)
            print("All elements were loaded or an error occurred.")

links = None
species = set()

service = Service('/snap/bin/firefox.geckodriver')  # Replace with the path to your ChromeDriver

# List of URLs containing filters for the general species list
# Modify this variable to include your urls
urls = []

for url in urls:
    driver = webdriver.Firefox(service=service)
    driver.get(url)
    number_of_results = 0
    count = 0

    while number_of_results == 0 and count < 10:  
        try:   
            time.sleep(3)
            number_of_results = int(driver.find_element(By.CSS_SELECTOR, "h1[class='heading heading--list']").find_element(By.XPATH, ".//span").text[1:-1])
        except: 
            count += 1
    if number_of_results == 0:
        print("Unable to load page.")
        break
    driver.quit()

    url_species = set()
    print(number_of_results)
    for i in range(5):
        driver = webdriver.Firefox(service=service)
        driver.get(url)
        try:
            # Change the page layout from "grid" to "list"
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[class='nav-page__item nav-page__item--list']"))
            )
            element.click()
            time.sleep(5)     
        except:
            print("Unable to click on the list.")
        
        # Loop to scroll to the bottom of the page until the list of results can no longer be expanded
        scrolling_loop()
        
        links = driver.find_elements(By.TAG_NAME, 'a')
        # Extract and print the 'href' attributes of each link
        for link in links:
            href = link.get_attribute('href')
            if href:  # Checks if href is not None
                s = href.strip().split("/")
                if len(s) > 3 and s[-3] == "species":
                    url_species.add(int(s[-2]))
        driver.quit()

        print(url_species)
        if len(url_species) == number_of_results:
            break

        time.sleep(60)
    
    species = species.union(url_species)
    if len(url_species) != number_of_results:
        with open(UNFINISHED_URL_FILE, "a+") as f:
            f.write(f"{url} needs to be split, couldn't get all ids.\n")

with open(ID_LIST_FILE, "w") as file:
    for i in species:
        file.write(f"{i}\n")

    
        
