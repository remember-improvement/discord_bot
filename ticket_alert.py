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

# === LINE Configuration ===
LINE_CHANNEL_ACCESS_TOKEN = 'l09zpnbCZyj2cHTJkT5wrjKr8FZr1h4KwvZO5bdHoPattnXdmOZ2xX1nUYdgNwecFueunvbVzVxhksxpaQZn3JflS5fnB+c3xgzyyHlRieXzXlA6+gAyevlme9nKfaTu+b6AuykRZy+81Llya/FfzAdB04t89/1O/w1cDnyilFU='
GROUP_ID = 'Cb0f4a778a61d4d93e0f82b2f1fefbec0'
LINE_PUSH_API = 'https://api.line.me/v2/bot/message/push'

# === Booking Constants ===
URL = 'https://reservation.pc.gc.ca/create-booking/results?mapId=-2147483328&searchTabGroupId=3&bookingCategoryId=10&_gl=1*1kd0kf4*_ga*MTIxODQ3ODc3MC4xNzQ0NjE1MDc2*_ga_PC690N3X7Z*MTc0NDYxNTA3Ni4xLjEuMTc0NDYxNTE4OC4wLjAuMA..&_ga=2.10881524.1308959875.1744615076-1218478770.1744615076&startDate=2025-10-05&endDate=2025-10-06&nights=1&isReserving=true&peopleCapacityCategoryCounts=%5B%5B-32767,null,1,null%5D%5D&searchTime=2025-05-11T07:51:46.166&flexibleSearch=%5Bfalse,false,null,1%5D&resourceLocationId=-2147483536&filterData=%7B%7D'
# UNAVAILABLE_TEXT = "LL: 6:30am-7am Departures Unavailable "
UNAVAILABLE_TEXT = "8:30 a.m. Bus Unavailable"
UNOPERATING_TEXT = "8:30 a.m. Bus Not Operating"

# === Send LINE Message ===
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

# === Check Availability ===
def check_ticket_availability():
    chrome_options = Options()
    user_agent=UserAgent.chrome
    # user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")  # For handling resource issues
    chrome_options.add_argument("--no-sandbox")  # For running in certain environments
    chrome_options.add_argument("--lang=en-us")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_prefs = {"intl.accept_languages": "en-US"}
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "disk-cache-size": 0
    })
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
        })


    try:
        driver.get(URL)

        # Wait for UI to stabilize
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "message-text"))
            )
        except TimeoutException:
            pass

        try:
            search_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "actionSearch"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
            sleep(0.5)
            driver.execute_script("arguments[0].click();", search_btn)
        except TimeoutException:
            print("Search button timeout.")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "td[aria-label*='8:30 a.m. Bus Unavailable']"))
            )
        except TimeoutException:
            print("Aria label timeout.")
        sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # elements = soup.select(
        #     'td.chart-cell.chart-cell--even.chart-cell--unavailable.ng-star-inserted[aria-label]'
        # )
        cells = driver.find_elements(By.CSS_SELECTOR, "td[aria-label*='8:30 a.m. Bus Unavailable']")
        for cell in cells:
            aria = cell.get_attribute("aria-label")
            print("Found slot:", aria)
            if "Available" in aria and UNAVAILABLE_TEXT not in aria and UNOPERATING_TEXT not in aria:
                print(f"🚨 Found Available: {aria}")
                send_line_message(GROUP_ID, f"🚨 Available: {aria}\n{URL}")
                return

        print("No tickets at 8:30 a.m.")

    finally:
        driver.quit()
        # os.system("taskkill /im chrome.exe /f >nul 2>&1")  # Force close zombie Chrome
        os.system("taskkill /im chromedriver.exe /f >nul 2>&1")

# === Schedule Task ===
if __name__ == "__main__":
    schedule.every(15).seconds.do(check_ticket_availability)
    while True:
        schedule.run_pending()
        sleep(1)
