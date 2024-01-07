import logging
import time
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from maps_scraper.drivers import create_driver
from maps_scraper.entities import Place
from maps_scraper.config import settings

from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

SEARCH = input("Enter the search term for Google Maps: ")
LATITUDE = 21.020833
LONGITUDE = 105.511944
ZOOM_LEVEL = 14

BASE_URL = "https://www.google.com/maps/search/{search}/@{latitude},{longitude},{zoom_level}z?hl=en"

FINAL_URL = BASE_URL.format(search=SEARCH, latitude=LATITUDE, longitude=LONGITUDE, zoom_level=ZOOM_LEVEL)

logger = logging.getLogger(__name__)

def find_elements_by_attribute(tag: str, attr_name: str, attr_value: str) -> list[WebElement]:
    query = f"{tag}[{attr_name}='{attr_value}']"
    elements = driver.find_elements(By.CSS_SELECTOR, query)
    return elements

def find_element_by_attribute(tag: str, attr_name: str, attr_value: str) -> WebElement:
    return find_elements_by_attribute(tag, attr_name, attr_value)[0]

def find_element_by_aria_label(tag: str, attr_value: str) -> WebElement:
    return find_element_by_attribute(tag, "aria-label", attr_value)

class GMapsNavigator:
    def __init__(self, driver) -> None:
        self.driver = driver
        self.place_idx = 0
        self.place_labels = []
        
    def _get_places_wrapper(self) -> WebElement:
        return WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, f"//div[@aria-label='Results for {SEARCH}']"))
        )
        
    def _capture_place_labels(self):
        try:
            places_wrapper = self._get_places_wrapper()
            
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", places_wrapper)
            
            scroll_count = 0  # Counter to limit the number of scrolls
            max_scrolls = 4   # Maximum number of scrolls for testing; adjust as needed
            
            while True:
                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", places_wrapper)
                try:
                    WebDriverWait(self.driver, 3).until(
                        lambda d: d.execute_script("return arguments[0].scrollHeight", places_wrapper) > last_height
                    )
                except TimeoutException:
                    self.scroll_up_slightly()

                new_height = self.driver.execute_script("return arguments[0].scrollHeight", places_wrapper)
                # or scroll_count >= max_scrolls
                if new_height == last_height or scroll_count >= max_scrolls: 
                    break
                last_height = new_height
                scroll_count += 1
                
            # Now scroll back to the top
            self.driver.execute_script("arguments[0].scrollTo(0, 0);", places_wrapper)
            
            all_divs = self._get_places_wrapper().find_elements(By.XPATH, "./div")
            # Clear existing labels
            self.place_labels = []

            # Capture aria-label values
            for i, div in enumerate(all_divs):
                if i % 2 == 0 and i > 1:
                    aria_labels = div.find_elements(By.CSS_SELECTOR, "a[aria-label]")
                    if aria_labels:
                        aria_label = aria_labels[0].get_attribute("aria-label")
                        
                        if '\'' not in aria_label:
                            self.place_labels.append(aria_label)
                        
        except Exception as e:
            logger.error(f"Error capturing place labels: {e}")
            raise

    @property
    def has_next_place(self) -> bool:
        return self.place_idx < len(self.place_labels)

    def scroll_up_slightly(self):
        scroll_amount = -100
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(2)
    
    def __iter__(self):
        return self

    def __next__(self) -> WebElement:
        return True

