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
import re
from datetime import datetime, timedelta
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# warning handling before /on sending the post request
warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_filename = f"logs/visa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
os.makedirs("logs", exist_ok=True)

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
        logging.FileHandler(log_filename),  # Log to file
    ],
)

# Add a startup message
logging.info("=== Visa Appointment Check Script Started ===")
logging.info(f"Log file: {log_filename}")

faculties = [
    {"faculty": "Calgary", "faculty_id": "89"},
    {"faculty": "Halifax", "faculty_id": "90"},
    {"faculty": "Montreal", "faculty_id": "91"},
    {"faculty": "Ottawa", "faculty_id": "92"},
    {"faculty": "Quebec", "faculty_id": "93"},
    {"faculty": "Toronto", "faculty_id": "94"},
    {"faculty": "Vancouver", "faculty_id": "95"},
]


# extract dates from ui
def extract_dates(sentence):
    """
    Extracts dates from a sentence and converts them to yyyy-mm-dd format.

    :param sentence: The input sentence containing dates.
    :return: A list of dates in yyyy-mm-dd format.
    """
    # Regex patterns for different date formats
    patterns = [
        r"\d{1,2} [A-Za-z]+, \d{4}",  # Matches dates like '24 February, 2026'
        r"\d{4}-\d{2}-\d{2}",  # Matches dates like '2026-07-14'
    ]

    dates = []

    for pattern in patterns:
        matches = re.findall(pattern, sentence)
        for match in matches:
            try:
                # Convert to datetime and then to yyyy-mm-dd format
                if "," in match:  # Handle '24 February, 2026'
                    dt = datetime.strptime(match, "%d %B, %Y")
                else:  # Handle '2026-07-14'
                    dt = datetime.strptime(match, "%Y-%m-%d")
                dates.append(dt.strftime("%Y-%m-%d"))
            except ValueError:
                pass  # Skip invalid matches

    return dates


def is_available_date_before(current_appointment_date, available_date):
    """
    Checks if the available date is before the current_appointment date.

    :param current_appointment_date: The current_appointment date in yyyy-mm-dd format.
    :param available_date: The available date in yyyy-mm-dd format.
    :return: True if the available date is before the current_appointment date, False otherwise.
    """
    # Parse the dates
    current_appointment_date_obj = datetime.strptime(
        current_appointment_date, "%Y-%m-%d"
    )
    available_date_obj = datetime.strptime(available_date, "%Y-%m-%d")

    # Compare the dates
    return available_date_obj < current_appointment_date_obj


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

        # Common options for both environments
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        chrome_options.page_load_strategy = "normal"

        # GitHub Actions specific options
        if os.getenv("GITHUB_ACTIONS") == "true":
            logging.info("Setting up Chrome for GitHub Actions (headless)...")
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("Chrome driver started in GitHub Actions environment")
        else:
            logging.info("Setting up Chrome for local environment (headed)...")
            service = Service(
                r"/Users/rahuljassal/Downloads/chromedriver-mac-arm64/chromedriver"
            )
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info("Chrome driver started in local environment")

        # Add additional wait for page load
        driver.implicitly_wait(10)
        # #time.sleep(2)

    except Exception as e:
        logging.error(f"Error in Chrome initialization: {str(e)}", exc_info=True)
        raise


