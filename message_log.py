from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import exceptions
from fake_useragent import UserAgent
from time import sleep
import json
import os
import re
import random
from discord_bot import driver_set_up_login,navigate_to_mention_thread,get_message_tag_name,get_original_tag_name,get_original_poster_tag_name
from database_manager import DiscordDatabaseManager
from mysql.connector import Error
from datetime import datetime

def navigate_to_unread_thread(driver):
    is_read = False
    is_jump_button_clicked = False
    message_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))  )
    try:
        thread_unread = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='button'][contains(@aria-label,'unread') or contains(@aria-label,'未讀')]")))
        print(thread_unread.text)
        
        thread_unread.click()  
        is_read =True
        is_jump_button_clicked = True 
    except Exception:
        is_read = False
        is_jump_button_clicked = True
        pass
    if is_jump_button_clicked:
        try:
            jump_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'barButtonAlt_cf58b5') and contains(@class,'barButtonBase_cf58b5')]")))
            jump_button.click()
            sleep(3)
        except Exception:
            is_jump_button_clicked = False
            pass
    if is_read:
        try:
            message_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))  )
            print("change thread")
            # message_input.send_keys("I am COMING !")
            # message_input.send_keys(Keys.RETURN)
        except Exception:
            pass
    else:
        pass       




def is_user_cooldown(user_id):
    db = DiscordDatabaseManager()
    current_updated_time = db.get_user_updated_time(user_id)
    if current_updated_time is True:
        return True
    updated_time = datetime.strptime(str(current_updated_time), "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    time_difference = now - updated_time
    print(f"time difference :{time_difference.seconds}")
    if time_difference.seconds<30:
        return True
    else:
        return False

def user_level_up(user_id):
    
    db = DiscordDatabaseManager()
    current_exp, current_level = db.get_user_current_exp_level(user_id)
    print(f"current exp : {current_exp}")
    print(f"current level : {current_level}")
    if current_level < 15 :
        threshold = 600
    elif current_level >= 15 and current_level < 30:
        threshold = 900
    elif current_level >= 30 and current_level <45:
        threshold = 1200
    elif current_level >=45 and current_level < 60:
        threshold = 1500
    db.update_user_current_gain_exp(user_id)
    gain_exp = db.get_user_current_gain_exp(user_id)
    
    if (current_exp + gain_exp) >= threshold:
        print("level+1")
        reamin_exp = (current_exp + gain_exp) - threshold
        print(reamin_exp)
        db.update_user_level(user_id,reamin_exp)
    else:
        print(f"exp+{gain_exp}")
        db.update_user_exp(gain_exp,user_id)



def main():
    # Set up WebDriver
    email = os.getenv("message_email")
    password =os.getenv("password")
    db = DiscordDatabaseManager()
    driver = driver_set_up_login(email,password)
    
    try:
        
        try:
            thread = WebDriverWait(driver, 100).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='button'][contains(@aria-label, 'LE SSERAFIM')]")))
            thread.click()
            jump_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'barButtonAlt_cf58b5')]")))
            jump_button.click()
        except Exception:
            pass
        
        
        while True:
            navigate_to_unread_thread(driver)
            sleep(1)
            message_content = ""
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']"))
            )
            thread_element = WebDriverWait(driver,3).until(
                EC.presence_of_element_located((By.XPATH,"//h2[@class='defaultColor_a595eb heading-md/semibold_dc00ef defaultColor_e9e35f title_fc4f04']"))
            )
            full_text = thread_element.text
            thread_name = full_text.split(":")[-1].strip()
            print(thread_name)
            try:
                message = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]//div[contains(@class,'messageContent') and not(contains(@class,'repliedTextContent'))]"))
                )
                serial_number = message.get_attribute("id")[16:]
                message_text = message.text
                
                print(message_text)
                if message_text == "@不畏懼 忠誠 !":
                    try:
                        db.set_thread_is_mentioned(thread_name)
                        
                        print(f"set {thread_name} mentioned")
                    except Error as e:
                        print(f"{thread_name} set metioned error : {e}")
                    
                

            except exceptions.TimeoutException or exceptions.NoSuchElementException:
                print("can not find simple message")
                continue

            try:
                message_emoji = message.find_element(By.XPATH,".//img[@data-type='emoji']")
                emoji = message_emoji.get_attribute('alt')
                print(emoji)
                
            except exceptions.NoSuchElementException:
                print("can not locate emoji element")
                emoji = ""
            try:
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    poster_serial_number,user_tag_name = get_original_poster_tag_name(driver)
                print(user_tag_name)
                print(poster_serial_number)
                
            except Exception:
                print("failed to get user tag name")
                username = "username"
                continue
           
            try:
                username_element = message.find_element(By.XPATH, f"//*[@id='message-username-{serial_number}']")
                username = username_element.text
                
            except (exceptions.NoSuchElementException,exceptions.StaleElementReferenceException) as e:
                try:
                    username_element = message.find_element(By.XPATH, f"//*[@id='message-username-{poster_serial_number}']")
                    username = username_element.text
                    print(username)
                except exceptions.NoSuchElementException as e:
                    print("no such username element, pass")
                    username = "username"
                    
                except exceptions.StaleElementReferenceException as e:
                    print(f"stale username element error {e}, continue")
                    username = "username"
                    pass
                
            
            
            user_record_exists = db.check_record_exists("user","user_id",user_tag_name)
            message_record_exists = db.check_record_exists("message_log","serial_number",serial_number)
            user_cooldown = is_user_cooldown(user_tag_name)
           
            if not user_record_exists:
                try:
                    db.log_user_info(user_tag_name,username)
                    
                except Error as e:   
                    print(f"db execute log user error : {e}")
                    continue
            else:
                try:
                    if username != "user":
                        db.update_user_info(user_tag_name,username)
                except Error as e:
                    print(f"db execute update user error : {e}") 
            if not message_record_exists:
                try:
                    if message_text != "":
                       db.log_message_history(user_tag_name,thread_name,message_text,None,serial_number)
                    elif emoji != "":
                        db.log_message_history(user_tag_name,thread_name,None,emoji,serial_number)
                    else:
                        db.log_message_history(user_tag_name,thread_name,None,None,serial_number)
                except Error as e:
                    print(f"db execute log message history error : {e}")
                    continue
            try:
                if not user_cooldown and not message_record_exists :
                    print("user level up")
                    print(user_tag_name)
                    user_level_up(user_tag_name)
                else:
                    print("user is cool down now")
                    pass
            except exceptions as e:
                print(f"level up error : {e}")
            
            sleep(1)  # Wait before checking for new messages

    except KeyboardInterrupt:
        print("Script interrupted by user.")
        driver.quit()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("interrupt")
        
        driver.quit()


        

if __name__ == "__main__":
    main()