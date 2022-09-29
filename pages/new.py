import streamlit as st
import pandas as pd 
import sys, os
from pathlib import Path
from functions import create_AgGrid, file_download, get_movement, gen_article, create_plot, rm_mydb
input = Path().cwd().parents[0] / 'excel_files'
import plotly.express as px
from pathlib import Path
from datetime import datetime
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')



TODAY = datetime.today().strftime('%Y-%m-%d')
STARTING_PERIOD = ['2022-01-01', str(TODAY)]

st.header('Overview about NEW articles')


def get_new():
    select_query = f"""
    select distinct WHS.article_no, sum(WHS.quantity_single) as sum_quantity, PDB.model, PDB.status, min(PO.ETA) as first_appearance
    from Warehouse_StorageUnit_DUS WHS
    left join product_database PDB
    on PDB.article_no = WHS.article_no
    left join po_delivery_static PO 
    on PO.article_no = WHS.article_no
    where PDB.status in ('READY','NEW')  and PO.destination = 0 and PO.ship_way = 0 and PO.status = 'arrived'
    group by WHS.article_no
    order by min(PO.ETA);
    """
    NEW_ETA = pd.read_sql_query(select_query, con= rm_mydb)

    select_query = f"""
    select temp.*, GROUP_CONCAT(PO.ETA order by PO.ETA) as inbound_date, GROUP_CONCAT(PO.sum_qnt order by PO.ETA) as inbound_quantity 
    from 
        (select OUTBOUND.ItemCode, INV.sum_quantity, PDB.model, sum(OUTBOUND.Qty) as sum_outbound, count(OUTBOUND.ItemCode) as shipments, GROUP_CONCAT(OUTBOUND.Posting_Date order by OUTBOUND.Posting_Date SEPARATOR ',') as date,
        GROUP_CONCAT(OUTBOUND.Qty order by OUTBOUND.Posting_Date SEPARATOR ',') as outbound_qnt, sum(OUTBOUND.Qty) as outbound_sum, PDB.status, PDB.factory, PDB.moq
        from 
            (SELECT article_no, sum(quantity) as sum_quantity FROM Warehouse_inventory_DUS WHERE 1 group by article_no) as INV 
        right join Warehouse_outbound_DUS_hist OUTBOUND
        on OUTBOUND.ItemCode = INV.article_no
        right join product_database PDB
        on PDB.article_no = INV.article_no
        where OUTBOUND.Document not in ('GoodsReceipt', 'Good-Issue') and OUTBOUND.ItemCode < 18000 and 
        OUTBOUND.Posting_Date >= '{STARTING_PERIOD[0]}' and PDB.status in ('READY','NEW') and INV.sum_quantity != 0
        group by OUTBOUND.ItemCode) as temp
    left join (select article_no, sum(qty) as sum_qnt , ETA from po_delivery_static where ETA between '{STARTING_PERIOD[0]}' and '{STARTING_PERIOD[1]}' and destination = 0 group by ETA, article_no) PO 
    on PO.article_no = temp.ItemCode
    group by temp.ItemCode
    order by temp.shipments, temp.ItemCode;
    """

    NEW_slow = pd.read_sql_query(select_query, con= rm_mydb)
    NEW_slow['ItemCode'] = NEW_slow['ItemCode'].astype(int)
    return  NEW_ETA, NEW_slow
new_eta, new_slow = get_new()

st.markdown('<h3>NEW products with their first appearance date</h3>', unsafe_allow_html= True)
df, selected_row = create_AgGrid(new_eta)
# df1, selected_row1 = create_AgGrid(new, button_key= 1)


st.markdown(file_download(new_eta, name='new'), unsafe_allow_html= True)


if len(selected_row) == 0:
    st.warning("Please select one article no to view")
    st.stop()
else:
    chosen_article_all = int(selected_row[0]['article_no'])

st.markdown("<h3>NEW products that have slow sales record</h3>", unsafe_allow_html= True)

new_slow['criterium'] = (new_slow['sum_outbound']*-1) - (new_slow['moq']/12)
slow_sale_options = [str(row['ItemCode']) + ' ' + row['model'] for index, row in new_slow[new_slow['criterium'] < 0].iterrows()]

view_slow = st.checkbox('View slow selling new products', key= 'view_slow')
if st.session_state['view_slow']: 
    chosen_article_slow = st.selectbox(
                    label= 'Select an article no',
                    options= slow_sale_options
    )
    chosen_article_slow = int(chosen_article_slow.split(' ')[0])
    movement, originated_value = get_movement(start=STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= chosen_article_slow)
else:
    movement, originated_value = get_movement(start=STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= selected_row[0]['article_no'])

current_article = gen_article(movement)
bar_data = current_article.create_bar_data(initial_value= originated_value)
fig_qnt_traceback = create_plot(df= bar_data)
fig_qnt_traceback.update_layout(title= f"<b>Movement of {current_article.article_no} from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</b>"
                                 ,yaxis_title = 'Quantity', hovermode = 'x', xaxis_title = 'date')
st.plotly_chart(fig_qnt_traceback, use_container_width= True)
# current_article = Article(article_no= selected_row['ItemCode'].values[0],
#                         sum_quantity= selected_row['sum_quantity'].values[0],
#                         shipments= selected_row['shipments'].values[0],
#                         outbound_date= selected_row['date'].values[0],
#                         outbound_qnt= selected_row['outbound_qnt'].values[0]
#                         )
# if selected_row['inbound_date'].values[0] != -9999:
#     current_article.inbound_date = current_article.split_str(selected_row['inbound_date'].values[0])
#     current_article.inbound_qnt = current_article.split_str(selected_row['inbound_quantity'].values[0],convert_int= True)
# bar_data = current_article.create_bar_data()
# print(bar_data)
# min_y = min(bar_data['outbound']) - 50
# max_y = max([max(bar_data['inbound']),max(bar_data['sum_quantity'])]) +15
# fig_qnt_traceback = px.bar(
#     bar_data,
#     x= bar_data['date'],
#     y= ['sum_quantity','outbound', 'inbound'],
#     # hover_name= ['sum_quantity','outbound', 'inbound'],
#     text_auto= True,
#     title= f"<b>Movement of {current_article.article_no} </b>"
# )
# fig_qnt_traceback.update_layout(yaxis_title = 'Quantity', hovermode = 'x', xaxis_title = 'date')
# fig_qnt_traceback.update_xaxes(type = 'category')
# fig_qnt_traceback.update_yaxes(range=(min_y, max_y))
# st.plotly_chart(fig_qnt_traceback, use_container_width= True)