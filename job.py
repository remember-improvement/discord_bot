from database_manager import DiscordDatabaseManager

from mysql.connector import Error
import math
import random
class Job:
    def __init__(self, user_id):
        self.db = DiscordDatabaseManager()
        self.user_id = user_id
        exp, level = self.db.get_user_current_exp_level(user_id)
        self.exp = exp
        self.lv = level
        win_streak = self.db.get_user_pvp_win_streak(user_id)
        lose_streak = self.db.get_user_pvp_lose_streak(user_id)
        self.win_streak = win_streak
        self.lose_streak = lose_streak
    

    def get_exp_threshold(self,level):
        if level < 15:
            return 600
        elif 15 <= level < 30:
            return 900
        elif 30 <= level < 45:
            return 1200
        elif 45 <= level < 60:
            return 1500
        elif 60 <= level < 85:
            return 3000
        elif 85 <= level < 100:
            return 5000
        else:
            return 10000

    def calculate_level_exp(self,user_id, current_level, current_exp, gain_exp):
        db = DiscordDatabaseManager()

        # Define thresholds for each range of levels
         # You can set a default or max threshold if needed

        remaining_exp = current_exp + gain_exp
        level_up = False

        # Loop to handle leveling up multiple times if the gain_exp is large
        while remaining_exp >= self.get_exp_threshold(current_level):
            threshold = self.get_exp_threshold(current_level)
            remaining_exp -= threshold
            current_level += 1
            level_up = True

    # Update user level and remaining exp in database
        if level_up and current_level < 40:
            print(f"Level up! New level: {current_level}, remaining exp: {remaining_exp}")
            db.update_user_level(user_id, remaining_exp, current_level)
        elif level_up and current_level >=40:
            print(f"Level up! New level: {current_level}, remaining exp: 0")
            db.update_user_level(user_id, 0, current_level)
        else:
            db.update_user_exp(remaining_exp,user_id)

    def minus_user_exp(self,exp,user_id):
        if self.exp - exp < 0:
            self.db.update_user_exp(0,user_id)
        else:
            self.db.update_user_minus_exp(exp,user_id)

    def update_user_plus_current_exp(self, user_id):
        
        self.db.connection.autocommit = True
        try:
            cursor = self.db.connection.cursor()
            
            query = """
                    UPDATE discord.user_level ul
                    JOIN `discord`.`user` u ON ul.user_id = u.id
                    SET ul.current_gain_exp = ul.current_gain_exp + 1
                    WHERE u.user_id = %s;     
                    """
            cursor.execute(query,(user_id,))
            print("update user current exp plus 1")
        except Error as e:
            print(f"Update user current gain exp to +1 error: {e}")
            return None 
        finally:
            cursor.close()
    
    def update_user_minus_current_exp(self, user_id):
        current_gain_exp = self.db.get_user_current_gain_exp(user_id)
        if current_gain_exp - 1 < 0:
            print("User current gain exp is 0")
        else:
            self.db.connection.autocommit = True
            try:
                cursor = self.db.connection.cursor()
                
                query = """
                        UPDATE discord.user_level ul
                        JOIN `discord`.`user` u ON ul.user_id = u.id
                        SET ul.current_gain_exp = ul.current_gain_exp - 1
                        WHERE u.user_id = %s;     
                        """
                cursor.execute(query,(user_id,))
                print("update user current exp minus 1")
            except Error as e:
                print(f"Update user current gain exp to -1 error: {e}")
                return None 
            finally:
                cursor.close()

    def streak_exp_modifier(self, exp, current_level):

        def get_modified_exp_threshold(level):
            if level < 15:
                return 100
            elif 15 <= level < 30:
                return 80
            elif 30 <= level < 45:
                return 50
            elif 45 <= level < 60:
                return 30
            else:
                return 10
        if self.win_streak > 1 :
            modified_exp = exp + (get_modified_exp_threshold(current_level)*self.win_streak)
            return modified_exp
        else:
            return exp + get_modified_exp_threshold(current_level)


    def __str__(self):
        return f" Exp: {self.exp}, Level: {self.lv}"


