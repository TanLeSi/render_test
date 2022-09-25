from datetime import date,datetime
import streamlit as st
import pandas as pd 
from pathlib import Path
direc = Path().cwd()
import sys, calendar, os
sys.path.append(f'{direc.parents[0]}')
from functions import create_AgGrid, file_download

from sqlalchemy import create_engine
from urllib.parse import quote
# from dotenv import load_dotenv
# load_dotenv()
rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)

TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY = str(TODAY)
STARTING_PERIOD = ['2022-01-01', TODAY]
# STARTING_DATE_NO_MOVEMENT = '2022-01-01'

st.header('Items that have no movements in selected period')
from_date, to_date = st.columns(2)
STARTING_PERIOD[0] = from_date.date_input(label= 'Choose from date', value= datetime.strptime(STARTING_PERIOD[0], "%Y-%m-%d"))
STARTING_PERIOD[1] = to_date.date_input(label= 'Choose to date', value= datetime.strptime(STARTING_PERIOD[1], "%Y-%m-%d"))
def get_lastday_prev_month(date_input: datetime):
    currentDate = date_input
    if currentDate.month == 1:
        return date(currentDate.year-1, 12, 31)
    return date(currentDate.year, currentDate.month-1, calendar.monthrange(currentDate.year, currentDate.month-1)[1])

PREVIOUS_START = get_lastday_prev_month(STARTING_PERIOD[0])
PREVIOUS_END = get_lastday_prev_month(STARTING_PERIOD[1])
# ----no_movement
def get_no_movement(start: str, end: str):
    select_query = f"""
    select distinct ItemCode 
    from Warehouse_outbound_DUS_hist outbound
    where outbound.Posting_date between '{start}' and '{end}' and outbound.Document not in('GoodsReceipt', 'Good-Issue') and outbound.ItemCode < 18000
    """
    movement = pd.read_sql_query(select_query, con= rm_mydb)
    movement['ItemCode'] = movement['ItemCode'].astype(int)
    
    select_query = f"""
        select temp.*, PO.ETA as inbound_date, PO.sum_qnt as inbound_quantity
        from 
            (select INV.article_no, PDB.model, sum(INV.quantity) as quantity_sum, PDB.status, PDB.factory, Audit.first_appearance
            from Warehouse_inventory_DUS INV
            left join product_database PDB
            on PDB.article_no = INV.article_no
            left join (select ItemCode, min(Posting_Date) as first_appearance from InventoryAuditReport where 1 group by ItemCode) Audit
            on Audit.ItemCode = INV.article_no
            where INV.article_no not in {tuple(movement['ItemCode'].values)} and INV.quantity != 0 and INV.article_no < 18000 and PDB.status != 'EOL'
            and Audit.first_appearance < '{date(end.year, end.month, 1)}'
            group by INV.article_no) as temp
        left join (select article_no, sum(qty) as sum_qnt , ETA from po_delivery_static where ETA between '{start}' and '{end}' and destination = 0 group by ETA, article_no) PO 
        on PO.article_no = temp.article_no
        where 1
    """
    # print(select_query)
    no_movement = pd.read_sql_query(select_query,con=rm_mydb)
    no_movement[['quantity_sum', 'article_no']] = no_movement[['quantity_sum', 'article_no']].astype(int)
    return no_movement
no_movement = get_no_movement(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1])
st.markdown(f"<h2>Non EOL items that had no movements from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</h2>", unsafe_allow_html= True)
df, selected_row = create_AgGrid(no_movement)
st.markdown(file_download(no_movement, name='no_movement'), unsafe_allow_html= True)

#----- rotation
st.markdown(f"<h2>Comparision with previous period ( from {PREVIOUS_START} to {PREVIOUS_END} )</h2>", unsafe_allow_html= True)
no_movement_prev = get_no_movement(start= PREVIOUS_START,end= PREVIOUS_END)
better_products = [x for x in no_movement_prev['article_no'].unique() if x not in no_movement['article_no'].unique()]
better_df = no_movement_prev[no_movement_prev['article_no'].isin(better_products)][['article_no','quantity_sum', 'model', 'status', 'factory']]
still_products = [x for x in no_movement['article_no'].unique() if x not in better_products and x in no_movement_prev['article_no'].unique()]
still_df = no_movement[no_movement['article_no'].isin(still_products)][['article_no','quantity_sum','model', 'status', 'factory']]
new_no_products = [x for x in no_movement['article_no'].unique() if x not in no_movement_prev['article_no'].unique()]
new_no_df = no_movement[no_movement['article_no'].isin(new_no_products)][['article_no','quantity_sum','model', 'status', 'factory']]


if len(new_no_df) != 0:
    l_column, m_column, r_column = st.columns(3)
    r_column.header('Products that recently have no movement:')
    r_column.write(new_no_df)
    r_column.download_button(
        label= 'Download recently no movement products',
        data = better_df.to_csv(index= False).encode('utf-8'),
        file_name= f'Recently_no_movement_products{str(STARTING_PERIOD[0])},{str(STARTING_PERIOD[1])}.csv',
        mime='csv'
    )
else:
    l_column, m_column = st.columns(2)

l_column.header('Products that haven gotten better:')
l_column.write(better_df)
l_column.download_button(
    label= 'Download better products',
    data = better_df.to_csv(index= False).encode('utf-8'),
    file_name= f'Better_products{str(STARTING_PERIOD[0])},{str(STARTING_PERIOD[1])}.csv',
    mime='csv'
)
m_column.header('Products that still have no movement: ')
if len(still_products) != 0:
    m_column.write(still_df)
    m_column.download_button(
        label= 'Download no change products',
        data = still_df.to_csv(index= False).encode('utf-8'),
        file_name= f'no_change_products{str(STARTING_PERIOD[0])},{str(STARTING_PERIOD[1])}.csv',
        mime='csv'
    )
r_column.header('Products that newly appear in no movement')
if len(new_no_products) != 0:
    r_column.write(new_no_df)
    r_column.download_button(
        label= 'Download new no movement products',
        data = better_df.to_csv(index= False).encode('utf-8'),
        file_name= f'new_no_movement_products{str(STARTING_PERIOD[0])},{str(STARTING_PERIOD[1])}.csv',
        mime='csv'
    )



