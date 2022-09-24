import streamlit as st
import os
import plotly.express as px
from sqlalchemy import create_engine
import pandas as pd
from urllib.parse import quote
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from functions import create_AgGrid, file_download
load_dotenv()

rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)

TODAY = date.today()
if TODAY.weekday() == 6:
    TIME_DELTA = timedelta(days= 2)
elif TODAY.weekday() == 0:
    TIME_DELTA = timedelta(days= 3)
else:
    TIME_DELTA = timedelta(days= 1)
TODAY = datetime.strftime(date.today() - TIME_DELTA,'%Y-%m-%d')

LAST_WEEK = date.today()-TIME_DELTA
TODAY = str(TODAY)
LAST_WEEK = str(LAST_WEEK.strftime('%Y-%m-%d'))
STARTING_PERIOD = ['2022-07-01', '2022-07-31']
BOX_PALLETE = 26
MONTH = {
    'January': ['2022-01-01', '2022-01-31'],
    'February': ['2022-02-01', '2022-02-28'],
    'March': ['2022-03-01', '2022-03-31'],
    'April': ['2022-04-01', '2022-04-30'],
    'May': ['2022-05-01', '2022-05-31'],
    'June': ['2022-06-01', '2022-06-30'],
    'Juli': ['2022-07-01', '2022-07-31'],
    'August': ['2022-08-01', '2022-08-31'],
    'September': ['2022-09-01', '2022-09-30'],
    'October': ['2022-10-01', '2022-10-31'],
    'November': ['2022-11-01', '2022-11-30'],
    'October': ['2022-12-01', '2022-12-31'],
}
st.set_page_config(page_title= 'Inventory Report',
                    layout= 'wide'
)

st.markdown('<h1 style="text-align:center">Inventory Report </h1>', unsafe_allow_html= True)


def get_outbound_percent():
    select_query = f"""
    select Outbound.*, PDB.status, PDB.factory
    from Warehouse_outbound_DUS_hist Outbound
    left join product_database PDB
    on PDB.article_no = Outbound.ItemCode
    where Outbound.Posting_Date between '{STARTING_PERIOD[0]}' and '{STARTING_PERIOD[1]}' and Document not in ('Good-Issue', 'GoodsReceipt')
    """
    OUTBOUND = pd.read_sql_query(select_query,con= rm_mydb)    
    outbound_sum = OUTBOUND['Qty'].sum()*-1
    return OUTBOUND, round(outbound_sum/BOX_PALLETE/5,2)

OUTBOUND, avrg_outbound = get_outbound_percent()

outbound_percent = pd.DataFrame(columns=['date', 'CEZ', 'NEW', 'SUM'])
counter = 0
for each in OUTBOUND['Posting_Date'].unique():
    new_percent = OUTBOUND[(OUTBOUND['status'] == 'NEW') & (OUTBOUND['Posting_Date'] == each)]['Qty'].sum()*-1
    # new_percent = new_percent / OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum() * 100
    cez_percent = OUTBOUND[(OUTBOUND['factory'] == 'CEZ') & (OUTBOUND['Posting_Date'] == each)]['Qty'].sum()*-1
    # cez_percent = cez_percent / OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum() * 100
    if cez_percent < 0.01:
        cez_percent = 0
    if OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum()*-1 != 0:
        outbound_percent.loc[counter, 'CEZ'] = cez_percent
        outbound_percent.loc[counter, 'NEW'] = new_percent
        outbound_percent.loc[counter, 'date'] = each
        outbound_percent.loc[counter, 'SUM'] = OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum()*-1
        counter += 1


def get_capacity():
    capacity = pd.read_sql('Warehouse_capacity_daily', con= rm_mydb)
    return capacity