# Check URL Status
def visa_appointment_check(url, email, password, schedule_id, facility_id):
    try:
        if not url:
            logging.error(
                "URL is empty or None. Please check your environment variables."
            )
            return

        logging.info(f"Attempting to access URL: {url}")
        chrome()

        try:
            driver.get(url)
            driver.maximize_window()
            logging.info("Opened Url...")
            # Accept cookies if present
            try:
                cookie_button = WebDriverWait(url, 5).until(
                    EC.presence_of_element_located((By.ID, "accept-cookies"))
                )
                # #time.sleep(2)
                cookie_button.click()
                logging.info("cookie button clicked")
            except:
                pass
            # Click sign in
            sign_in = driver.find_element(By.LINK_TEXT, "Sign In")
            # time.sleep(2)
            sign_in.click()
            logging.info("Sign In Button Clicked")

            # Fill login form
            driver.find_element(By.ID, "user_email").send_keys(email)

            # time.sleep(2)
            logging.info("Email enetered")
            driver.find_element(By.ID, "user_password").send_keys(password)

            # time.sleep(2)
            logging.info("Password entered")
            driver.find_element(
                By.XPATH,
                "/html/body/div[5]/main/div[3]/div/div[1]/div/form/div[3]/label/div",
            ).click()
            # time.sleep(2)
            logging.info("Checkbox ticked")
            driver.find_element(By.NAME, "commit").click()
            # time.sleep(2)
            logging.info("Sign In Button Clicked")
            current_appointment = driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div[1]/div/div/div[2]/p[1]",
            ).text
            current_appointment_dates = extract_dates(current_appointment)
            logging.info(f"Current appointment date {current_appointment_dates}")

            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div[1]/div/div/div[1]/div[2]/ul/li",
            ).click()
            logging.info("Continue clicked")
            # time.sleep(5)
            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div/section/ul/li[4]/a/h5",
            ).click()
            # time.sleep(2)
            logging.info("Reschedule app 1 clicked")
            driver.find_element(
                By.XPATH,
                "/html/body/div[4]/main/div[2]/div[2]/div/section/ul/li[4]/div/div/div[2]/p[2]/a",
            ).click()
            logging.info("Reschedule app 2 clicked")
            time.sleep(2)
            # driver.find_element(
            #     By.XPATH, "/html/body/div[4]/main/div[3]/form/div[2]/div/input"
            # ).click()
            # logging.info("Continue clicked")
            time.sleep(5)
            available_dates = []
            # Make an API call to check for data
            URL = os.getenv("URL")
            URL = f"{URL}/schedule/{schedule_id}/appointment/days/{facility_id}.json?appointments[expedite]=false"
            # Get cookies from selenium session
            cookies = driver.get_cookies()
            cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

            # Create headers similar to browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": url,
            }

            # Make request with cookies and headers
            response = requests.get(
                URL,
                cookies=cookie_dict,
                headers=headers,
                verify=False,  # Since you're already ignoring SSL
            )

            if response.status_code == 200:
                data = response.json()
                if data:  # Check if the response contains data
                    logging.info("API returned data:" + str(data))
                    for date in data:
                        available_dates.append(date["date"])
                else:
                    logging.info(f"{facility_id}-API returned no data ")
            else:
                logging.info(
                    f"API call failed with status code: {response.status_code}"
                )
            if len(available_dates):
                early_date_flag = is_available_date_before(
                    current_appointment_dates[0], available_dates[0]
                )
                if early_date_flag:
                    if send_email_notification(available_dates, email):
                        logging.info("Entering the email function")
                    else:
                        logging.warning("Failed to send email notification")
                else:
                    logging.info(
                        f"for {email} current date: {current_appointment_dates[0]}, earliest date available: { available_dates[0]}"
                    )
                    logging.info(
                        "Early dates are not available, will try again after 15 mins"
                    )
            else:
                logging.info("No Dates Available")
            driver.quit()
        except Exception as e:
            logging.error(f"Error in inner try block: {str(e)}", exc_info=True)
            driver.quit()

        logging.info("Process exited...")

    except Exception as e:
        logging.error(f"Error in inner try block: {str(e)}", exc_info=True)
        driver.quit()


def send_email_notification(available_dates, email):
    """Send email notification about available visa appointment dates."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Parse multiple email addresses from environment variable
    try:
        notification_emails = eval(os.getenv("NOTIFICATION_EMAIL", "[]"))
        if isinstance(notification_emails, str):
            notification_emails = [notification_emails]
    except:
        logging.error(
            "Failed to parse NOTIFICATION_EMAIL. It should be a list of emails."
        )
        return False

    if not all([smtp_server, smtp_username, smtp_password, notification_emails]):
        logging.error("Missing email configuration environment variables")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = ", ".join(notification_emails)  # Join all emails with comma
        msg["Subject"] = (
            f"{email} ||  WooHoo...Visa Appointment Dates Available!"
            if len(available_dates)
            else "No Visa Appointment Dates Available"
        )

        # Create email body
        body = "The following visa appointment dates are available:\n\n"
        for date in available_dates:
            body += f"{date}\n"
        body += "\nPlease check the visa appointment system to book your slot."

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            # Send to all recipients
            server.send_message(msg)

        logging.info(f"Email notification sent to: {', '.join(notification_emails)}")
        return True

    except Exception as e:
        logging.error(f"Failed to send email notification: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        # Log system information
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Current working directory: {os.getcwd()}")

        # Check if .env file exists
        logging.info("Checking .env file...")
        if os.path.exists(".env"):
            logging.info(".env file found")
        else:
            logging.warning(".env file not found")

        # Add debug logging for environment variables
        logging.info("Checking environment variables:")
        env_vars = ["URL", "EMAIL", "PASSWORD", "SCHEDULE_ID", "FACILITY_ID"]
        missing_vars = []

        for var in env_vars:
            value = os.getenv(var)
            if value:
                logging.info(f"{var}: Set (length: {len(value)} characters)")
            else:
                logging.error(f"{var}: Not set")
                missing_vars.append(var)

        if missing_vars:
            logging.error(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            sys.exit(1)

        url = os.getenv("URL")
        logging.info("Starting visa appointment check...")

        try:

            def stringToArrayConverter(string):
                return string.strip("[]").split(",")

            EMAIL = stringToArrayConverter(os.getenv("EMAIL", "[]"))
            SCHEDULE_ID = stringToArrayConverter(os.getenv("SCHEDULE_ID", "[]"))
            FACILITY_ID = stringToArrayConverter(os.getenv("FACILITY_ID", "[]"))
            PASSWORD = stringToArrayConverter(os.getenv("PASSWORD", "[]"))
            for i in range(0, len(PASSWORD)):

                visa_appointment_check(
                    url, EMAIL[i], PASSWORD[i], SCHEDULE_ID[i], FACILITY_ID[i]
                )
                logging.info(
                    f"Visa appointment check for {EMAIL[i]} completed successfully"
                )
        except Exception as e:
            logging.error(f"Error in visa_appointment_check: {str(e)}", exc_info=True)
            raise

    except Exception as e:
        logging.error(f"Fatal error in main function: {str(e)}", exc_info=True)
        raise
    finally:
        logging.info("=== Script Execution Completed ===")
