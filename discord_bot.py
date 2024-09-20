from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from time import sleep
import json
import os
import re
import random
from food_recommend import get_coordinates, recommend
from spotify_bot import get_random_popular_track
import mysql.connector
from mysql.connector import Error
from selenium.common import exceptions
from database_manager import DiscordDatabaseManager
from datetime import datetime,timedelta
from dotenv import load_dotenv
load_dotenv()


def genearate_text_image(fortune_level,thread):
    text_path = 'fortune_config.json'

    # Open the file and load the data
    with open(text_path, 'r', encoding='utf-8') as file:
        fortune = json.load(file)
    fortune_text = fortune[fortune_level]
    thread_list=["aespa", "LE SSERAFIM", "Cosmic Girls", "ITZY", "NMIXX", "IVE-「真」好DIVE的窩", "SSS.jpg交易串", "(G)I-DLE","STAYC","BABYMONSTER","RESCENE","鐵豚"]
    
    if thread not in thread_list:
        default_image_directory = "idol_image"
        default_files = os.listdir(default_image_directory)
        default_files = [file for file in default_files if os.path.isfile(os.path.join(default_image_directory, file))]
        random.shuffle(default_files)
        image_path = os.path.join(default_image_directory, default_files.pop())
         
    else:
        image_directory = f"idol_image/{thread}"
        files = os.listdir(image_directory)
        files = [file for file in files if os.path.isfile(os.path.join(image_directory, file))]
        random.shuffle(files)
        image_path = os.path.join(image_directory, files.pop())
    
    # print(fortune_text)
    print(image_path)
    
    return fortune_text, image_path

def navigate_to_mention_thread(driver,thread):
    is_mentiond = False
    is_jump_button_clicked = False
    message_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))  )
    try:
        thread_mention = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, f"//div[@role='button'][contains(@aria-label,' mention') or contains(@aria-label,' 則提及') and contains(@aria-label,'{thread}')]")))
        print(thread_mention.text)
        #message_input.send_keys(f"前往 {thread_mention.text} 中 ...")
        #message_input.send_keys(Keys.RETURN)
        thread_mention.click()  
        is_mentiond =True
        is_jump_button_clicked = True 
    except Exception:
        is_mentiond = False
        is_jump_button_clicked = True
        pass
    if is_jump_button_clicked:
        try:
            jump_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'barButtonAlt_cf58b5') and contains(@class,'barButtonBase_cf58b5')]")))
            jump_button.click()
        except Exception:
            is_jump_button_clicked = False
            pass
    if is_mentiond:
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
    


