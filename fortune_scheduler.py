import os
from time import sleep
from datetime import datetime, timedelta
from database_manager import DiscordDatabaseManager
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import schedule
load_dotenv()

def create_connection():
    try:
        # Connect to MySQL with correct credentials
        connection = mysql.connector.connect(
            host='localhost',       # Replace with your host if needed
            database='discord',     # Replace with your database name
            user='root',   # Replace with your MySQL username
            password='nick9176' # Replace with your MySQL password
        )
        
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
        
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None
db = DiscordDatabaseManager()
def reset_to_default():
    latest_created_time_id = db.get_all_created_time_and_id()
    reset_hours = timedelta(hours=24)
    for result in latest_created_time_id:
        created_time = datetime.strptime(str(result[1]), "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        time_difference = now - created_time
        print(time_difference)
        if time_difference >= reset_hours:
            db.update_user_current_gain_exp_to_default(result[0])
            print(f"Update {result[0]} current gain exp to default")
schedule.every(10).minutes.do(reset_to_default)

# Keeps the scheduler running
while True:
    schedule.run_pending()
    sleep(1)
