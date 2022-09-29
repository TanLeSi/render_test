import streamlit as st
import pandas as pd 
import sys, os
from pathlib import Path
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')
from functions import create_AgGrid, file_download, rm_mydb
import mysql.connector
from sqlalchemy import create_engine
from datetime import date
from urllib.parse import quote
# from dotenv import load_dotenv
# load_dotenv()



TODAY = date.today()
TODAY = str(TODAY.strftime('%Y-%m-%d'))
st.header('Forgotten Items')

# ----forgotten_items
def get_forgotten_items():
    select_query = f"""
    select INV_.*, PDB.model, PDB.qnt_box, PDB.status, PDB.factory
    from 
        (select INV.article_no, sum(INV.quantity) as sum_quantity from Warehouse_inventory_DUS INV where INV.article_no < 18000 GROUP BY INV.article_no) as INV_
    left join product_database PDB
    on PDB.article_no = INV_.article_no
    left join 
        (select * from po_delivery_static where ETA >= '{TODAY}' ) as PO
    on PO.article_no = INV_.article_no
    where INV_.sum_quantity < PDB.qnt_box and INV_.sum_quantity != 0  and PO.ETA is null
    ORDER BY `INV_`.`sum_quantity` ASC;
"""

    forgotten_items = pd.read_sql_query(select_query, con= rm_mydb)
    forgotten_items.sort_values(by=['sum_quantity', 'article_no'], inplace= True)
    return forgotten_items

forgotten_items = get_forgotten_items()
st.write(f"""Items that have less than 1 box quantity. Usually only 1 piece left. 
            They don't take much space in WHS but keeping track of them requires a lot of man power""")
df, selected_row = create_AgGrid(forgotten_items)


st.markdown(file_download(forgotten_items, name='forgotten_items'), unsafe_allow_html= True)