def fortune_teller(driver, message, message_input):
    db = DiscordDatabaseManager()
    serial_number = message.get_attribute("id")[16:]
    
    
    
    try:
        user_tag_name = get_message_tag_name(driver,message)
        if user_tag_name is None:
            serial_number, user_tag_name = get_original_poster_tag_name(driver)
        print(user_tag_name)
        username_element = message.find_element(By.XPATH, f"//*[@id='message-username-{serial_number}']")
        username = username_element.text
    except Exception:
        username = "Hi" 
    fortune_level = ["大吉", "中吉", "吉", "小凶", "大凶"]
    level = random.choice(fortune_level)
    user_record_exists = db.check_record_exists("user","user_id",user_tag_name)
    if not user_record_exists:
        try:
            db.log_user_info(user_tag_name,username)
        except Error as e:
            print(f"db execute log user error : {e}")
            sleep(1)
    try:
        db.log_fortune_history(user_tag_name,level)
    except Error as e:
        print(f"db execute log fortune error : {e}")
    latest_created_time = db.get_latest_fortune_log_created_time(user_tag_name)
    created_time = datetime.strptime(str(latest_created_time), "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    cooldown_time = now - created_time
    try:
        results = db.get_most_message_thread(user_tag_name,5)
        threads = [row[0] for row in results]  # Thread names
        weights = [row[1] for row in results]  # Message counts as weights
        thread = random.choices(threads, weights=weights, k=1)[0]
        print(thread)
    except Error as e:
        print(f"db execute get most message error : {e}")
    try:
        fortune_text, image_path = genearate_text_image(level,thread)
    except FileNotFoundError:
        print("image not found")

    try:
        results = db.get_fortune_level_count(user_tag_name)
        fortune_trend = ""
        for fortune in results:
            fortune_trend+=f"{fortune[0]} : {fortune[1]} "
    except Error as e:
        print(f"db execute error : {e}")
    try:
        relative_path = image_path
        absolute_path = os.path.abspath(relative_path)
        upload_element = driver.find_element(By.XPATH, "//input[@class='file-input' and @type='file']")   
        upload_element.send_keys(absolute_path)
        sleep(2)
        try:
            message_input.send_keys(f" @{user_tag_name} 今天的運勢為 : {level}   {fortune_text}")
            message_input.send_keys(Keys.SHIFT,Keys.RETURN)
            message_input.send_keys(f"目前運勢累計 {fortune_trend} ")
            message_input.send_keys(Keys.SHIFT,Keys.RETURN)
            message_input.send_keys(f"目前CD時間 : {str(cooldown_time)} ")
        except Exception:
            message_input.send_keys(f" Hi 今天的運勢為 : {level}   {fortune_text}")
        finally:
            message_input.send_keys(Keys.RETURN)
        
        sleep(1)
    except Exception as e:
        print(f"Error interacting with message options: {e}")


def random_pick_one(message_text,):
    try:
        option_list = message_text.split()
        options = option_list[1:]
        pick_option = random.choice(options)
    except Exception:
        pick_option = "怪怪的 有問題"
    return pick_option
def get_message_tag_name(driver,message):
    serial_number = message.get_attribute("id")[16:]
    print(serial_number)
    try:
        username_element = WebDriverWait(message, 2).until(
            EC.presence_of_element_located((By.XPATH, f"//*[@id='message-username-{serial_number}']")))
        username_element.click()
    except exceptions.TimeoutException or Exception or exceptions.NoSuchElementException:
        print("error when get username element")
    try:
        user_tag_name_element = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.XPATH,"//span[@class='userTagUsername_c32acf']")))
        user_tag_name = user_tag_name_element.text
    except exceptions.TimeoutException or Exception or exceptions.NoSuchElementException:
        print("error when get user tag name element ")
        user_tag_name = None
    finally:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
    return user_tag_name


def get_original_poster_tag_name(driver):
    pre=1
    user_tag_name = None
    current_message = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]")))
    while user_tag_name is None:
        previous_message = current_message.find_element(By.XPATH, f"preceding-sibling::li[{pre}]")
        previous_message_content = previous_message.find_element(By.XPATH, ".//div[contains(@class,'messageContent') and not(contains(@class,'repliedTextContent'))]")
        user_tag_name = get_message_tag_name(driver,previous_message_content)
        serial_number = previous_message_content.get_attribute("id")[16:]
        print(user_tag_name)
        print(pre)
        pre+=1
    return serial_number,user_tag_name

def get_user_tag_name(driver,message):
    serial_number = message.get_attribute("id")[16:]
    print(serial_number)
    try:
        username_element = WebDriverWait(message, 2).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@id='message-reply-context-{serial_number}']//span[contains(@class, 'username_f9f2ca')]")))
        
        username_element.click()
        
        
    except exceptions.TimeoutException or Exception:
            
        try:
            username_element = WebDriverWait(message, 2).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@id='message-username-{serial_number}']")))
            username_element.click()
        except exceptions.TimeoutException or Exception:
            print("error when get username element")
            # user_tag_name = None
            # user_tag_name = "hi 你好"

    try:
        user_tag_name_element = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.XPATH,"//span[@class='userTagUsername_c32acf']")))
        user_tag_name = user_tag_name_element.text
    except exceptions.TimeoutException or Exception:
        print("error when get user tag name element ")
        
        user_tag_name = None
    finally:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
    return user_tag_name



def get_recommend_restaurant(address):
    api_key = os.getenv("api-key")
    try:
        latitude, longitude = get_coordinates(address, api_key)
    except Exception as e:
        recommend_restaurant = "都可以 隨便 我沒差"
        return recommend_restaurant,None
    try:
        restaurant_list, address_dict = recommend(longitude,latitude)
        print(restaurant_list)
        print(address_dict)
        
    except Exception as e:
        print("get restaurant_list : " +e )
    if len(restaurant_list) < 1:
        recommend_restaurant = "老麥"
        return recommend_restaurant,None
    else:
        recommend_restaurant = random.choice(restaurant_list)
        print(address_dict[recommend_restaurant])
        return recommend_restaurant, address_dict[recommend_restaurant]


