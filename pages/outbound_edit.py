import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime
sys.path.append(Path.cwd().parents[0])
from functions import rm_mydb

ADD = 'add cancel order'
BRING_BACK = 'bring back canceled or old order'
def get_order(order_number: int):
    select_query = f"select * from Warehouse_outbound_DUS_temp where Document_Number = {order_number}"
    pending_order = pd.read_sql_query(select_query, con= rm_mydb)
    return pending_order[['Document_Number', 'ItemCode', 'ItemName','Qty', 'Posting_Date', 'loading_status']]

def get_status_order(order_number: int):
    select_query = f"select * from Warehouse_outbound_DUS_hist where Document_Number = {order_number}"
    shipped_order = pd.read_sql_query(select_query, con= rm_mydb)
    shipped_order['Qty'] = shipped_order['Qty'].astype(int)
    select_query = f"select * from Warehouse_outbound_DUS_temp where Document_Number = {order_number}"
    pending_order = pd.read_sql_query(select_query, con= rm_mydb)
    pending_order['Qty'] = pending_order['Qty'].astype(int)
    return shipped_order[['Document_Number','Document', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date', 'loading_status']], pending_order[['Document_Number','Document', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date', 'loading_status']]

def get_order_audit(order_number: int):        
    select_query = f"select * from InventoryAuditReport where Document_Number = {order_number}"
    audit_order = pd.read_sql_query(select_query, con= rm_mydb)
    if order_number < 300000:
        posting_dates = audit_order.sort_values('Posting_Date', ascending= False).Posting_Date.unique()
        return audit_order[audit_order['Posting_Date'] == posting_dates[0]][['Document_Number', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date']]
    audit_order['Qty'] = audit_order['Qty'].astype(int)
    return audit_order[['Document_Number', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date']]

def add_order(order_number: int, purpose: str):
    select_query = f"select * from outbound_edit_WHS where Document_Number = {order_number} and action = '{purpose}'"
    temp  = pd.read_sql_query(select_query,con= rm_mydb)
    if not temp.shape[0]:
        with rm_mydb.connect() as connection:
            insert_query = f"INSERT INTO outbound_edit_WHS (Document_Number,date_edit, action) values ({order_number}, '{datetime.today().strftime('%Y-%m-%d %H:%M:%S')}', '{purpose}')"
            connection.execute(insert_query)


def update_order(order_number:int, purpose_search: str, purpose_new: str):
    select_query = f"select * from outbound_edit_WHS where Document_Number = {order_number} and action = '{purpose_search}'"
    temp  = pd.read_sql_query(select_query,con= rm_mydb)
    if not temp.shape[0]:
        return 0
    with rm_mydb.connect() as connection:
        insert_query = f"update outbound_edit_WHS set date_edit = '{datetime.today().strftime('%Y-%m-%d %H:%M:%S')}', action= '{purpose_new}' where Document_Number = {order_number} and action = '{purpose_search}'"
        connection.execute(insert_query)
        return 1
        

st.markdown('<h1 style="text-align:center">Outbound Edit</h1>', unsafe_allow_html= True)   
options = st.radio(label="Choose an option", options=[ADD, BRING_BACK])
order_number = st.text_input("Please type in cancelled order number:")
try: 
    order_number = int(order_number)
except:
    st.warning("order number must be a number")
    st.stop()
shipped_order, pending_order = get_status_order(order_number)
if options == ADD:
    if shipped_order.shape[0] and (shipped_order['Document'].values[0] == pending_order['Document'].values[0]): 
        st.header('Shipped order')
        st.warning("This order was already shipped")
        st.write(shipped_order)
        st.stop()
    st.header('Pending order')
    st.write(pending_order)
    if st.button("Cancel this order"):
        if update_order(order_number, purpose_search= BRING_BACK, purpose_new= ADD):
            st.success('Successfully added cancelled order')
        else:
            try:
                add_order(order_number, purpose= ADD)
                st.success('Successfully bring back order')
            except:
                st.error("Something's wrong")

elif options == BRING_BACK:
    if pending_order.shape[0]:  
            st.info("This order is already available, no need to bring it back")
            st.write(pending_order)
            st.stop()
    elif shipped_order.shape[0]:
        st.warning("This order is already shipped. Cannot bring back anymore. Please check")
        st.write(shipped_order)
        st.stop()
    st.write(get_order_audit(order_number))
    if st.button("Bring back this order"):
        if update_order(order_number, purpose_search= ADD, purpose_new= BRING_BACK):
            st.success('Successfully bring back order')
        else:
            try:
                add_order(order_number, purpose= BRING_BACK)
                st.success('Successfully bring back order')
            except:
                st.error("Something's wrong")