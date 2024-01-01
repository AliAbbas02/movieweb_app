from data_Manager import DataManagerInterface
import csv

class CSVDataManager(DataManagerInterface):
    def __init__(self,filename):
        self.filename:str = filename

    def get_all_users(self) -> dict:
        with open(self.filename) as file:
            csv_reader:dict = csv.DictReader(file)
        
        return self.sorting_data(csv_reader)
    
    @staticmethod
    def sorting_data(data) -> dict:
        all_users:dict = {}
        for each_user in data:
                id:int = int(each_user['id'])
                name:str = each_user['name']
                movies:dict = each_user['movies']
                all_users[id]:dict = {'name': name,\
                                   'movies': movies}
        
        return all_users



    def get_user_movies(self, user_id) -> dict:
        return self.get_all_users()[user_id]['movies']
    

    