def get_recommend_track(user_id):
    db = DiscordDatabaseManager()
    results = db.get_most_message_thread(user_id,5)
    threads = [row[0] for row in results]  # Thread names
    weights = [row[1] for row in results]  # Message counts as weights
    artist = random.choice(threads)
    print(artist)
    if artist == "IVE-「真」好DIVE的窩":
        artist = "IVE"
    elif artist == "SSS.jpg交易串":
        artist = "tripleS"
    elif artist == "好Bunnis的窩":
        artist = "NewJeans"
    elif artist == "鐵豚":
        artist = "Honkai:Star Rail"
    elif artist == "捕夢網":
        artist = "Dreamcatcher"
    elif artist == "機器人測試區":
        artist = "五月天"
    result = get_random_popular_track(artist)
    if result is None:
        return None
    else:
        track_name, track_url = result
        return artist ,track_name, track_url


def navigate_to_reply_post_message(driver,serial_number):
    reply_preview_element = WebDriverWait(driver,5).until(
            EC.presence_of_all_elements_located((By.XPATH,f"//div[@class='repliedTextPreview_f9f2ca clickable_f9f2ca' and @role='button']"))
        )
    try:
        post_element = reply_preview_element.pop()
        post_element.click()
    except exceptions or Exception:
        print("can not click reply preview")
    sleep(5)
    try:
        post_message = WebDriverWait(driver,5).until(
            EC.presence_of_element_located((By.XPATH,f"//div[@id='message-reactions-{serial_number}']"))
        )
    except exceptions.StaleElementReferenceException:
        print("can not locate post message")
    except exceptions.TimeoutException:
        print("timeout error")
    return post_message

def get_lucky_draw_user_list(driver,message,emoji_name):
    sleep(2)
    print(emoji_name)
    print(message.text)
    try:
        emoji_element = message.find_element(By.XPATH, f".//div[@role='button' and contains(@aria-label, '{emoji_name}')]")
        print("find emoji")
    except exceptions.NoSuchElementException:
        print("can not find emoji element")
    try:
        actions = ActionChains(driver)
        actions.move_to_element(emoji_element).perform()
        print("hover on the emoji element")
        sleep(3)
    except exceptions or TypeError:
        print("hover error")


    try:
        reaction_text = WebDriverWait(driver,5).until(
            EC.presence_of_element_located((By.XPATH,f"//div[@class='reactionTooltip_fba897']"))
        )
        print("find text")
        sleep(2)
        reaction_text.click()
        sleep(2)
    except exceptions.TimeoutException:
        print("can not click reaction text")
    try:
    # Wait until the popup window is located
        popup = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='reactors_f2bfbb thin_eed6a8 scrollerBase_eed6a8 fade_eed6a8']"))
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", popup)
    except exceptions.TimeoutException:
        print("Cannot locate reaction popup window")
        popup = None

    reaction_user_list = []

    if popup:
        count=0
        while True:
            # Scroll down by a small amount each time
            driver.execute_script("arguments[0].scrollBy(0, 500);", popup)
            sleep(3)  # Wait for more users to load

            # Find all usernames in the currently visible popup
            try:
                reaction_user_list_element = driver.find_elements(By.CLASS_NAME, "username_f2bfbb")
                reaction_name_list_element = driver.find_elements(By.CLASS_NAME, "name_f2bfbb")
                if reaction_user_list_element and reaction_name_list_element:
                    for index, (user_element, name_element) in enumerate(zip(reaction_user_list_element, reaction_name_list_element)):
                        # Append unique usernames to avoid duplicates
                        user_id = user_element.text.strip()
                        name_text = name_element.text.strip()
                        if user_id not in reaction_user_list :
                            if user_id == "":
                                user_id = name_text
                            print(f"Element {index + 1} text: {user_id}")
                            reaction_user_list.append(user_id)
                        

                else:
                    print("No elements found with class 'username_f2bfbb'")
                    
            except exceptions.NoSuchElementException :
                print("can not find reaction user list")
            count+=500
            if count+500 > last_height:
                break
        
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
 
    return reaction_user_list

