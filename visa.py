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
        time.sleep(2)

    except Exception as e:
        logging.error(f"Error in Chrome initialization: {str(e)}", exc_info=True)
        raise


# Check URL Status
def visa_appointment_check(url):
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
            driver.find_element(By.ID, "user_email").send_keys(os.getenv("EMAIL"))
            time.sleep(2)
            logging.info("Email enetered")
            driver.find_element(By.ID, "user_password").send_keys(os.getenv("PASSWORD"))
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
            available_dates = []
            if WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[4]/main/div[4]/div/div/form/fieldset/ol/fieldset/div/div[2]/div[2]/small",
                    )
                )
            ):
                if send_email_notification(available_dates):
                    logging.info("Email notification sent successfully")
                else:
                    logging.warning("Failed to send email notification")
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
                        for date in data:
                            available_dates.append(date)
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


def send_email_notification(available_dates):
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
            "WooHoo...Visa Appointment Dates Available!"
            if len(available_dates)
            else "No Visa Appointment Dates Available"
        )

        # Create email body
        body = "The following visa appointment dates are available:\n\n"
        for date in available_dates:
            body += f"- {date['date']}\n"
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
            visa_appointment_check(url)
            logging.info("Visa appointment check completed successfully")
        except Exception as e:
            logging.error(f"Error in visa_appointment_check: {str(e)}", exc_info=True)
            raise

    except Exception as e:
        logging.error(f"Fatal error in main function: {str(e)}", exc_info=True)
        raise
    finally:
        logging.info("=== Script Execution Completed ===")
