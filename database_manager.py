import mysql.connector
from mysql.connector import Error
import os
from time import sleep
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
class DiscordDatabaseManager:
    def __init__(self):
        self.connection = self.database_setup()

    def database_setup(self):
        connection = mysql.connector.connect(
            host=os.getenv("db_host"),
            user=os.getenv("db_user"),
            password=os.getenv("db_password"),
            database=os.getenv("db_name")
        )
        try:
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None

    def check_record_exists(self, table_name, column_name, value):
        try:
            cursor = self.connection.cursor()
            query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {column_name} = %s)"
            cursor.execute(query, (value,))
            exists = cursor.fetchone()[0]
            return exists
        except Error as err:
            print(f"Check record exists error: {err}")
            return False
    def log_message_history(self,user,thread,message_text,emoji,serial_number):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM `discord`.`user` WHERE user_id = %s", (user,))
            user_id = cursor.fetchone()
            cursor.execute("SELECT id FROM `discord`.`thread` WHERE thread = %s", (thread,))
            thread_id = cursor.fetchone()
            if user_id and thread_id:
                query = """
                        INSERT INTO `discord`.`message_log` (`user_id`, `thread_id`, `message`, `emoji`, `serial_number`)
                        VALUES (%s, %s, %s, %s, %s);
                        """
                
            else:
                raise Error
            cursor.execute(query, (user_id[0], thread_id[0], message_text, emoji, serial_number))
            self.connection.commit()
        
        
        except Error as err:
            print(f"log message history Error: {err}")

    def log_user_info(self, user_id, user_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO `discord`.`user` (`user_id`, `user_name`) VALUES (%s, %s);",
                (user_id, user_name)
            )
            self.connection.commit()
        except Error as err:
            self.connection.rollback()
            print(f"Log user info error: {err}")

    def update_user_info(self, user_id, user_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE `discord`.`user` SET `user_name` = %s WHERE `user_id` = %s;",
                (user_name, user_id)
            )
            self.connection.commit()
        except Error as err:
            self.connection.rollback()
            print(f"Update user info error: {err}")

    def log_fortune_history(self, user_id, fortune_level):
        latest_created_time = self.get_latest_fortune_log_created_time(user_id)
        created_time = datetime.strptime(str(latest_created_time), "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        time_difference = now - created_time
        cool_down_hours =  timedelta(hours=6)
        
        if (time_difference) < cool_down_hours and latest_created_time is not None:
            print(time_difference)
            pass
        else:
            try:
                cursor = self.connection.cursor()
                query = """
                    INSERT INTO `discord`.`fortune_log` (`user_id`, `fortune_level_id`)
                    SELECT u.id, fl.id
                    FROM `discord`.`user` u
                    JOIN `discord`.`fortune_level` fl
                    ON u.id = (SELECT id FROM `discord`.`user` WHERE user_id = %s)
                    AND fl.id = (SELECT id FROM `discord`.`fortune_level` WHERE level = %s);
                    """
                cursor.execute(query, (user_id, fortune_level))
                self.connection.commit()
            except Error as err:
                self.connection.rollback()
                print(f"Log fortune history error: {err}")
        

    def get_fortune_level_count(self, user_id):
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT 
                    fr.level AS fortune_level, 
                    COUNT(*) AS count
                FROM 
                    discord.fortune_log fl
                JOIN 
                    discord.fortune_level fr ON fl.fortune_level_id = fr.id
                WHERE 
                    fl.user_id = (
                        SELECT id 
                        FROM discord.user 
                        WHERE user_id = %s
                    )
                    AND fl.fortune_level_id IN (1, 2, 3, 4, 5)
                GROUP BY 
                    fl.fortune_level_id, fr.level;
                """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"Get fortune level count error: {e}")
            return []
    def get_user_recap(self, user_id):
        try:
            cursor = self.connection.cursor()
            query = """
                       SELECT 
                        COUNT(ml.id) AS message_count,  -- Total message count for the user

                        (SELECT emoji 
                        FROM discord.message_log 
                        WHERE emoji IS NOT NULL 
                        AND user_id = u.id 
                        AND created_time >= NOW() - INTERVAL 1 MONTH  -- Filter for the past month
                        GROUP BY emoji 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 1) AS most_popular_emoji,  -- Most popular emoji for the user

                        (SELECT t.thread -- Retrieve the thread name
                        FROM discord.message_log ml2
                        JOIN discord.thread t ON ml2.thread_id = t.id
                        WHERE ml2.thread_id IS NOT NULL 
                        AND ml2.user_id = u.id 
                        AND ml2.created_time >= NOW() - INTERVAL 1 MONTH  -- Filter for the past month
                        GROUP BY ml2.thread_id 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 1) AS most_popular_thread,  -- Most popular thread name for the user

                        (SELECT COUNT(*) 
                        FROM discord.message_log ml3
                        WHERE ml3.thread_id = (SELECT thread_id 
                                                FROM discord.message_log ml4
                                                WHERE ml4.thread_id IS NOT NULL 
                                                AND ml4.user_id = u.id 
                                                AND ml4.created_time >= NOW() - INTERVAL 1 MONTH  -- Filter for the past month
                                                GROUP BY ml4.thread_id 
                                                ORDER BY COUNT(*) DESC 
                                                LIMIT 1) 
                        AND ml3.user_id = u.id) AS message_count_in_popular_thread,  -- Message count in the most popular thread

                        (SELECT COUNT(*)
                        FROM discord.message_log ml5
                        WHERE ml5.user_id = u.id 
                        AND ml5.created_time >= NOW() - INTERVAL 1 MONTH  -- Filter for the past month
                        AND ml5.emoji IS NOT NULL) AS emoji_count  -- Count of emojis for the user

                        
                    FROM discord.message_log ml
                    JOIN discord.user u ON ml.user_id = u.id
                    WHERE u.user_id = %s
                    AND ml.created_time >= NOW() - INTERVAL 1 MONTH  -- Filter for the past month
                    GROUP BY u.user_id;
                    """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Get user recap error: {e}")
            return None

    def get_user_dream_context(self, context):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT user_id, COUNT(*) AS message_count
                    FROM discord.message_log
                    WHERE message LIKE %s
                    GROUP BY user_id
                    ORDER BY message_count DESC
                    LIMIT 1;
                    """   
            cursor.execute(query, ('%' + context + '%',))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Get user dream context error: {e}")
            return None
    
    def get_dream_text_count_from_thread(self, context):
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT 
                    t.thread,
                    COUNT(ml.thread_id) AS message_count
                FROM 
                    discord.message_log ml
                JOIN 
                    discord.thread t ON ml.thread_id = t.id
                WHERE 
                    ml.message LIKE %s
                GROUP BY 
                    t.thread
                ORDER BY 
                    message_count DESC
                LIMIT 3;
                   """
            cursor.execute(query, ('%' + context + '%',))
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Get user dream context count error: {e}")
            return None

    def get_most_message_thread(self, user_id, size):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT 
                        t.thread,
                        COUNT(ml.id) AS message_count
                    FROM 
                        discord.message_log ml
                    JOIN 
                        discord.thread t ON ml.thread_id = t.id
                    JOIN 
                        discord.user u ON ml.user_id = u.id
                    WHERE 
                        u.user_id = %s
                        AND ml.created_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY 
                        t.thread
                    ORDER BY 
                        message_count DESC
                    LIMIT %s;
                  """
            cursor.execute(query, (user_id,size))
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Get user most message thread error: {e}")
            return ('LE SSERAFIM',)    

    def set_thread_is_mentioned(self,thread):
        try:
            cursor = self.connection.cursor()
            query = """
                    UPDATE `discord`.`thread` SET `is_mentioned` = 1 WHERE (`thread` = %s);
                    """
            cursor.execute(query, (thread,))
            self.connection.commit()
        except Error as e:
            print(f"Set thread is mentioned error: {e}")
        finally:
            cursor.close()

    def set_thread_is_unmentioned(self,thread):
        try:
            cursor = self.connection.cursor()
            query = """
                    UPDATE `discord`.`thread` SET `is_mentioned` = 0 WHERE (`thread` = %s);
                    """
            cursor.execute(query, (thread,))
            self.connection.commit()
            print(f"set {thread} to unmentioned")
        except Error as e:
            print(f"Set thread is unmentioned error: {e}")
        finally:
            cursor.close()
    
    def check_thread_is_mentioned(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("FLUSH TABLES;")
            query = """
                    SELECT SQL_NO_CACHE `thread` from `discord`.`thread` WHERE `is_mentioned` = 1;                 
                    """
            cursor.execute(query)
            result = cursor.fetchall()
            
            if result:
            
                return result[0][0]
            else:
                
                return None
            
        except Error as e:
            print(f"Check thread is mentioned error: {e}")
            return None
        finally:
            cursor.close()

    def get_top_user_in_thread(self, thread, count):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT 
                        u.user_id,
                        COUNT(ml.id) AS message_count
                    FROM 
                        discord.message_log ml
                    JOIN 
                        discord.user u ON ml.user_id = u.id
                    JOIN 
                        discord.thread t ON ml.thread_id = t.id
                    WHERE 
                        t.thread = %s  
                        AND ml.created_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY 
                        u.user_name
                    ORDER BY 
                        message_count DESC
                    LIMIT %s;
                    """
            cursor.execute(query,(thread,count))
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Get top user in thread error: {e}")
            return None  
        finally:
            cursor.close()

    def get_message_count_from_thread(self, thread):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT 
                        COUNT(ml.id) AS total_message_count
                    FROM 
                        discord.message_log ml
                    JOIN 
                        discord.thread t ON ml.thread_id = t.id
                    WHERE 
                        t.thread = %s
                        AND ml.created_time >= DATE_SUB(NOW(), INTERVAL 7 DAY);
                    """
            cursor.execute(query,(thread,))
            result = cursor.fetchall()
            print(result)
            return result[0][0]
        except Error as e:
            print(f"Get messaage count from thread error: {e}")
            return None 
        finally:
            cursor.close()

    def update_user_exp(self, exp, user_id):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            query = """
                    UPDATE `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.exp = ul.exp + %s  
                    WHERE u.user_id = %s;  
                    """
            cursor.execute(query,(exp,user_id))
            print(f"Rows affected: {cursor.rowcount}")
        except Error as e:
            print(f"Update user exp error: {e}")
            self.connection.rollback()
            return None 
        finally:
            cursor.close()

    def update_user_minus_exp(self, exp, user_id):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            query = """
                    UPDATE `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.exp = ul.exp - %s  
                    WHERE u.user_id = %s;  
                    """
            cursor.execute(query,(exp,user_id))
            print(f"Rows affected: {cursor.rowcount}")
        except Error as e:
            print(f"Update user minus exp error: {e}")
            self.connection.rollback()
            return None 
        finally:
            cursor.close()

    def get_user_current_exp_level(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("FLUSH TABLES;")
            query = """
                    SELECT ul.exp,ul.level
                    FROM `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    WHERE u.user_id = %s;
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            return result[0]
    
        except Error as e:
            print(f"Get current user exp error: {e}")
            return None 
        finally:
            cursor.close()

    def update_user_level(self, user_id, exp):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            query_exp="""
                    UPDATE discord.user_level ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.exp = %s   
                    WHERE u.user_id = %s; 
                    """
            cursor.execute(query_exp,(exp,user_id))
            query = """
                    UPDATE `discord`.`user_level`ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET `level` = `level` + 1 
                    WHERE u.`user_id` = %s;
                    """
            cursor.execute(query,(user_id,))
            
            # self.connection.commit()
        except Error as e:
            print(f"Update user exp error: {e}")
            return None 
        finally:
            cursor.close()
    
    
    def get_user_updated_time(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("FLUSH TABLES;")
            query = """
                    SELECT ul.updated_time
                    FROM `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    WHERE u.user_id = %s;
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            if not result:
                return True
            else:
                return result[0][0]
        except Error as e:
            print(f"Get current user updated_time error: {e}")
            return None 
        finally:
            cursor.close()

    def get_user_fortune_exp(self, user_id):
        try:
            cursor = self.connection.cursor()
            
            query = """
                    SELECT fl2.fortune_exp
                    FROM `discord`.`fortune_level` fl2
                    WHERE fl2.id = (
                        SELECT fl1.fortune_level_id
                        FROM `discord`.`fortune_log` fl1
                        JOIN `discord`.`user` u ON fl1.user_id = u.id
                        WHERE u.user_id = %s
                        ORDER BY fl1.created_time DESC
                        LIMIT 1
                    );
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            
            if not result:
                return 20
            else:
                return result[0][0]
            
        except Error as e:
            print(f"Get user fortune exp error: {e}")
            return None 
        finally:
            cursor.close()
    
    def update_user_current_gain_exp(self, user_id):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            current_gain_exp = self.get_user_fortune_exp(user_id)
            query = """
                    UPDATE discord.user_level ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.current_gain_exp = %s   
                    WHERE u.user_id = %s;     
                    """
            cursor.execute(query,(current_gain_exp,user_id))
        except Error as e:
            print(f"Update user current gain exp error: {e}")
            return None 
        finally:
            cursor.close()
    
    def update_user_current_gain_exp_to_default(self, user_id):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            
            query = """
                    UPDATE discord.user_level ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.current_gain_exp = 20
                    WHERE u.id = %s;     
                    """
            cursor.execute(query,(user_id,))
        except Error as e:
            print(f"Update user current gain to default exp error: {e}")
            return None 
        finally:
            cursor.close()

    def get_user_current_gain_exp(self, user_id):
        try:
            cursor = self.connection.cursor()
            
            query = """
                    SELECT ul.current_gain_exp
                    FROM `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    WHERE u.user_id = %s; 
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            if not result:
                return 20
            else:
                return result[0][0]
        except Error as e:
            print(f"Get user current gain exp error: {e}")
            return None 
        finally:
            cursor.close()

    def get_top_level_user(self):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT u.user_id, ul.exp, ul.level
                    FROM `discord`.`user_level` ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    WHERE u.id NOT IN (6367,15) 
                    ORDER BY ul.level DESC, ul.exp DESC
                    LIMIT 5;
                    """
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Get top level user error: {e}")
            return None 
        finally:
            cursor.close()
    
    def get_latest_fortune_log_created_time(self,user_id):
        try:
            cursor = self.connection.cursor()
            query = """
                    SELECT fl.created_time
                    FROM `discord`.`fortune_log` fl
                    JOIN `discord`.`user` u ON fl.user_id = u.id
                    WHERE u.user_id = %s
                    ORDER BY fl.created_time DESC
                    LIMIT 1;
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            if not result:
                return datetime.strptime("2024-09-02 01:24:58", "%Y-%m-%d %H:%M:%S")
            return result[0][0]
        except Error as e:
            print(f"Get latest fortune log created time error: {e}")
            return None 
        finally:
            cursor.close()
    
    def get_all_created_time_and_id(self):
        try:
            cursor = self.connection.cursor()
            query = """
                   SELECT 
                    f.user_id, 
                    f.created_time
                FROM 
                    discord.fortune_log f
                JOIN 
                    (SELECT 
                        user_id, 
                        MAX(created_time) AS max_created_time
                    FROM 
                        discord.fortune_log
                    GROUP BY 
                        user_id
                    ) latest 
                ON 
                    f.user_id = latest.user_id 
                    AND f.created_time = latest.max_created_time;
                    """
            cursor.execute(query)
            result = cursor.fetchall()
            
            return result
        except Error as e:
            print(f"Get all latest fortune log created time and user id error: {e}")
            return None 
        finally:
            cursor.close()
    
    def get_latest_pve_created_time(self, user_id):
        
        try:
            cursor = self.connection.cursor()
            query = """
                   SELECT bp.created_time
                    FROM `discord`.`battle_pve_log` bp
                    JOIN `discord`.`user` u ON bp.user_id = u.id
                    WHERE u.user_id = %s
                    ORDER BY bp.created_time DESC
                    LIMIT 1;
                    """
            cursor.execute(query,(user_id,))
            result = cursor.fetchall()
            if not result:
                return datetime.strptime("2024-09-02 01:24:58", "%Y-%m-%d %H:%M:%S")
            return result[0][0]
        except Error as e:
            print(f"Get all latest fortune log created time and user id error: {e}")
            return None 
        finally:
            cursor.close()
    
    def log_user_battle_pve(self, user_id, monster ,win_or_lose, gain_exp):
        self.connection.autocommit = True
        try:
            cursor = self.connection.cursor()
            query = """
                    INSERT INTO `discord`.`battle_pve_log` (`user_id`, `beat_monster`, `win_or_lose`, `gain_exp`)
                    SELECT u.id, %s, %s, %s
                    FROM `discord`.`user` u
                    WHERE u.id = (SELECT id FROM `discord`.`user` WHERE user_id = %s);

                    """
            cursor.execute(query,(monster,win_or_lose,gain_exp,user_id))
        except Error as e:
            print(f"log user battle pve error: {e}")
            return None 
        finally:
            cursor.close()