import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime
sys.path.append(Path.cwd().parents[0])
from functions import rm_mydb
import xlsxwriter as xw
from io import BytesIO
import re

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
        return audit_order[audit_order['Posting_Date'] == posting_dates[0]][['Document_Number', 'Document', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date']]
    audit_order['Qty'] = audit_order['Qty'].astype(int)
    return audit_order[['Document_Number', 'Document', 'ItemCode', 'ItemName', 'Qty', 'Posting_Date']]

def add_order(order_number: int, purpose: str, order: pd.DataFrame):
    select_query = f"select * from outbound_edit_WHS where Document_Number = {order_number} and action = '{purpose}'"
    temp  = pd.read_sql_query(select_query,con= rm_mydb)
    document = order['Document'].unique()[0]
    if not temp.shape[0]:
        with rm_mydb.connect() as connection:
            insert_query = f"INSERT INTO outbound_edit_WHS (Document_Number,Document,date_edit, action) values ({order_number},'{document}', '{datetime.today().strftime('%Y-%m-%d %H:%M:%S')}', '{purpose}')"
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

def edit_ebay_control_list(file_input):
    temp = str(file_input.getvalue())
    result = re.search('from date,(.*),to date', temp)
    date = result.group(1)
    ebay_check_list = pd.read_csv(file_input, skiprows=1).fillna(0)
    ebay_check_list['mix'] = ebay_check_list['Palette_Box'].duplicated(keep= False).reset_index(drop= True)
    ebay_check_list['date'] = date
    rows = ebay_check_list.shape[0]+1
    columns = ebay_check_list.shape[1]
    output = BytesIO()
    workbook = xw.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    for i in range(rows):
        for j in range(columns):
            if i == 0:
                worksheet.write(i,j,list(ebay_check_list.columns)[j])
                continue
            elif i<rows-1:
                mix = ebay_check_list.loc[ebay_check_list.index == i-1, 'mix']
                qty = ebay_check_list.loc[ebay_check_list.index == i-1, 'Qty_diff'].values[0]
                if mix.values[0] == True or qty > 1:
                    cell_format = {'bg_color':'red'}
                    cell_format_qty = {'bg_color':'red','font_size':14}
                    if j == 4:
                        worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format_qty))
                    else:
                        worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format))
                else:
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j])
    workbook.close()
    return output, date

def edit_ebay_pickup_list(file_input):
    temp = str(file_input.getvalue())
    result = re.search('from date,(.*),to date', temp)
    date = result.group(1)
    ebay_check_list = pd.read_csv(file_input, skiprows=1).fillna(0)
    ebay_check_list['date'] = date
    rows = ebay_check_list.shape[0]+1
    columns = ebay_check_list.shape[1]
    output = BytesIO()
    workbook = xw.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    for i in range(rows):
        for j in range(columns):
            if i == 0:
                worksheet.write(i,j,list(ebay_check_list.columns)[j])
                continue
            elif i<rows-1:
                qty = ebay_check_list.loc[ebay_check_list.index == i-1, 'Qty_diff'].values[0]
                if qty > 1:
                    cell_format_qty = {'bg_color':'red','font_size':14}
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format_qty))                    
                else:
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j])
    workbook.close()
    return output, date

st.markdown('<h1 style="text-align:center">Outbound Edit</h1>', unsafe_allow_html= True)   

left_column, right_column = st.columns(2)

with left_column:
    st.header("Edit ebay control list")
    ebay_control_upload = st.file_uploader("Upload ebay control list", accept_multiple_files= False)
    try:
        file_output, date_output = edit_ebay_control_list(file_input= ebay_control_upload)
        st.download_button(
            label="Download new Ebay control list",
            data=file_output.getvalue(),
            file_name=f"Ebay_control_list_{date_output}.xlsx",
            mime="application/vnd.ms-excel"
        )
    except:
        pass

with right_column:
    st.header("Edit ebay pickup list")
    ebay_pickup_upload = st.file_uploader("Upload ebay pickup list", accept_multiple_files= False)
    try:
        file_output, date_output = edit_ebay_pickup_list(file_input= ebay_pickup_upload)
        st.download_button(
            label="Download new Ebay pickup list",
            data=file_output.getvalue(),
            file_name=f"Ebay_pickup_list_{date_output}.xlsx",
            mime="application/vnd.ms-excel"
        )
    except:
        pass

options = st.radio(label="Choose an option", options=[ADD, BRING_BACK])
order_number = st.text_input("Please type in cancelled order number:")
try: 
    order_number = int(order_number)
except:
    st.warning("order number must be a number")
    st.stop()
shipped_order, pending_order = get_status_order(order_number)
if options == ADD:
    if shipped_order.shape[0] and pending_order.shape[0]: 
        if (shipped_order['Document'].values[0] == pending_order['Document'].values[0]): 
            st.header('Shipped order')
            st.warning("This order was already shipped")
            st.write(shipped_order)
            st.stop()
    st.header('Pending order')
    st.write(pending_order)
    if pending_order.shape[0]:
        if st.button("Cancel this order"):
            if update_order(order_number, purpose_search= BRING_BACK, purpose_new= ADD):
                st.success('Successfully added cancelled order')
            else:
                try:
                    add_order(order_number, purpose= ADD, order= pending_order)
                    st.success('Successfully added cancelled order')
                except:
                    st.error("Something's wrong")

elif options == BRING_BACK:
    audit_orders = get_order_audit(order_number)
    if pending_order.shape[0]:  
            st.info("This order is already available, no need to bring it back")
            st.write(pending_order)
            st.stop()
    elif shipped_order.shape[0]:
        if (shipped_order.Document.values[0] ==audit_orders.Document.values[0]):
            st.warning("This order is already shipped. Cannot bring back anymore. Please check")
            st.write(shipped_order)
            st.stop()
    st.write(audit_orders)
    if st.button("Bring back this order"):
        if update_order(order_number, purpose_search= ADD, purpose_new= BRING_BACK):
            st.success('Successfully bring back order')
        else:
            try:
                add_order(order_number, purpose= BRING_BACK, order= audit_orders)
                st.success('Successfully bring back order')
            except:
                st.error("Something's wrong")