class GMapsPlacesCrawler:
    def __init__(self, driver) -> None:
        self.navigator = GMapsNavigator(driver)
        self.places_data = []  # Initialize an empty list to store place data
        
    def get_place_detail_wrapper(self, aria_label: str) -> WebElement:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[@aria-label='{aria_label}']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            
            review_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//div[@aria-label='{aria_label}']"))
            )
            return review_element

        except NoSuchElementException:
            places_wrapper = self._get_places_wrapper()
            driver.execute_script(f"arguments[0].scrollTo(0, 100);", places_wrapper)
            # Handle or re-raise exception as needed after scrolling
            raise
            
        
    def get_places(self):
        try:
            with open('places_data.json', 'r', encoding='utf-8') as file:
                # Load existing data or initialize as empty list if file is empty
                self.places_data = json.load(file) if file.read().strip() else []
        except FileNotFoundError:
            # If file doesn't exist, initialize as empty list
            self.places_data = []
        
        
        try:
            self.navigator._capture_place_labels()
        
            for aria_label in self.navigator.place_labels:
            # Use the aria-label to find and click the a tag
                attempts = 0
                max_attempts = 2
                while attempts < max_attempts:
                    try:
                        place_detail_wrapper = self.get_place_detail_wrapper(aria_label) 
                        if place_detail_wrapper:
                            logger.info(f"Processing place {aria_label}")
                            place_data = self.get_place_details(aria_label)
                            
                            # Append the new place data and write to file each loop
                            self.places_data.append(place_data)
                            with open('places_data.json', 'w', encoding='utf-8') as file:
                                json.dump(self.places_data, file, ensure_ascii=False, indent=4)
                        break
                    except Exception as e:
                        logger.error(f"An error occurred in get_places_details.")
                        attempts += 1
                        logger.info(f"Retrying... Attempt {attempts} of {max_attempts}")
            
            # Write the data to a JSON file
            with open('places_data.json', 'w', encoding='utf-8') as file:
                json.dump(place_data, file, ensure_ascii=False, indent=4)
            
        except Exception as e:
            logger.error(f"An error occurred during get_places processing: {aria_label}")
        
    def refresh_place_detail_wrapper(self, aria_label: str) -> WebElement:
        return driver.find_element(By.XPATH, f"//div[@aria-label='{aria_label}']")
        
    def get_place_details(self, aria_label: str):
        # Initialize default values for place data
        place_name, address, business_hours, phone_number, photo_link, rate, reviews = '', '', {}, '', '', '', []
    
        # DATA
        place_name = self.get_place_name(aria_label)
        address = self.get_address(aria_label)
        business_hours = self.get_business_hours(aria_label)
        phone_number = self.get_phone_number(aria_label)
        photo_link = self.get_image_link(aria_label)
        rate, reviews = self.get_review(aria_label)

        place = {
            "name": place_name,
            "address": address,
            "business_hours": business_hours,
            "phone_number": phone_number,
            "photo_link": photo_link,
            "rate": rate,
            "reviews": reviews
        }
        
        place_log = Place(place_name, address, business_hours, phone_number, photo_link, rate, reviews)
        logger.info(place_log)
        
        return place
        
    def get_place_name(self, aria_label: str) -> str:
        place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
        place_name_element = place_detail_wrapper.find_element(By.TAG_NAME, "h1")
        return place_name_element.text

    def get_address(self, aria_label: str) -> str:
        # Locate the specific div with the aria-label "Information for aria_label"
        place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
        info_div = place_detail_wrapper.find_element(By.XPATH, f"//div[@aria-label='Information for {aria_label}']")

        # Find the button within this div that contains the address
        address_button = info_div.find_element(By.XPATH, "//button[starts-with(@aria-label, 'Address:')]")
        
        # Extract the address from the aria-label attribute of the button
        address_aria_label = address_button.get_attribute("aria-label")
        address = address_aria_label.split("Address: ", 1)[1] if "Address: " in address_aria_label else ""

        return address

    def get_phone_number(self, aria_label: str) -> str:
        try:
            place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
            phone_button = place_detail_wrapper.find_element(By.XPATH, ".//button[contains(@aria-label, 'Phone:')]")
            
            # Extract the aria-label attribute
            phone_label = phone_button.get_attribute("aria-label").strip()

            # Parse the phone number from the aria-label
            phone_number = phone_label.split("Phone: ", 1)[1] if "Phone: " in phone_label else ""

            return phone_number

        except NoSuchElementException as e:
            # If the phone number button is not found, just return an empty string
            return ""
   
    def get_business_hours(self, aria_label: str) -> dict[str, str]:
        business_hours = {}

        try:
            place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
            business_hours_div = place_detail_wrapper.find_element(By.XPATH, ".//div[contains(@aria-label, 'Hide open hours for the week')]")
            
            # Find the table within this div
            business_hours_table = business_hours_div.find_element(By.XPATH, ".//table")

            # Iterate over each row in the table to extract the day and hours
            for row in business_hours_table.find_elements(By.XPATH, ".//tr"):
                day_element = row.find_element(By.XPATH, ".//td[1]/div").get_attribute('textContent').strip()
                hours_element = row.find_element(By.XPATH, ".//td[2]").get_attribute("aria-label").strip().replace('\u202f', ' ')
                
                # logging.info(f"Day: {day_element}, Hours: {hours_element}")

                if day_element and hours_element:
                    business_hours[day_element] = hours_element

        except NoSuchElementException:
            # If the business hours div is not found, just return an empty dict
            pass

        return business_hours

    def get_image_link(self, aria_label: str) -> str:
        try:
            place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
            cover_img = place_detail_wrapper.find_element(By.XPATH, ".//img[@decoding='async']")
            return cover_img.get_property("src")

        except NoSuchElementException as e:
            # If the image is not found, return an empty string
            return ""
        
    def get_all_review_details_js(self, driver, reviews_container):
        """
        Use JavaScript to extract all review details (name, rating, time, content) 
        for all reviews in the container.
        Returns a list of dictionaries containing these details.
        """
        script = """
        var reviews = arguments[0].querySelectorAll('div[data-review-id]');
        var reviewDetails = [];
        reviews.forEach(function(review) {
            var ratingSpan = review.querySelector('div > div > div:nth-child(4) > div:nth-child(1) > span:nth-child(1)');
            var rating = ratingSpan ? ratingSpan.getAttribute('aria-label') : '';
            var reviewTimeSpan = review.querySelector('div > div > div:nth-child(4) > div:nth-child(1) > span:nth-child(2)');
            var reviewTime = reviewTimeSpan ? reviewTimeSpan.innerText.trim() : '';
            var contentSpan = review.querySelector('div > div > div:nth-child(4) > div:nth-child(2) > div > span');
            var content = contentSpan ? contentSpan.innerText.trim() : '';
            reviewDetails.push({rating, reviewTime, content});
        });
        return reviewDetails;
        """
        return driver.execute_script(script, reviews_container) 
        
    def get_review(self, aria_label: str) -> tuple[str, str]:
        reviews = []
        rate = ""
        
        try:
            place_detail_wrapper = self.refresh_place_detail_wrapper(aria_label)
            
            reviews_button = WebDriverWait(place_detail_wrapper, 2).until(
                EC.element_to_be_clickable((By.XPATH, f".//button[@aria-label='Reviews for {aria_label}']"))
            )
            reviews_button.click()
          
            while True:
                try:
                    rating_div = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.XPATH, ".//div[@class='fontDisplayLarge']"))
                    )
                    rate = rating_div.text.strip()
                    break
                except StaleElementReferenceException:
                    # logger.error("Stale element reference when accessing rating_div.")
                    continue
            
            def find_scrollable_container():
                try:
                    scrollable_container = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"//div[@aria-label='{aria_label}']/div[3]"))
                    )
                    return scrollable_container
                except Exception as e:
                    logging.error(f"Error finding scrollable container.")
                
            # Scroll to the bottom of the scrollable reviews container
            last_height = driver.execute_script("return arguments[0].scrollHeight", find_scrollable_container())
            
            while True:
                try:
                    scrollable_container = find_scrollable_container()
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_container)
                    time.sleep(1)  # Sleep to allow loading of new elements

                    new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_container)
                    
                    if new_height == last_height:
                        break
                    last_height = new_height
                except StaleElementReferenceException:
                    continue  # Retry loop with fresh element
            
            # Click all 'More' buttons in batch
            more_buttons = find_scrollable_container().find_elements(By.XPATH, ".//button[@aria-label='See more']")
            for button in more_buttons:
                driver.execute_script("arguments[0].click();", button)
            
            # Extract reviews from the 8th child of scrollable_reviews_container
            try:
                reviews_container = WebDriverWait(find_scrollable_container(), 5).until(
                    EC.visibility_of_element_located((By.XPATH, "./div[8]"))
                )
            except Exception as e:
                logging.error("Timeout waiting for the reviews container to be visible.")
            
            # Use JavaScript to get all review details at once
            review_details = self.get_all_review_details_js(driver, reviews_container)
            
            for i, detail in enumerate(review_details):
                try:
                    # Extract each detail from the JavaScript output
                    rating = detail['rating']
                    review_time = detail['reviewTime']
                    review_content = detail['content']
                    
                    reviews.append({
                        "review_time": review_time,
                        "rating": rating,
                        "review_content": review_content
                    })
                    
                except NoSuchElementException as e:
                    logging.warning(f"An error with review {i+1} was found. Skipping this review. {e}. ")

        except NoSuchElementException:
            logging.error("Element not found.")
        except TimeoutException:
            logging.error("Timeout waiting for reviews to be visible.")
        except Exception as e:
            logging.error("An error occurred in get_review.")

        logging.info("Completed getting reviews. Total reviews: {}".format(len(reviews)))
        return rate, reviews

if __name__ == "__main__": 
    logger.info("[bold yellow]== * Running Gmaps Scraper ==[/]", extra={"markup": True})
    settings.dict()
    driver = create_driver()
    driver.get(FINAL_URL)

    crawler = GMapsPlacesCrawler(driver)
    try:
        crawler.get_places()
    except (ValueError) as e:
        logger.error(e)
    finally:
        input("Press Enter to exit...")  # Wait for user input before exiting.
    
