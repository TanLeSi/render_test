import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from article import Article
import base64, os
import pandas as pd 
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()

@st.cache(allow_output_mutation=True)
def create_db_connection():
    rm_port = os.getenv('port')
    rm_dbname = os.getenv('dbname')
    rm_host = os.getenv('host')
    rm_user = os.getenv('user')
    rm_password = os.getenv('password')
    return create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)

rm_mydb = create_db_connection()
TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY = str(TODAY)


def create_AgGrid(df, button_key= 0, selection_mode= False, update_trigger= GridUpdateMode.SELECTION_CHANGED):
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_pagination(enabled= True, paginationAutoPageSize= False, paginationPageSize= 20)
    # gd.configure_side_bar()
    if not selection_mode:
        gd.configure_selection("disabled")
    else:
        sel_mode = st.radio('Selection Type', options= ['single'], index= 0, key= f"{button_key} + 'sel'")
        gd.configure_selection(selection_mode= sel_mode, use_checkbox= True, pre_selected_rows= [0])

    gridoptions = gd.build()
    grid_table = AgGrid(df, gridOptions= gridoptions,
                        update_mode= update_trigger,
                        theme= 'alpine',
                        fit_columns_on_grid_load= True,
                        key= button_key,
                        reload_data= True,
                        )
    sel_row = grid_table['selected_rows']
    return grid_table, sel_row

def file_download(df: pd.DataFrame, name: str):
    csv = df.to_csv(index= False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f"<a href= 'data:file/csv;base64,{b64}' download='{name}.csv'> Download CSV File </a>"
    return href

def gen_article(movement: pd.DataFrame):
    current_article = Article(article_no= movement['article_no'].values[0],
                            sum_quantity= movement['sum_quantity'].values[0],
                            moq= movement['moq'].values[0],
                            model= movement['model'].values[0],
                            factory= movement['factory'].values[0],
                            movement= movement
                            )
    return current_article

def get_movement(start: str, end: str, article_no: int):
    VERSION = {
        '11635': 4120, 
        '11674': 500,
        '11713': 500,
        '11525': 1292,
        '11411': 2000,
        '11517': 1960,
        '12013': 54,
        '11533': 86
    }
    select_query = f"""
        select Document_Number
        from InventoryAuditReport 
        where Posting_Date between '{start}' and '{end}' and Warehouse in ('40549DUS', 'EbayDUS') and ItemCode = {article_no}
        group by Document_Number, ItemCode
        having sum(Qty) = 0
    """
    DUS_Ebay_transfer = pd.read_sql_query(select_query, con=rm_mydb)
    select_query = f"""
        (select audit.ItemCode as article_no, INV.sum_quantity, audit.Posting_Date, audit.Document_Number, audit.Document,
        sum(audit.Qty) as movement_quantity, PDB.model, PDB.status, PDB.factory, PDB.moq, group_concat(distinct audit.Warehouse order by audit.Warehouse ) as Warehouse_concat
        from InventoryAuditReport audit
        left join product_database PDB
        on PDB.article_no = audit.ItemCode
        left join (select article_no, sum(quantity) as sum_quantity from Warehouse_inventory_DUS where article_no = {article_no} group by article_no) as INV
        on INV.article_no = audit.ItemCode
        where (audit.Warehouse in ('40549DUS', 'EbayDUS') and audit.Qty < 0 and audit.ItemCode = {article_no} and audit.Posting_Date between '{start}' and '{end}')
        or (audit.ItemCode = {article_no} and audit.Document = 'GoodsReceiptPO' and audit.Posting_Date between '{start}' and '{end}')
        group by audit.Document_Number, audit.ItemCode
        order by audit.Posting_Date) 
    """
    # print(select_query)
    movement = pd.read_sql_query(select_query, con= rm_mydb)
    movement = movement[~movement['Document_Number'].isin(DUS_Ebay_transfer['Document_Number'].values)]
    if len(movement) == 0:
        return pd.DataFrame(), 0
    movement['article_no'] = movement['article_no'].astype(int)
    movement['inbound_qnt'] = 0
    for index, row in movement.iterrows():
        if row['Document'] == 'GoodsReceiptPO':
            movement.loc[index, 'inbound_qnt'] = row['movement_quantity']
            movement.loc[index, 'movement_quantity'] = 0
        try: 
            temp_qnt = VERSION[str(row['article_no'])]
            movement.loc[index, 'sum_quantity'] += temp_qnt
        except:
            pass
    originated_quantity = movement['movement_quantity'].sum()*-1 + movement['sum_quantity'].values[0] -  movement['inbound_qnt'].sum()
    movement = movement[movement['Posting_Date'] <= str(end)]
    movement = pd.concat([movement, movement.iloc[-1:]], ignore_index= True)
    movement.loc[len(movement)-1, ['Posting_Date', 'movement_quantity', 'inbound_qnt']] = TODAY, 0, 0
    movement = pd.concat([movement, movement.iloc[-1:]], ignore_index= True)
    movement.loc[len(movement)-1, ['sum_quantity','Posting_Date', 'movement_quantity', 'inbound_qnt']] = originated_quantity, datetime.strftime((datetime.strptime(min(movement['Posting_Date'].values), "%Y-%m-%d") - timedelta(days= 1)),"%Y-%m-%d"), 0, 0
    movement.fillna(0).sort_values(by='Posting_Date', ascending= False, inplace= True)
    return movement, originated_quantity

def create_plot(df: pd.DataFrame):
    min_y = min(df['movement_quantity']) - 50
    max_y = max([max(df['inbound_qnt']),max(df['sum_quantity'])]) +15
    fig_qnt_traceback = px.bar(
    df,
    x= df['Posting_Date'],
    y= ['sum_quantity','movement_quantity', 'inbound_qnt'],
    # hover_name= ['sum_quantity','outbound', 'inbound'],
    text_auto= True,
    )
    fig_qnt_traceback.update_xaxes(type = 'category')
    fig_qnt_traceback.update_yaxes(range=(min_y, max_y))
    return fig_qnt_traceback