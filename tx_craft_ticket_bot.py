import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import time
import os

# Set up user profile
user_data_dir = os.path.expanduser("C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data")  # Change as needed
profile = "Default"

options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument(f"--profile-directory={profile}")
options.add_argument("--start-maximized")

# Launch Chrome using undetected-chromedriver
driver = uc.Chrome(options=options)

# Go to the page
concert_id = "25_lsf"
url = f"https://tixcraft.com/activity/detail/{concert_id}"
driver.get(url)
time.sleep(10)
# Refresh until "立即購票" shows up
while True:
    try:
        print("Refreshing...")
        driver.refresh()
        time.sleep(0.1)
        buy_link = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.buy a'))
        )
        buy_link.click()
        print("Clicked buy link.")
        
    
        find_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'button.btn.btn-primary[data-href*="{concert_id}"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", find_button)
        time.sleep(0.5)  # wait a bit for scrolling animation

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'button.btn.btn-primary[data-href*="{concert_id}"]'))
        ).click()
        print("Clicked 'Find tickets'")
        break
    
    except Exception as e:
        print("Still waiting for buy link...")
        continue
    except KeyboardInterrupt:
        print("🛑 Stopping script manually (Ctrl+C)")
        driver.quit()
        break

# Wait for the Find Tickets button
    
while True:
    try:
        # Your fixed checkCode
        checkcode_value = "LF101507984"  # ← Replace with your actual membership-based code

    # Wait until the input is present
        checkcode_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "checkCode"))
        )

    # Fill the code
        checkcode_input.clear()
        checkcode_input.send_keys(checkcode_value)
        print("✅ Filled checkCode input")

        # Wait for the submit button
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and contains(text(), "Submit")]'))
        )
        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
        submit_button.click()
        print("🚀 Form submitted")
        break
    except KeyboardInterrupt:
        print("🛑 Stopping script manually (Ctrl+C)")
        driver.quit()
        break
    except:
        print("failed to submit")
        continue
    

zone = "藍4B-1"
xpath = f'//li[.//font[contains(text(), "{zone}") and not(contains(text(), "Sold out"))]]'
while True:
    try:
        seat = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable(
        (By.XPATH, f'//a[contains(text(), "{zone}") and .//font[contains(text(), "Available")]]')
         )
        )
        seat.click()
        print(f"✅ Clicked available seat in {zone}")
        # available_zone = driver.find_element(By.XPATH, xpath)
        # driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", available_zone)
        # time.sleep(0.5)  # wait a bit for scrolling animation
        # print(f"✅ {zone} is available!")
        # available_zone.click()  # if it's clickable
        break
    except KeyboardInterrupt:
        print("🛑 Stopping script manually (Ctrl+C)")
        driver.quit()
        break
    except:
        print(f"❌ {zone} is sold out or not found")
        continue



while True:
    try:
        select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//select[starts-with(@id, "TicketForm_ticketPrice")]'))
    )

        # Wrap in Select and pick value "2"
        dropdown = Select(select_element)
        dropdown.select_by_value("2")

        print("✅ Selected value 2 from dynamic select element")
        break
    except KeyboardInterrupt:
        print("🛑 Stopping script manually (Ctrl+C)")
        driver.quit()
        break
    except:
        print(f"❌ Selected value 2 not found")
        continue
while True:
    try:
        checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "TicketForm_agree"))
        )
        if not checkbox.is_selected():
            checkbox.click()
            print("✅ Checked the 'Agree' box.")
            break
        else:
            print("☑️ Already checked.")
    except KeyboardInterrupt:
        print("🛑 Stopping script manually (Ctrl+C)")
        driver.quit()
        break
    except Exception as e:
        print("❌ Could not find or check the 'Agree' checkbox:", e)
        continue

input("Press Enter to quit...")
driver.quit()
