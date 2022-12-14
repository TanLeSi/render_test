import streamlit as st
st.set_page_config(page_title= 'Inventory Report',
                    layout= 'wide'
)
import os, pendulum, calendar
import plotly.express as px
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime, date, timedelta
from functions import create_AgGrid, file_download, rm_mydb
from dotenv import load_dotenv
load_dotenv()


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
STARTING_PERIOD = ['2022-07-01', TODAY]
BOX_PALLETE = 26


def get_month(current_year: int):
    result = {}
    for i in range(1,13):
        if i<10:
            temp_date = f"{current_year}-0{i}-01"
        else:
            temp_date = f"{current_year}-{i}-01"
        temp_date = pendulum.parse(temp_date)
        result[f"{calendar.month_name[i]}"] = [temp_date.start_of("month").to_datetime_string().split(" ")[0],temp_date.end_of("month").to_datetime_string().split(" ")[0]]
    return result

MONTH = get_month(current_year= pendulum.today().year)

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

# OUTBOUND, avrg_outbound = get_outbound_percent()

# outbound_percent = pd.DataFrame(columns=['date', 'CEZ', 'NEW', 'SUM'])
# counter = 0
# for each in OUTBOUND['Posting_Date'].unique():
#     new_percent = OUTBOUND[(OUTBOUND['status'] == 'NEW') & (OUTBOUND['Posting_Date'] == each)]['Qty'].sum()*-1
#     # new_percent = new_percent / OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum() * 100
#     cez_percent = OUTBOUND[(OUTBOUND['factory'] == 'CEZ') & (OUTBOUND['Posting_Date'] == each)]['Qty'].sum()*-1
#     # cez_percent = cez_percent / OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum() * 100
#     if cez_percent < 0.01:
#         cez_percent = 0
#     if OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum()*-1 != 0:
#         outbound_percent.loc[counter, 'CEZ'] = cez_percent
#         outbound_percent.loc[counter, 'NEW'] = new_percent
#         outbound_percent.loc[counter, 'date'] = each
#         outbound_percent.loc[counter, 'SUM'] = OUTBOUND[OUTBOUND['Posting_Date'] == each]['Qty'].sum()*-1
#         counter += 1


def get_capacity():
    capacity = pd.read_sql('Warehouse_capacity_daily', con= rm_mydb)
    return capacity

capacity = get_capacity()
capacity['EOL_occupied_units'] = capacity['total_units'] - capacity['normal_units'] - capacity['cez_occupied_units']
# CEZ_occupation = capacity.loc[capacity['date'] == TODAY,'cez_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100
# NEW_occupation = capacity.loc[capacity['date'] == TODAY,'new_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100
# EOL_occupation = capacity.loc[capacity['date'] == TODAY,'EOL_occupied_units'].values[0]/capacity.loc[capacity['date'] == TODAY,'total_units'].values[0]*100

# st.markdown(f"<h2> CEZ takes {round(CEZ_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)
# st.markdown(f"<h2> CEZ takes {round(outbound_percent['CEZ'].sum()/outbound_percent['SUM'].sum()*100,2)}% from total sales</h2>", unsafe_allow_html= True)
# st.markdown(f"<h2> NEW takes {round(NEW_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)
# st.markdown(f"<h2> NEW takes {round(outbound_percent['NEW'].sum()/outbound_percent['SUM'].sum()*100,2)}% from total sales</h2>", unsafe_allow_html= True)
# st.markdown(f"<h2> EOL takes {round(EOL_occupation,2)}% from total warehouse capacity</h2>", unsafe_allow_html= True)






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


# fig_outbound = px.line(
#     outbound_percent,
#     x= outbound_percent['date'],
#     y= ['SUM'],
#     # hover_name= ['sum_quantity','outbound', 'inbound'],
#     markers= True,
#     title= f"<b>Outbound daily</b>"
# )
# fig_outbound.update_layout(yaxis_title = 'Pieces', hovermode = 'x', xaxis_title = 'date')
# st.plotly_chart(fig_outbound, use_container_width= True)

st.markdown(f"<h1>Summary of inbound</h1>", unsafe_allow_html= True)
month_index = int(str(TODAY).split('-')[1])
selected_months = st.multiselect(
    label= 'Select time period',
    options= list(MONTH.keys()),
    default= list(MONTH.keys())[month_index-1]
)

columns = ['ItemCode', 'model', 'factory']
columns.extend([each for each in selected_months])
result = pd.DataFrame(columns= columns)
for each_month in selected_months:    
    temp_result = pd.DataFrame(columns= columns)
    temp_date = MONTH[f"{each_month}"]
    select_query = f"""
        SELECT audit.ItemCode, PDB.model, PDB.factory, cast(sum(Qty) as UNSIGNED) as {each_month}
        FROM `InventoryAuditReport` audit
        left join product_database PDB
        on PDB.article_no = audit.ItemCode
        where audit.Document = 'GoodsReceiptPO' and audit.Warehouse = '40549DUS'
        and audit.Posting_Date between '{MONTH[f"{each_month}"][0]}' and '{MONTH[f"{each_month}"][1]}'
        group by audit.ItemCode;
    """
    # print(select_query)
    temp = pd.read_sql_query(select_query, con=rm_mydb)
    temp_result[['ItemCode', 'model', 'factory', f"{each_month}"]] = temp
    result = pd.concat([result,temp_result], ignore_index= True)

agg_dict = {each:'first' if each in ['model','factory'] else 'sum' for each in columns[1:]}
result = result.groupby(by= ['ItemCode'], as_index= False).agg(agg_dict)
# st.write(result)
df, selected_row = create_AgGrid(result) #update_trigger=GridUpdateMode.GRID_CHANGED)
file_name = str(selected_months).replace('[','').replace(']','').replace("'",'')
st.markdown(file_download(result, name=f"inbound_sum_for {file_name}"), unsafe_allow_html= True)