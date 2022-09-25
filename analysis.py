from audioop import tomono
import pandas as pd 
import streamlit as st 
import os,sys
from urllib.parse import quote
from sqlalchemy import create_engine

from dotenv import load_dotenv
load_dotenv()
rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)


COUNTRY_LIST = ['AU', 'CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA', 'USA_ACCECOMM']

def mod_stock(stock_planner: pd.DataFrame):
    stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
    stock_planner['MOI'] = stock_planner['MOI'].astype(float)
    stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
    stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)
    return stock_planner

too_much = pd.DataFrame()
for each_country in COUNTRY_LIST:
    
    select_query = f"""
            select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
                PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{each_country}' as country
            from stock_planner_temp_{each_country} stock
            left join product_database PDB 
            on PDB.article_no = stock.article_no
            where 1
        """
    temp = pd.read_sql_query(select_query, con= rm_mydb)
    temp = mod_stock(temp)
    too_much = pd.concat([too_much, temp])

too_much = too_much[too_much['MOI'] > 1000]
result = too_much[['article_no', 'sku', 'status', 'factory', 'country']].groupby(by='article_no').agg({
    'article_no': 'count',
    'sku': 'first',
    'status': 'first',
    'factory': 'first',
    'country': lambda x: ', '.join(x)
})
result.rename(columns={'article_no':'count'}, inplace= True)
print(result.sort_values(by= 'count', ascending= False))
# a = too_much['article_no'].value_counts()
# b = pd.DataFrame(columns= ['article_no', 'count'])
# b['article_no'] = a.index
# b['count'] = a.values
# b.to_excel('too_much.xlsx',index= False)