def driver_set_up_login(email,password):
    user_agent=UserAgent.chrome
    # user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")  # For handling resource issues
    chrome_options.add_argument("--no-sandbox")  # For running in certain environments
    chrome_options.add_argument("--lang=en-us")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_prefs = {"intl.accept_languages": "en-US"}
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
        })

    driver.maximize_window()

    # Log in to Discord
    driver.get("https://discord.com/login")
    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        # Interact with the elements
        email_input.send_keys(email)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"An error occurred during login: {e}")

    # Navigate to the desired channel
    
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app-mount']/div[2]/div[1]/div[1]/div/div[2]/div/div/nav/ul/div[2]/div[3]/div[1]"))
        ).click()
        

    except Exception as e:
        print(f"An error occurred while navigating to the channel: {e}") 
    return driver

def get_original_tag_name(driver):
    pre=1
    user_tag_name = None
    current_message = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]")))
    while user_tag_name is None:
        previous_message = current_message.find_element(By.XPATH, f"preceding-sibling::li[{pre}]")
        previous_message_content = previous_message.find_element(By.XPATH, ".//div[contains(@class,'messageContent') and not(contains(@class,'repliedTextContent'))]")
        user_tag_name = get_user_tag_name(driver,previous_message_content)
        print(user_tag_name)
        print(pre)
        pre+=1
    return user_tag_name

def calculate_win_or_lose_exp(user_id, monster_lv, monster_exp):
    db = DiscordDatabaseManager()
    current_exp,current_level = db.get_user_current_exp_level(user_id)
    player_attack = random.randint(1,current_level)
    monster_health = random.randint(1,monster_lv)
    
    if player_attack >= monster_health:
        return "win",monster_exp
    else:
        return "lose", monster_exp//2

