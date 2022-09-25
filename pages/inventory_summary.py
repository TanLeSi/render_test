from weakref import ProxyType
import pandas as pd 
import streamlit as st 
import os,sys
from urllib.parse import quote
from sqlalchemy import create_engine
from pathlib import Path
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')
from functions import file_download, create_AgGrid, gen_article, get_movement, create_plot
# from dotenv import load_dotenv
# load_dotenv()
rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)

pd.options.display.float_format = "{:,.2f}".format

COUNTRY_LIST = ['AU', 'CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA', 'USA_ACCECOMM']

st.markdown('<h1 style="text-align:center">Inventory Summary</h1>', unsafe_allow_html= True)



def get_stock_planner(country_code: str):
    select_query = f"""
        select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
            PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA
        from stock_planner_temp_{country_code} stock
        left join product_database PDB 
        on PDB.article_no = stock.article_no
        where 1
    """
    stock_planner = pd.read_sql_query(select_query, con= rm_mydb)
    stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
    stock_planner['MOI'] = stock_planner['MOI'].astype(float)
    stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
    stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)

    return stock_planner


def create_download_button(df: pd.DataFrame, product_type: str, country: str, button_key= 0):
    st.header(f"{product_type} products")
    df_return, selected_row_std = create_AgGrid(df, button_key= button_key)
    print(df)
    st.download_button(
            label= f'Download {product_type}',
            data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
            file_name= f'{product_type}_inventory{country}.csv',
            mime='csv'
        )

view_type = st.radio(
        label= 'Choose view type:',
        options= ('by market', 'by article_no')
    )
if view_type == 'by market':
    st.write(f"available markets: {', '.join(COUNTRY_LIST)}")
    country_code = st.text_input("Please type market/partnered warehouse in", 'ES')

    stock_planner = get_stock_planner(country_code= country_code)
    df_return, selected_row_std = create_AgGrid(stock_planner[(stock_planner['status'] == 'STD') & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False), button_key= 0)
    # df_return, selected_row_std = create_AgGrid(stock_planner[(stock_planner['status'].isin(['NEW', 'READY'])) & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False), button_key= 1)
    # df_return, selected_row_std = create_AgGrid(stock_planner[stock_planner['factory'].isin(['CEZ'])].sort_values(by= 'MOI', ascending= False), button_key= 2)
    # df_return, selected_row_std = create_AgGrid(stock_planner[stock_planner['status'] == 'EOL'].sort_values(by= 'MOI', ascending= False), button_key= 3)
#     sys.exit()
#     # for STD products
#     create_download_button(df=stock_planner[(stock_planner['status'] == 'STD') & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False),
#                             product_type= 'STD', country= country_code)


#     # for NEW products
#     create_download_button(df=stock_planner[(stock_planner['status'].isin(['NEW', 'READY'])) & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False),
#                             product_type= 'NEW', country= country_code, button_key= 1)


#     # for CEZ products
#     create_download_button(df= stock_planner[stock_planner['factory'].isin(['CEZ'])].sort_values(by= 'MOI', ascending= False),
#                             product_type= 'CEZ', country= country_code, button_key= 2)

#     # for EOL products
#     create_download_button(df= stock_planner[stock_planner['status'] == 'EOL'].sort_values(by= 'MOI', ascending= False),
#                             product_type= 'EOL', country= country_code, button_key= 3)

# elif view_type == 'by article_no':
#     pass
