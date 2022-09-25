from cgi import test
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



def mod_stock(stock_planner: pd.DataFrame):
    stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
    stock_planner['MOI'] = stock_planner['MOI'].astype(float)
    stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
    stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)
    return stock_planner

def get_stock_planner(country_code: str):
    select_query = f"""
        select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
            PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{country_code}' as country
        from stock_planner_temp_{country_code} stock
        left join product_database PDB 
        on PDB.article_no = stock.article_no
        where 1
    """
    stock_planner = pd.read_sql_query(select_query, con= rm_mydb)
    stock_planner = mod_stock(stock_planner= stock_planner)
    return stock_planner

def create_download_button(df: pd.DataFrame, product_type: str, country: str, button_key= 0):
    st.header(f"{product_type} products")
    df_return, selected_row_std = create_AgGrid(df, button_key= button_key)
    st.download_button(
            label= f'Download {product_type}',
            data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
            file_name= f'{product_type}_inventory_{country}.csv',
            mime='csv'
        )

def get_info_article(article_no: int):
    stock_all = pd.DataFrame()
    for each_country in COUNTRY_LIST:
        select_query = f"""
            select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
                PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{each_country}' as country
            from stock_planner_temp_{each_country} stock
            left join product_database PDB 
            on PDB.article_no = stock.article_no
            where stock.article_no = {article_no}
        """
        each_stock = pd.read_sql_query(select_query, con= rm_mydb)
        stock_all = pd.concat([stock_all,each_stock], ignore_index= True)
    return mod_stock(stock_all)


def get_stock_overview(country_list: list[str], MOI_threshold: int, operator: str):
    too_much = pd.DataFrame()
    for each_country in country_list:    
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
    if operator == 'greater than':
        too_much = too_much[too_much['MOI'] > MOI_threshold]
    elif operator == 'less than':
        too_much = too_much[too_much['MOI'] > MOI_threshold]
    else:
        too_much = too_much[(too_much['MOI'] > MOI_threshold[0]) & (too_much['MOI'] < MOI_threshold[1])]    
        
    result = too_much[['article_no', 'sku', 'status', 'factory', 'country']].groupby(by='article_no').agg({
        'article_no': 'count',
        'sku': 'first',
        'status': 'first',
        'factory': 'first',
        'country': lambda x: ', '.join(x)
    })
    result.rename(columns={'article_no':'count'}, inplace= True)
    result.insert(0, 'article_no', result.index)
    return result.sort_values(by= ['count'], ascending= False)

def test_int_input(input):
    try:
        input = int(input)
    except:
        st.warning('MOI must be a number')
        st.stop()

st.header('Stock overview')
overview_operator = st.radio(
    label= 'Choose operator',
    options= ('greater than', 'less than', 'between')
)
if overview_operator == 'between':
    MOI_under = st.text_input('Please type in MOI under threshold')
    MOI_upper = st.text_input('Please type in MOI upper threshold')
    test_int_input(MOI_under)
    test_int_input(MOI_upper)
    MOI_input = [int(MOI_under), int(MOI_upper)]
else:
    MOI_input = st.text_input('Please type in MOI threshold')
    test_int_input(MOI_input)
    MOI_input = int(MOI_input)

stock_overview = get_stock_overview(country_list= COUNTRY_LIST, MOI_threshold= MOI_input, operator= overview_operator)
df_return, selected_row_std = create_AgGrid(stock_overview, button_key= 'Overview')
st.download_button(
        label= f'Download overview MOI_{MOI_input}',
        data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
        file_name= f'overview_MOI_{MOI_input}.csv',
        mime='csv'
    )


view_type = st.radio(
        label= 'Choose view type:',
        options= ('by market', 'by article_no')
    )
if view_type == 'by market':
    st.write(f"available markets: {', '.join(COUNTRY_LIST)}")
    country_code = st.text_input("Please type market/partnered warehouse in", 'ES')
    if country_code not in COUNTRY_LIST:
        st.warning(f'{country_code} is not acceptable as a market')
        st.stop()
    stock_planner = get_stock_planner(country_code= country_code)

    # for STD products
    create_download_button(df=stock_planner[(stock_planner['status'] == 'STD') & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False),
                            product_type= 'STD', country= country_code)


    # for NEW products
    create_download_button(df=stock_planner[(stock_planner['status'].isin(['NEW', 'READY'])) & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False),
                            product_type= 'NEW', country= country_code, button_key= 1)


    # for CEZ products
    create_download_button(df= stock_planner[stock_planner['factory'].isin(['CEZ'])].sort_values(by= 'MOI', ascending= False),
                            product_type= 'CEZ', country= country_code, button_key= 2)

    # for EOL products
    create_download_button(df= stock_planner[stock_planner['status'] == 'EOL'].sort_values(by= 'MOI', ascending= False),
                            product_type= 'EOL', country= country_code, button_key= 3)

elif view_type == 'by article_no':
    article_no_input = st.text_input("Please type article_no in", '11525')
    try:
        article_no_input = int(article_no_input)
    except:
        st.write("Article_no must be a number!")
    article_stock = get_info_article(article_no_input)
    st.header(f"{article_no_input} across all markets")
    df_return, selected_row_std = create_AgGrid(article_stock)
    st.download_button(
            label= f'Download {article_no_input} across all markets',
            data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
            file_name= f'{article_no_input}_inventory_all_markets.csv',
            mime='csv'
        )