capacity = get_capacity()
capacity['EOL_occupied_units'] = capacity['total_units'] - capacity['normal_units'] - capacity['cez_occupied_units']
CEZ_occupation = capacity.loc[capacity['date'] == TODAY,'cez_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100
NEW_occupation = capacity.loc[capacity['date'] == TODAY,'new_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100
EOL_occupation = capacity.loc[capacity['date'] == TODAY,'EOL_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100

st.markdown(f"<h2> CEZ takes {round(CEZ_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)
st.markdown(f"<h2> CEZ takes {round(outbound_percent['CEZ'].sum()/outbound_percent['SUM'].sum()*100,2)}% from total sales</h2>", unsafe_allow_html= True)
st.markdown(f"<h2> NEW takes {round(NEW_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)
st.markdown(f"<h2> NEW takes {round(outbound_percent['NEW'].sum()/outbound_percent['SUM'].sum()*100,2)}% from total sales</h2>", unsafe_allow_html= True)
st.markdown(f"<h2> EOL takes {round(EOL_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)

def get_inbound() -> float:
    select_query = f"""
    select distinct ETA, sum(Qty) as sum_inbound from po_delivery_static where ETA >= TODAY and destination = 0 and ship_way = 0
    group by ETA
    """
    SUM_inbound = pd.read_sql_query(select_query, con= rm_mydb)
    convert_to_pallete = SUM_inbound['sum_inbound'].values[0] / BOX_PALLETE
    return round(convert_to_pallete,2)




capacity['occupied_percent'] = capacity['total_occupied_units'] / capacity['normal_units']*100
capacity.round({'occupied_percent':2})
fig_capacity = px.line(
    capacity,
    x= capacity['date'],
    y= ['occupied_percent'],
    # hover_name= ['sum_quantity','outbound', 'inbound'],
    markers= True,
    title= f"<b>Capacity daily</b>"
)
fig_capacity.update_layout(yaxis_title = 'Capacity percent', hovermode = 'x', xaxis_title = 'date')
# fig_capacity.update_yaxes(range=(0, 100))
st.plotly_chart(fig_capacity, use_container_width= True)


fig_outbound = px.line(
    outbound_percent,
    x= outbound_percent['date'],
    y= ['SUM'],
    # hover_name= ['sum_quantity','outbound', 'inbound'],
    markers= True,
    title= f"<b>Outbound daily</b>"
)
fig_outbound.update_layout(yaxis_title = 'Pieces', hovermode = 'x', xaxis_title = 'date')
st.plotly_chart(fig_outbound, use_container_width= True)

st.markdown(f"<h1>Summary of inbound</h1>", unsafe_allow_html= True)
month_index = int(str(TODAY).split('-')[1])
selected_months = st.multiselect(
    label= 'Select time period',
    options= list(MONTH.keys()),
    default= list(MONTH.keys())[month_index-2:month_index]
)

columns = ['ItemCode', 'model']
columns.extend([each for each in selected_months])
result = pd.DataFrame(columns= columns)
for each_month in selected_months:    
    temp_result = pd.DataFrame(columns= columns)
    select_query = f"""
        SELECT ItemCode, model, sum(Qty) as {each_month}
        FROM `InventoryAuditReport` audit
        left join product_database PDB
        on PDB.article_no = audit.ItemCode
        where Document = 'GoodsReceiptPO' and audit.Warehouse = '40549DUS'
        and Posting_Date between '{MONTH[f"{each_month}"][0]}' and '{MONTH[f"{each_month}"][1]}'
        group by ItemCode;
    """
    # print(select_query)
    temp = pd.read_sql_query(select_query, con=rm_mydb)
    temp_result[['ItemCode', 'model', f"{each_month}"]] = temp
    result = pd.concat([result,temp_result], ignore_index= True)

agg_dict = {each:'first' if each == 'model' else 'sum' for each in columns[1:]}
result = result.groupby(by= ['ItemCode'], as_index= False).agg(agg_dict)
df, selected_row = create_AgGrid(result)
file_name = str(selected_months).replace('[','').replace(']','').replace("'",'')
st.markdown(file_download(result, name=f"inbound_sum_for {file_name}"), unsafe_allow_html= True)