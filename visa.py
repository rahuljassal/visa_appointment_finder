from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
import time
import logging
import requests
import os
from dotenv import load_dotenv
import warnings
import urllib3
from datetime import datetime, timedelta

# warning handling before /on sending the post request
warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()


# Launch of Chrome browser
def chrome():
    global driver
    try:
        logging.info("Initializing Chrome options...")
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "profile.default_content_settings.popups": 0,
            "directory_upgrade": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Add these options for GitHub Actions
        chrome_options.add_argument("--headless=new")  # Updated headless mode syntax
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")

        logging.info("Starting Chrome driver...")
        if os.getenv("GITHUB_ACTIONS") == "true":
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("Chrome driver started in GitHub Actions environment")
        else:
            service = Service(
                r"/Users/rahuljassal/Downloads/chromedriver-mac-arm64/chromedriver"
            )
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info("Chrome driver started in local environment")

        time.sleep(2)
    except Exception as e:
        logging.error(f"Error in Chrome initialization: {str(e)}", exc_info=True)


# Check URL Status
def visa_appointment_check(url):
    try:
        chrome()
        logging.info(str(url))
        try:
            driver.get(url)
            driver.maximize_window()
            logging.info("Opened Url...")
            # Accept cookies if present
            try:
                cookie_button = WebDriverWait(url, 5).until(
                    EC.presence_of_element_located((By.ID, "accept-cookies"))
                )
                time.sleep(2)
                cookie_button.click()
                logging.info("cookie button clicked")
            except:
                pass
            # Click sign in
            sign_in = driver.find_element(By.LINK_TEXT, "Sign In")
            time.sleep(2)
            sign_in.click()
            logging.info("Sign In Button Clicked")

            # Fill login form
            driver.find_element(By.ID, "user_email").send_keys(os.getenv("email"))
            time.sleep(2)
            logging.info("Email enetered")
            driver.find_element(By.ID, "user_password").send_keys(os.getenv("password"))
            time.sleep(2)
            logging.info("Password entered")
            driver.find_element(
                By.XPATH,
                "/html/body/div[5]/main/div[3]/div/div[1]/div/form/div[3]/label/div",
            ).click()
            time.sleep(2)
            logging.info("Checkbox ticked")
            driver.find_element(By.NAME, "commit").click()
            time.sleep(2)
            logging.info("Sign In Button Clicked")
            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div[1]/div/div/div[1]/div[2]/ul/li",
            ).click()
            logging.info("Continue clicked")
            time.sleep(5)
            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div/section/ul/li[4]/a/h5",
            ).click()
            time.sleep(2)
            logging.info("Reschedule app 1 clicked")
            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div/section/ul/li[4]/div/div/div[2]/p[2]/a",
            ).click()
            logging.info("Reschedule app 2 clicked")
            time.sleep(2)
            driver.find_element(
                By.XPATH, "/html/body/div[4]/main/div[3]/form/div[2]/div/input"
            ).click()
            logging.info("Continue clicked")
            time.sleep(5)
            if WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[4]/main/div[4]/div/div/form/fieldset/ol/fieldset/div/div[2]/div[2]/small",
                    )
                )
            ):
                logging.info("No Dates are available as system is too busy")
                driver.quit()
            else:
                logging.info("Wohooo....Appointment Dates are available")
                # Make an API call to check for data
                # api_url = os.getenv("appointment_url")
                SCHEDULE_ID = os.getenv("SCHEDULE_ID")
                FACILITY_ID = os.getenv("FACILITY_ID")
                api_url = f"https://ais.usvisa-info.com/en-ca/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
                response = requests.get(api_url)

                if response.status_code == 200:
                    data = response.json()
                    if data:  # Check if the response contains data
                        logging.info("API returned data:" + str(data))
                    else:
                        logging.info("API returned no data")
                else:
                    logging.info(
                        f"API call failed with status code: {response.status_code}"
                    )
                driver.quit()
            logging.info("Process exited...")
        except Exception as e:
            logging.error(f"Error in inner try block: {str(e)}", exc_info=True)
            driver.quit()
    except Exception as err:
        logging.error(f"Error in check Appointment function: {str(err)}", exc_info=True)
        if "driver" in globals():
            driver.quit()


if __name__ == "__main__":
    try:
        # Get the current date
        now = datetime.now()
        date_obj = datetime.strftime(now, "%d-%b-%Y")
        Today_date = datetime.strptime(date_obj, "%d-%b-%Y").date()
        urllib3.disable_warnings()
        filedate = str(Today_date)

        # Define the file path
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_path = os.path.join(log_dir, f"Visa_Automation_{filedate}.log")

        # Basic Configuration for Logging
        logging.basicConfig(
            filename=file_path,
            format="%(asctime)s ~ %(levelname)s - %(message)s",
            datefmt="%d-%b-%Y %H:%M:%S",
            level=logging.INFO,
        )

        # Also log to console when running in GitHub Actions
        if os.getenv("GITHUB_ACTIONS") == "true":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter("%(asctime)s ~ %(levelname)s - %(message)s")
            )
            logging.getLogger().addHandler(console_handler)

        logging.info("VISA Automation process started ...")
        url = os.getenv("URL")
        visa_appointment_check(url)

    except Exception as e:
        logging.error(f"Error occurred in main function: {str(e)}", exc_info=True)
        raise  # Re-raise the exception to mark the GitHub Action as failed
