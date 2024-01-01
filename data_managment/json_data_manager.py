import json
from data_Manager import DataManagerInterface


class JSONDataManager(DataManagerInterface):
    def __init__(self, filename):
        self.filename:str = filename
    
    def get_all_users(self) -> dict:
        with open(self.filename) as file:
            data:dict = json.load(file)
        return data

    
    def get_user_movies(self, user_id) -> dict:
        all_users = self.get_all_users()
        return all_users[user_id]['movies']
    
    def validate_user(self, id, password) -> bool:
        try:
            user = self.get_all_users()[str(id)]
            if user['password'] == password:
                return True
            return False
        except KeyError:
            return False
    

        

    





