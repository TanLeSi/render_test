from dataclasses import dataclass
import numpy as np
import pandas as pd 
from datetime import date
TODAY = date.today()
TODAY = str(TODAY.strftime('%Y-%m-%d'))
from pathlib import Path
input = Path().cwd() / 'excel_files'

@dataclass
class Article:
    article_no: int
    sum_quantity: int 
    moq: int
    model: str
    factory: str
    movement: pd.DataFrame

    def __post_init__(self):
        if self.factory != 'CEZ':
            self.factory = 'normal'
    def __str__(self) -> str:
        return str(self.article_no) 

    def __repr__(self) -> str:
        return str(self.article_no)
    
    # def split_str(self, input: str, convert_int = False) -> list:

    #     input = input.split(',')
    #     if convert_int:
    #         return [int(each) for each in input]
    #     return input

    # def create_timeline(self):
    #     if len(self.inbound_date) != 0:
    #         timeline = self.Posting_Date + self.inbound_date
    #         timeline = list(set(timeline))
    #     else:
    #         timeline = list(set(self.Posting_Date))
    #     return sorted(timeline, reverse= True)

    # def create_dict(self, list_key, list_value):
    #     result, value_temp, temp_date = {}, [], 0
    #     for i in range(len(list_key)):
    #         value_temp.append(list_value[i])
    #         if i == len(list_key)-1:
    #             result[list_key[i]] = value_temp
    #         elif list_key[i] != list_key[i+1] and i < len(list_key)-1:
    #             result[list_key[i]] = value_temp
    #             value_temp = []
            
    #     return result

    def create_bar_data(self, initial_value: int):
        movement_accumulated = self.movement.copy().fillna(0)
  
        movement_accumulated = movement_accumulated.groupby(by=['Posting_Date'], as_index= False).agg({
            'article_no': 'first',
            'sum_quantity': 'first',
            'movement_quantity': 'sum',
            'inbound_qnt': 'sum',
            'factory': 'first'
        }).sort_values(by='Posting_Date')
        movement_accumulated.reset_index(drop= True, inplace= True) 
        movement_accumulated.loc[0, 'sum_quantity'] = initial_value
        movement_accumulated['article_no'] = movement_accumulated['article_no'].astype(int)
        for i in range(len(self.movement)):
            if i > 0:
                movement_accumulated.loc[i, 'sum_quantity'] = movement_accumulated.loc[i-1, 'sum_quantity'] + movement_accumulated.loc[i-1, 'movement_quantity'] + movement_accumulated.loc[i-1, 'inbound_qnt']
        return movement_accumulated.sort_values(by='Posting_Date')


def main():
    new = pd.read_excel(input / 'NEW.xlsx', sheet_name= 'new')
    chosen_article = 11902
    selected_row = new[new['ItemCode'] == chosen_article]
    selected_row.fillna(-9999, inplace= True)
    current_article = Article(article_no= selected_row['ItemCode'].values[0],
                            sum_quantity= selected_row['sum_quantity'].values[0],
                            shipments= selected_row['shipments'].values[0],
                            Posting_Date= selected_row['date'].values[0],
                            outbound_qnt= selected_row['outbound_qnt'].values[0]
                            )
    if selected_row['inbound_date'].values[0] != -9999:
        current_article.inbound_date = current_article.split_str(selected_row['inbound_date'].values[0])
        current_article.inbound_qnt = current_article.split_str(selected_row['inbound_quantity'].values[0],convert_int= True)
    bar_data = current_article.create_bar_data()

if __name__ == '__main__':
    main()