# Subclass for Knight
class Knight(Job):
    def __init__(self,user_id):
        super().__init__(user_id)

    


    def duel_result(self, user_id,result, bargain_exp):
        if result == 'win':

            if 1 < self.lose_streak+1 < 6:
                gain_exp = self.streak_exp_modifier(bargain_exp,self.lv)*self.lose_streak*0.8
            else :
                gain_exp = bargain_exp*0.8
            self.calculate_level_exp(user_id,self.lv,self.exp,gain_exp)
            print("Knight won the duel.")
            return math.ceil(gain_exp)
            
        else:
            lost_exp = bargain_exp*0.8    # Loses 50% less exp on loss
            self.minus_user_exp(lost_exp,user_id)
            print("Knight lost the duel.")
            return int(lost_exp)
            


# Subclass for Thief
class Thief(Job):
    def __init__(self,user_id):
        super().__init__(user_id)



    def duel_result(self, user_id,result, bargain_exp):
        if result == 'win':
            if 1<self.win_streak +1 < 6   :
                gain_exp =  self.streak_exp_modifier(bargain_exp,self.lv)*(self.win_streak+1)*1.2 
            else:
                gain_exp = bargain_exp*1.2 
            self.calculate_level_exp(user_id,self.lv,self.exp,gain_exp)
            print("Thief won the duel.")
            return math.ceil(gain_exp)
            
        else:
            if 1<self.lose_streak+1 < 6 :
                lost_exp = self.streak_exp_modifier(bargain_exp,self.lv)*(self.lose_streak+1)*1.2 
            else:
                lost_exp = bargain_exp*1.2 
            self.minus_user_exp(lost_exp,user_id)
            print("Thief lost the duel.")
            return math.ceil(lost_exp)

# Subclass for Mage
class Mage(Job):
    def __init__(self,user_id):
        super().__init__(user_id)

    def duel_result(self,user_id ,result, bargain_exp):
        double_secret_trigger = random.random() < 0.1  # 10% chance to trigger secret
        triple_secret_trigger = random.random() < 0.05
        five_times_secret_trigger = random.random() < 0.01
        if result == 'win':
            if double_secret_trigger:
                print("Mage triggered a secret effect! 2x exp!")
                gain_exp = bargain_exp*2
                self.calculate_level_exp(user_id, self.lv, self.exp, gain_exp)
                return math.ceil(gain_exp), "觸發2倍秘密!"
            elif triple_secret_trigger:
                print("Mage triggered a secret effect! 3x exp!")
                gain_exp = bargain_exp*3
                self.calculate_level_exp(user_id, self.lv, self.exp, gain_exp)
                return math.ceil(gain_exp), "觸發3倍秘密!"
            elif triple_secret_trigger:
                print("Mage triggered a secret effect! 5x exp!")
                gain_exp = bargain_exp*5
                self.calculate_level_exp(user_id, self.lv, self.exp, gain_exp)
                return math.ceil(gain_exp), "觸發5倍秘密!"
            else:
                self.calculate_level_exp(user_id, self.lv, self.exp, bargain_exp)
                return math.ceil(bargain_exp)
        else:            
            print("Mage lost the duel.")
            if double_secret_trigger:
                self.minus_user_exp(bargain_exp*2,user_id)  # 2x exp loss
                return math.ceil(bargain_exp*2), "觸發2倍秘密!"
            elif triple_secret_trigger:
                self.minus_user_exp(bargain_exp*3,user_id)  # 3x exp loss
                return math.ceil(bargain_exp*3), "觸發3倍秘密!"
            elif five_times_secret_trigger:
                self.minus_user_exp(bargain_exp*5,user_id)  # 5x exp loss
                return math.ceil(bargain_exp*5), "觸發5倍秘密!"
            else:
                self.minus_user_exp(bargain_exp,user_id)
                return math.ceil(bargain_exp)

# Subclass for Priest
class Priest(Job):
    def __init__(self, user_id):
        super().__init__(user_id)

    def duel_result(self, user_id,result,bargain_exp):
        if result == 'win':
            if self.db.get_user_current_gain_exp(user_id) < 100:
                if self.win_streak +1 >= 3:
                    self.update_user_plus_current_exp(user_id)
                self.update_user_plus_current_exp(user_id)
            self.calculate_level_exp(user_id,self.lv,self.exp,bargain_exp)
            print("Priest won the duel.")
            return int(bargain_exp)
           
        else:
            if self.db.get_user_current_gain_exp(user_id) > 10:
                if self.lose_streak+1 >=3:
                    self.update_user_minus_current_exp(user_id)
                self.update_user_minus_current_exp(user_id)
            self.minus_user_exp(bargain_exp,user_id)
            print("Priest lost the duel.")
            return int(bargain_exp)
   





