from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import schedule
import os
from time import sleep
import os
import signal
import psutil
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
load_dotenv()
# === LINE Configuration ===
GROUP_ID = os.getenv("group_id")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("line_channel_access_token")
LINE_PUSH_API = 'https://api.line.me/v2/bot/message/push'

# === Booking Constants ===
URL = 'https://reservation.pc.gc.ca/create-booking/results?mapId=-2147483328&searchTabGroupId=3&bookingCategoryId=10&_gl=1*1kd0kf4*_ga*MTIxODQ3ODc3MC4xNzQ0NjE1MDc2*_ga_PC690N3X7Z*MTc0NDYxNTA3Ni4xLjEuMTc0NDYxNTE4OC4wLjAuMA..&_ga=2.10881524.1308959875.1744615076-1218478770.1744615076&startDate=2025-10-05&endDate=2025-10-06&nights=1&isReserving=true&peopleCapacityCategoryCounts=%5B%5B-32767,null,1,null%5D%5D&searchTime=2025-05-11T07:51:46.166&flexibleSearch=%5Bfalse,false,null,1%5D&resourceLocationId=-2147483536&filterData=%7B%7D'
# UNAVAILABLE_TEXT = "LL: 6:30am-7am Departures Unavailable "
UNAVAILABLE_TEXT = "8:30 a.m. Bus Unavailable"
UNOPERATING_TEXT = "8:30 a.m. Bus Not Operating"


def send_line_message(group_id, text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    payload = {
        "to": group_id,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(LINE_PUSH_API, headers=headers, json=payload)

def create_driver():
    chrome_options = Options()
    user_agent = UserAgent().chrome
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--remote-debugging-port=9222")
    prefs = {
        "download.default_directory": "/path/to/download/directory",
        "profile.managed_default_content_settings.images": 2,
        "disk-cache-size": 0
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()
    return driver

def check_ticket_availability(driver):


    try:
        driver.get(URL)
        driver.refresh()
        try:
            search_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "actionSearch"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
            sleep(0.5)
            driver.execute_script("arguments[0].click();", search_btn)
        except TimeoutError:
            print("search button time out")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td[aria-label*='8:30 a.m. Bus Unavailable']"))
        )
        sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cells = driver.find_elements(By.CSS_SELECTOR, "td[aria-label*='8:30 a.m. Bus Unavailable']")
        for cell in cells:
            aria = cell.get_attribute("aria-label")
            if "Available" in aria and UNAVAILABLE_TEXT not in aria and UNOPERATING_TEXT not in aria:
                send_line_message(GROUP_ID, f"🚨 Available: {aria}\n{URL}")
                return
        print("No tickets at 8:30 a.m.")
    except TimeoutException:
        print("Timeout occurred.")
    finally:
        # driver.quit()
        # kill_chromedriver()
        now = datetime.now()
        print("Execute Time =", now.strftime("%Y-%m-%d %H:%M:%S"))


def kill_chromedriver():
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'chromedriver':
            try:
                os.kill(process.info['pid'], signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating chromedriver process: {e}")

if __name__ == "__main__":
    
    try:
        while True:
            driver = create_driver()
            check_ticket_availability(driver)
            sleep(15)
            driver.quit()
            kill_chromedriver()
    except KeyboardInterrupt:
        print("Process interrupted.")
    finally:
        driver.quit()
        print("Driver closed.")