def main():
    # Set up WebDriver
    email = os.getenv("user_email")
    password =os.getenv("password")
    driver = driver_set_up_login(email,password)
    
    db = DiscordDatabaseManager()
    # Main loop for message processing
    # Path to your JSON file
    file_path = 'command_config.json'

    # Open the file and load the data
    with open(file_path, 'r', encoding='utf-8') as file:
        command = json.load(file)
    try:
        
        try:
            thread = WebDriverWait(driver, 1000).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='button'][contains(@aria-label, 'LE SSERAFIM')]")))
            thread.click()
            jump_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'barButtonAlt_cf58b5')]")))
            jump_button.click()
            message_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))  
                        )
        except Exception:
            pass
        
        message_queue=[]
        while True:
            # sleep(10)
            is_replied =False
            mentioned_thread = db.check_thread_is_mentioned()
            print(f"mentioned thread : {mentioned_thread}")
            if mentioned_thread is not None:    
                navigate_to_mention_thread(driver,mentioned_thread)
                db.set_thread_is_unmentioned(mentioned_thread)
            thread_element = WebDriverWait(driver,3).until(
                EC.presence_of_element_located((By.XPATH,"//h2[@class='defaultColor_a595eb heading-md/semibold_dc00ef defaultColor_e9e35f title_fc4f04']"))
            )
            full_text = thread_element.text
            thread_name = full_text.split(":")[-1].strip()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']"))
            )
            
            try:
                reply_message = WebDriverWait(driver, 0.5).until(
                    EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]//div[contains(@class,'messageContent') and (contains(@class,'repliedTextContent'))]"))
                )
                reply_message_text = reply_message.text
                print(reply_message_text)
                serial_number = reply_message.get_attribute("id")[16:]
                
                is_replied = True
            except exceptions.TimeoutException:
                
                
                try:
                    reply_message = WebDriverWait(driver, 0.5).until(
                        EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]//div[contains(@class,'repliedTextPreview_f9f2ca clickable_f9f2ca')]"))
                    )
                    parent_element = reply_message.find_element(By.XPATH,"..")
                    reply_message_text = reply_message.text
                    print(reply_message_text)
                    serial_number = parent_element.get_attribute("id")[22:]
                    
                    is_replied = True
                except exceptions.TimeoutException:
                    # print("can not find image reply message")
                    pass
            
            try:
                message = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//ol[@data-list-id='chat-messages']/li[last()]//div[contains(@class,'messageContent') and not(contains(@class,'repliedTextContent'))]"))
                )
                message_text = message.text
                print(message_text)
                
                    
                # lucky_draw(driver,message,"heart")
                # serial_number = message.get_attribute("id")[16:]
                # print(serial_number)
            except exceptions.TimeoutException:
                print("can not find simple message")
            except exceptions.StaleElementReferenceException:
                print("message text stale error")
                continue
            message_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
            if message_text == "!今日運勢":
                fortune_teller(driver, message, message_input)

            elif message_text == "!打怪":
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    serial_number,user_tag_name = get_original_poster_tag_name(driver)
                latest_created_time = db.get_latest_pve_created_time(user_tag_name)
                created_time = datetime.strptime(str(latest_created_time), "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                time_difference = now - created_time
                cool_down_minutes =  timedelta(minutes=10)
                if time_difference < cool_down_minutes and latest_created_time is not None:
                    message_input.send_keys(f"現在還在打怪CD時間，已經過了 {time_difference} ，CD是10分鐘")
                    message_input.send_keys(Keys.RETURN)
                    continue
                file_path = "monster.json"
                with open(file_path, 'r', encoding='utf-8') as file:
                    monster_config = json.load(file)
                monsters = list(monster_config.keys())
                random_monster = random.choice(monsters)
                random_monster_lv = monster_config[random_monster]["LV"]
                random_monster_exp = monster_config[random_monster]["EXP"]
                win_or_lose, gain_exp = calculate_win_or_lose_exp(user_tag_name,random_monster_lv,random_monster_exp)
                db.log_user_battle_pve(user_tag_name,random_monster,win_or_lose,gain_exp)
                if win_or_lose == "win":
                    db.update_user_exp(gain_exp,user_tag_name)
                    message_input.send_keys(f"@{user_tag_name} 您擊倒了 LV {random_monster_lv} 的 {random_monster}，並獲得了 {gain_exp} 經驗值 ")
                    message_input.send_keys(Keys.RETURN)
                elif win_or_lose == "lose":
                    
                    db.update_user_minus_exp(gain_exp,user_tag_name)
                    if random_monster == "比愛心的呂小弟":
                        image_path = os.path.join("idol_image", "比愛心的呂小弟.JPG")
                        relative_path = image_path
                        absolute_path = os.path.abspath(relative_path)
                        upload_element = driver.find_element(By.XPATH, "//input[@class='file-input' and @type='file']")   
                        upload_element.send_keys(absolute_path)
                        sleep(1.5)
                    message_input.send_keys(f"@{user_tag_name} 很不幸地，您輸給了 LV {random_monster_lv} 的 {random_monster}，並失去了 {gain_exp} 經驗值 ")
                    message_input.send_keys(Keys.RETURN)
                    sleep(1)
                    
                
            elif message_text == "!pin":
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    serial_number,user_tag_name = get_original_poster_tag_name(driver)
                if is_replied is True and user_tag_name == "nicklee_":
                    command["!公告"] = reply_message_text
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(command, file, indent=4, ensure_ascii=False)
                    


            elif message_text == "!level":
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    serial_number,user_tag_name = get_original_poster_tag_name(driver)
                current_exp,current_level = db.get_user_current_exp_level(user_tag_name)
                
                message_input.send_keys(f"@{user_tag_name}  目前獲取經驗值 : {current_exp}，等級 : {current_level}")
                message_input.send_keys(Keys.RETURN)

            elif message_text == "!魯王":
                results = db.get_top_level_user()
                message_input.send_keys("魯王排行榜前五名")
                message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                for i in range(0,len(results)):
                    user_tag_name = results[i][0]
                    current_exp = results[i][1]
                    current_level = results[i][2]
                    message_input.send_keys(f"@{user_tag_name}  目前獲取經驗值 : {current_exp}，等級 : {current_level}")
                    message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                message_input.send_keys("真的超魯的，宅必了")
                message_input.send_keys(Keys.RETURN)

            elif message_text == "!song":
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    serial_number,user_tag_name = get_original_poster_tag_name(driver)
                result = get_recommend_track(user_tag_name)
                if result is None:
                    message_input.send_keys("找不到適合你的歌，ㄏ")
                    message_input.send_keys(Keys.RETURN)
                else:
                    artist, track_name, track_url = result
                    message_input.send_keys(f"@{user_tag_name} 這邊推薦您 {artist} 的 {track_name}，希望您會喜歡")
                    message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                    message_input.send_keys("      (Spotify 優越專用)      ")
                    message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                    message_input.send_keys(f"{track_url}")
                    message_input.send_keys(Keys.RETURN)

            elif message_text == "!亂源":
                top_users = db.get_top_user_in_thread(thread_name,3)
                total_message_count = db.get_message_count_from_thread(thread_name)
                
                message_input.send_keys("讓我來向您介紹本串亂源名單 : ")
                message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                for user in top_users:
                    message_percentage = round(int(user[1])/int(total_message_count)*100,0)
                    print(int(user[1]))
                    print(int(total_message_count))
                    message_input.send_keys(f"@{user[0]} 在過去一周在本串發言了 {user[1]} 次，發言率 {message_percentage}%")
                    message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                message_input.send_keys("真的超可憐的，人生只剩下DC是不是，請大家共同譴責他們")
                message_input.send_keys(Keys.RETURN)


            elif message_text.startswith("!dreamrank"):
                dream_text = message_text[11:]
                result = db.get_dream_text_count_from_thread(dream_text)
                message_input.send_keys("夢男串排行榜")
                message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                if len(result) < 1:
                    message_input.send_keys("沒有此相關訊息")
                else:  
                    for i in range(0,len(result)):
                        thread, text_count  = result[i]
                        message_input.send_keys(f"{thread} 串 出現了 {text_count} 次 {dream_text}, 超魯的")
                        message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                message_input.send_keys(Keys.RETURN)


            elif message_text.startswith("!recap"):
                user_tag_name = get_message_tag_name(driver,message)
                if user_tag_name is None:
                    serial_number,user_tag_name = get_original_poster_tag_name(driver)
                
                result = db.get_user_recap(user_tag_name)
                message_count, popular_emoji, popular_thread, thread_message_count, emoji_count = result 
                recap_header = f" @{user_tag_name} 以下為你的本月回顧 : "
                message_input.send_keys(recap_header)
                message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                recap_content_1 = f"我們在各討論串發現了好多你的足跡，這個月來你總共發送了{message_count+emoji_count} 條訊息，最喜歡的表情符號是 {popular_emoji}"
                message_input.send_keys(recap_content_1)
                message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                recap_content_2 = f"同時，你在 {popular_thread} 串也非常活躍！總共在這個討論串講了 {thread_message_count} 次話，{popular_thread}串不再是死群！"
                message_input.send_keys(recap_content_2)
                message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                recap_end = f"感謝你的付出，讓討論串不再無聊，在新的一個月，請繼續保持，繼續作夢！"
                message_input.send_keys(recap_end)
                message_input.send_keys(Keys.RETURN)

            elif message_text.startswith("!抽獎"):
                if is_replied != True:
                    pass
                else:
                    #!抽獎 -n 6 -e EMOJI_NAME
                    n_match = re.search(r"-n (\d+)", message_text)
                    emoji_match = re.search(r"-e (.+)", message_text)
                    n_value = int(n_match.group(1)) if n_match else None
                    emoji_name = emoji_match.group(1) if emoji_match else None
                    
                    message_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
                    
                    post_message = navigate_to_reply_post_message(driver,serial_number)
                    print(post_message.text)
                    try:
                        user_list = get_lucky_draw_user_list(driver,post_message,emoji_name)
                        print(user_list)
                        sleep(2)
                        if n_value is not None:
                            try:
                                lucky_guys = random.sample(user_list,n_value)
                            except ValueError:
                                print("can not exceed user list")
                        else:
                            lucky_guys = random.sample(user_list,1)
                        
                        
                        message_input.send_keys(f"參加抽獎名單 :")
                        message_input.send_keys(Keys.RETURN)
                        for user in user_list:
                            message_input.send_keys(user)
                            message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                        message_input.send_keys(Keys.BACK_SPACE)
                        message_input.send_keys(Keys.RETURN)
                        for guy in lucky_guys:
                            message_input.send_keys(f"抽到 {guy} 了，他不要，他要捐出來")
                            message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                        message_input.send_keys(Keys.BACK_SPACE)
                        message_input.send_keys(Keys.RETURN)
                    except exceptions.ElementNotInteractableException:
                        print("element is not interactable")


            elif message_text == "!ALL":
                general_text = "目前已有機器人指令如下:"
                message_input.send_keys(general_text)
                message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                for key in command:
                    message_input.send_keys(key)
                    message_input.send_keys(Keys.SHIFT, Keys.RETURN)
                message_input.send_keys(Keys.BACK_SPACE)
                message_input.send_keys(Keys.RETURN)
            
            elif message_text.startswith("!PICK"):
                option = random_pick_one(message_text)
                user_tag_name = get_user_tag_name(driver,message)
                if user_tag_name is None:
                    user_tag_name = get_original_tag_name(driver)
                    
                        
                try:
                    message_input.send_keys(f"@{user_tag_name} 小弟弟我的建議是 : "+option)
                    message_input.send_keys(Keys.RETURN)
                except:
                    pass

            elif message_text.startswith("!吃什麼"):
                user_tag_name = get_user_tag_name(driver,message)
                if user_tag_name is None:
                    user_tag_name = get_original_tag_name(driver)
                try:
                    message_list = message_text.split()
                    if len(message_list)<2:
                        recommend_restaurant = "老麥"
                    else:
                        print(message_list)
                        location = message_list[1]
                        print(location)
                        try:
                            recommend_restaurant, address = get_recommend_restaurant(location)
                            print(address)
                            print(recommend_restaurant)
                        except Exception as e:
                            print(f"recommend function got : {e}")
                except Exception as e:
                    print(e)

                try:
                    message_input.send_keys(f"@{user_tag_name} 感覺現在來吃個 {recommend_restaurant} 還不錯")
                    message_input.send_keys(Keys.SHIFT,Keys.RETURN)
                    if address is not None:
                        address = address[3:]
                        if address[0] == " ":
                            address = address[1:]
                        message_input.send_keys(f"https://www.google.com/maps?q={address}")
                    message_input.send_keys(Keys.RETURN)
                except exceptions.ElementNotInteractableException as e:
                    print(e)
                    pass
                except Exception:
                    message_input.send_keys(f"@{user_tag_name} 店家名稱我打不出來，請重新輸入")
                    message_input.send_keys(Keys.RETURN)

            elif message_text in command:
                print(f"Found message: {message_text}")
                serial_number = message.get_attribute("id")[16:]
                print(serial_number)
                try:
                    username_element = message.find_element(By.XPATH, f"//*[@id='message-username-{serial_number}']")
                    username = username_element.text
                except Exception:
                    username = "Hi"
                
                if command[message_text] is None:
                    try:
                        relative_path = f"LS_album_card/{message_text[1:]}.jpg"
                        absolute_path = os.path.abspath(relative_path)
                        upload_element = driver.find_element(By.XPATH, "//input[@class='file-input' and @type='file']")   
                        upload_element.send_keys(absolute_path)
                        sleep(3)
                        # user_tag_name = get_user_tag_name(driver,message)
                        # if user_tag_name is None:
                        #     user_tag_name = get_original_tag_name(driver)
                        # message_input.send_keys(f"@{user_tag_name}")
                        message_input.send_keys(Keys.RETURN)
                        sleep(2)
                    except Exception as e:
                        print(f"Error interacting with message options: {e}")
                else:
                    message_input = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))  
                            )
                    command_message = command[message_text]
                    if is_replied is True:
                        user_tag_name = get_user_tag_name(driver,message)
                        if user_tag_name is None:
                            user_tag_name = get_original_tag_name(driver)
                        print(user_tag_name)
                        
               
                        message_input.send_keys(f"@{user_tag_name} {command_message}" )
                    else:
                        message_input.send_keys(command_message)
                        
                        

                    message_input.send_keys(Keys.RETURN)
                    
            else:
                pass
            
            sleep(0.1)  # Wait before checking for new messages

    except KeyboardInterrupt:
        print("Script interrupted by user.")
        driver.quit()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("interrupt")
        
        driver.quit()


if __name__ == '__main__':
    main()