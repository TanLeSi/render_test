import streamlit as st
import pandas as pd 
import sys, os
import plotly.express as px
from datetime import datetime
from pathlib import Path
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')
from functions import file_download, create_AgGrid, gen_article, get_movement, create_plot, rm_mydb

TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY = str(TODAY)
STARTING_PERIOD = ['2022-04-01', '2022-06-30']
st.header('Slow selling items')
from_date, to_date = st.columns(2)
STARTING_PERIOD[0] = from_date.date_input(label= 'Choose from date', value= datetime.strptime(STARTING_PERIOD[0], "%Y-%m-%d"))
STARTING_PERIOD[1] = to_date.date_input(label= 'Choose to date', value= datetime.strptime(TODAY, "%Y-%m-%d"))
CRITERIUM = st.selectbox(label='Choose criterium',options= ('MOQ/12', 'MOQ/6'))
st.write(f"Criterium: items that have outbound quantity in between {STARTING_PERIOD[0]} and {STARTING_PERIOD[1]} less than their MOQ/{CRITERIUM.split('/')[-1]}")

# ----slow_sale

def get_slow_sale(start: str, end: str):
    select_query = f"""
    select temp.* from 
        (select OUTBOUND.ItemCode, INV.sum_quantity, PDB.model, sum(OUTBOUND.Qty) as outbound_sum, PDB.status, PDB.factory, PDB.moq
        from 
            (SELECT article_no, sum(quantity) as sum_quantity FROM Warehouse_inventory_DUS WHERE 1 group by article_no) as INV 
        right join Warehouse_outbound_DUS_hist OUTBOUND
        on OUTBOUND.ItemCode = INV.article_no
        right join product_database PDB
        on PDB.article_no = INV.article_no
        where OUTBOUND.Document not in ('GoodsReceipt', 'Good-Issue') and OUTBOUND.ItemCode < 18000 and OUTBOUND.Posting_Date >= '{start}' and PDB.status != 'EOL' and INV.sum_quantity != 0
        group by OUTBOUND.ItemCode) as temp
    where (temp.outbound_sum*-1) < (temp.moq/{CRITERIUM.split('/')[-1]})
"""
    slow_sale_general = pd.read_sql_query(select_query, con= rm_mydb)
    slow_sale_general['ItemCode'] = slow_sale_general['ItemCode'].astype(int)
    slow_sale_general['fullfill_percent'] = (slow_sale_general['outbound_sum']*-1 / 3 ) / (slow_sale_general['moq']/int(CRITERIUM.split('/')[-1])) * 100
    return slow_sale_general.fillna(-9999)

slow_sale = get_slow_sale(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1])
df, selected_row = create_AgGrid(slow_sale[['ItemCode', 'sum_quantity', 'model', 'moq', 'fullfill_percent']].round({'fullfill_percent':2}), selection_mode= True)
st.markdown(file_download(slow_sale, name='slow_sale'), unsafe_allow_html= True)
try:
    chosen_article = int(selected_row[0]['ItemCode'])
except:
    st.warning("Please select one article no to view")
    st.stop()


movement, originated_value = get_movement(start=STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= int(chosen_article))
current_article = gen_article(movement)
bar_data = current_article.create_bar_data(initial_value= originated_value)
fig_qnt_traceback = create_plot(df= bar_data)
fig_qnt_traceback.update_layout(title= f"<b>Movement of {current_article.article_no} from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</b>"
                                 ,yaxis_title = 'Quantity', hovermode = 'x', xaxis_title = 'date')
st.plotly_chart(fig_qnt_traceback, use_container_width= True)


st.markdown(f'<h3>View {current_article.article_no} from specified period </h3>', unsafe_allow_html= True)
specified_from, specified_to = st.columns(2)
STARTING_PERIOD[0] = specified_from.date_input(label= 'Choose from date', value= STARTING_PERIOD[0], key= 'specified_from')
STARTING_PERIOD[1] = specified_to.date_input(label= 'Choose to date',value= STARTING_PERIOD[1], key = 'specified_to')

specified_movement, specified_originated_value = get_movement(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no=current_article.article_no)
specified_article = gen_article(movement= specified_movement)
specified_bar_data = specified_article.create_bar_data(initial_value= specified_originated_value)

fig_specified_qnt_traceback = create_plot(df= specified_bar_data)
fig_specified_qnt_traceback.update_layout(
        title= f"<b>Movement of {current_article.article_no} from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</b>",
        yaxis_title = 'Quantity', hovermode = 'x', xaxis_title = 'date')
st.plotly_chart(fig_specified_qnt_traceback, use_container_width= True)

