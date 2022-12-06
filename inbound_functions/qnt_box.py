import sys
import pandas as pd
import numpy as np
from pathlib import Path
sys.path.append(Path.cwd().parents[1])
from functions import rm_mydb
import streamlit as st
print(Path.cwd())

BOX_QNT_COLUMN = 'CIN NO.&CIN'
ARTICLE_NO_COLUMN = 'ITEM NO.& DESCRIPTION'
QUANTITY_COLUMN = 'QUANTITY'
GROSS_WEIGHT = 'GROSS WEIGHT\n(KG)'
# CONTAINER_DATE = sys.argv[2]

def find_start_index(df: pd.DataFrame):
    for index, row in df.iterrows():
        first_cell = df.iloc[index,0]
        try:
            first_cell.startswith('CIN')
        except:
            continue 
        if first_cell.startswith('CIN'):
            return index + 1
    return -1

def filter_table(df:pd.DataFrame, start_index: int):
    table = df.iloc[start_index-1:len(df),:]
    table.columns = table.iloc[0]
    # print(table)
    table = table[[BOX_QNT_COLUMN, ARTICLE_NO_COLUMN, QUANTITY_COLUMN,GROSS_WEIGHT]]
    table = table.iloc[1:len(table),:]
    table = table[~((table[QUANTITY_COLUMN].isna()) |(table[ARTICLE_NO_COLUMN].isna())) ]
    table[ARTICLE_NO_COLUMN] = table[ARTICLE_NO_COLUMN].astype(int)
    # table = pd.merge(left= table, right= PDB[['article_no', 'qnt_box']], how= 'left', left_on= ARTICLE_NO_COLUMN, right_on= 'article_no')
    table.reset_index(drop=True, inplace= True)
    return table

@st.cache
def rearrange_table(df: pd.DataFrame):
    df = pd.read_excel(df,sheet_name= None)
    sum_inbound = pd.DataFrame(columns=['box_qnt', 'article_no', 'Quantity'])
    for name, sheet in df.items():
        start_index = find_start_index(sheet)
        if start_index < 0:
            print(f"Couldn't find start index for {name}")
        else:
            table = filter_table(df= sheet, start_index= start_index)
        table.rename(columns={BOX_QNT_COLUMN: "box_qnt", ARTICLE_NO_COLUMN: "article_no", QUANTITY_COLUMN: "Quantity", GROSS_WEIGHT: "gross_weight"}, inplace= True)
        sum_inbound = pd.concat([sum_inbound, table], ignore_index= True)

    # sum_inbound = pd.concat([sum_inbound, sum_inbound_each], ignore_index= True)
    sum_inbound['article_no'] = sum_inbound['article_no'].astype(int)
    return sum_inbound


@st.cache
def get_PDB(article_nos: str):
    select_query = f"""
        select article_no, model, status, qnt_box, carton_length_cm, carton_width_cm, carton_height_cm
        from product_database where article_no in ({article_nos})
    """
    PDB = pd.read_sql_query(select_query, con= rm_mydb )
    return PDB

def get_PO(date: str):
    select_query = f"""
        select PO.article_no, sum(Qty) as db_qty, PO.ETA, PDB.status, PDB.model, PDB.qnt_box as PDB_qnt_box, PDSA.qnt_box as PDSA_qnt_box, PDB.weight, WHS.default_article_no 
        from po_delivery_static PO
        left join product_database PDB
        on PDB.article_no = PO.article_no
        left join product_database_storage_assign PDSA
        on PDSA.article_no = PO.article_no
        left join Warehouse_StorageUnit_DUS WHS
        on WHS.default_article_no = PO.article_no
        where PO.ETA = '{date}'
        group by PO.article_no 
        order by PO.article_no
    """
    PO = pd.read_sql_query(select_query, con= rm_mydb)
    PO['article_no'] = PO['article_no'].astype(int)
    PO['db_qty'] = PO['db_qty'].astype(int)
    return PO

def get_WHS(article_nos: str):
    select_query = f"""
        select default_article_no, concat(section,number,'-',level,'-',side) as default_location, id, size
        from Warehouse_StorageUnit_DUS where default_article_no in ({article_nos})
    """
    WHS = pd.read_sql_query(select_query, con= rm_mydb )
    return WHS

def check_qnt_box(df: pd.DataFrame):
    for index, row in df.iterrows():
        if row['box_qnt'] == 1:
            continue
        if int(row['article_no']) > 18000:
            continue
        calculated_qnt_box = np.floor(row['Quantity']/row['box_qnt'])
        df.loc[index,'calculated_qnt_box'] = calculated_qnt_box
    # df['calculated_qnt_box'] = np.floor(df['Quantity']/df['box_qnt'])
    miss_match_qnt_box = df.query("calculated_qnt_box != qnt_box")
    if len(miss_match_qnt_box) == 0:
        st.write("All qnt_box from file and PDB match \n")
    else:
        st.write('Missmatch qnt_box:')
        st.table(miss_match_qnt_box)

def check_miss_match_qnt(right: pd.DataFrame, left: pd.DataFrame):
    right_error = right.query('db_qty != Quantity')
    left_error = left.query('db_qty != Quantity')
    result = pd.concat([left_error,right_error], ignore_index= True)
    if result.shape[0]:
        st.write("Missmatch inbound quantities")
        st.table(result[['article_no', 'db_qty', 'ETA','Quantity']].sort_values('article_no'))
    else:
        st.write("Quantities from file matches with database match\n")





