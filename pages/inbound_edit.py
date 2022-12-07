import streamlit as st
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from functions import rm_mydb, create_AgGrid
from inbound_functions import box_arrange
from inbound_functions import qnt_box

def update_measurement(df: pd.DataFrame):
    for index, row in df.iterrows():
        update_query_PDB = f"""
            update product_database set 
                carton_length_cm = {row['new_carton_length_cm']},
                carton_width_cm = {row['new_carton_width_cm']},
                carton_height_cm = {row['new_carton_height_cm']},
                qnt_box = {row['new_qnt_box']}
            where article_no = {row['article_no']}
        """
        update_query_PDSA = f"""
            update product_database_storage_assign set 
                carton_length_cm = {row['new_carton_length_cm']},
                carton_width_cm = {row['new_carton_width_cm']},
                carton_height_cm = {row['new_carton_height_cm']},
                qnt_box = {row['new_qnt_box']}
            where article_no = {row['article_no']}
        """
        with rm_mydb.connect() as connection:
            if row['new_carton_length_cm']*row['new_carton_width_cm']*row['new_carton_height_cm'] != 0:
                connection.execute(update_query_PDB)
                connection.execute(update_query_PDSA)


def update_pallet_qty(df: pd.DataFrame):
    for index, row in df.iterrows():
        if np.isnan(row['id']):
            st.warning(f"Error! {row['article_no']} doesn't have a default place yet")    
            continue    
        if row['status'] in ('NEW','READY'):
            max_qty = np.floor(row['sum_box']*1)
        max_qty = row['sum_box']
        if row['size'] == 'Quarter':
            max_qty_WHS = np.floor(max_qty*0.15)
        elif row['size'] == 'Half':
            max_qty_WHS = np.ceil(max_qty*0.4)
        else:
            max_qty_WHS = max_qty
        update_query = f"""
                        UPDATE `Warehouse_StorageUnit_DUS` SET single_quantity_max = {max_qty_WHS*row['qnt_box']}, 
                        single_quantity_threshold = {max_qty_WHS*row['qnt_box']*0.8} where id = {int(row['id'])}"""
        with rm_mydb.connect() as connection:
            connection.execute(update_query)
        # st.write(update_query)

        update_query = f"""UPDATE `product_database_storage_assign` SET Full_qty={max_qty*row['qnt_box']}, Half_qty= {np.ceil(max_qty*0.4)*row['qnt_box']}, 
                    Quarter_qty= {np.floor(max_qty*0.15)*row['qnt_box']}, Storing_way= '{row['way']}', qnt_box = {row['qnt_box']} 
                    where article_no = {row['article_no']}"""
        # st.write(update_query)

        with rm_mydb.connect() as connection:
            connection.execute(update_query)

st.markdown('<h1 style="text-align:center">Inbound Edit</h1>', unsafe_allow_html= True)   

date_input = st.date_input('Container date')

# handle input container file

inbound_upload = st.file_uploader("upload inbound file", accept_multiple_files= False)
try:    
    inbound_upload = qnt_box.rearrange_table(inbound_upload)
except:
    st.error("Can not read input file")
    st.stop()

PDB = qnt_box.get_PDB(article_nos=','.join(map(str,inbound_upload['article_no'].unique())))
inbound_upload = pd.merge(left= inbound_upload, right= PDB, how='left', left_on='article_no', right_on= 'article_no')
format_dict = {
    'carton_length_cm':"{:.1f}",
    'carton_width_cm':"{:.1f}",
    'carton_height_cm':"{:.1f}",
    'gross_weight':"{:.2f}",
}
with st.expander("inbound_summary"):
    st.table(inbound_upload.style.format(format_dict))
    st.download_button(
            label= f'sum_inbound_{date_input}',
            data = inbound_upload.assign(
                new_carton_length_cm= inbound_upload['carton_length_cm'],
                new_carton_width_cm= inbound_upload['carton_width_cm'],
                new_carton_height_cm= inbound_upload['carton_height_cm'],
                new_qnt_box= inbound_upload['qnt_box']
            ).to_csv(index= False).encode('utf-8'),
            file_name= f'sum_inbound_{date_input}.csv',
            mime='csv'
        )
# inbound_upload.to_csv('inbound_test.csv', index= False)
with st.expander(label="Compare data from file with database", expanded= True):
    qnt_box.check_qnt_box(inbound_upload)
    sum_inbound = inbound_upload.groupby(by= ['article_no'], as_index= False).agg({
        'Quantity': 'sum',
        'box_qnt': 'sum', 
        'gross_weight': 'first'
    })
    PO = qnt_box.get_PO(date= date_input)
    file_db = pd.merge(left= PO, right= sum_inbound, how= 'right', left_on= 'article_no', right_on= 'article_no')
    db_file = pd.merge(left= PO, right= sum_inbound, how= 'left', left_on= 'article_no', right_on= 'article_no')
    qnt_box.check_miss_match_qnt(left= file_db, right= db_file)
    WHS = qnt_box.get_WHS(article_nos=','.join(map(str,inbound_upload['article_no'].unique())))
    find_default = pd.merge(left= inbound_upload[['article_no','Quantity','model', 'qnt_box']], right= WHS, how= 'left', left_on= 'article_no', right_on= 'default_article_no')
    st.write("Following articles haven't been assigned to a default place yet")
    st.table(find_default[find_default['default_location'].isna()][['article_no','Quantity','model', 'qnt_box', 'default_article_no']])

# calculate box_arrange

result_arrange, max_arrange = box_arrange.calculate_box_arrange(input_df= inbound_upload)

result_max_only = result_arrange.sort_values(by=['sum_box'], ascending= False).drop_duplicates(['article_no'])
result_max_only = pd.merge(left= inbound_upload[['article_no','model','qnt_box', 'status']], right= result_max_only, how='left', left_on = 'article_no', right_on='article_no')

with st.expander("view arrangement on pallete", expanded= True):
    df_return, selected_row = create_AgGrid(result_max_only, button_key= "max_arrange", selection_mode= True)
    selected_article = int(selected_row[0]['article_no'])

    def highlight_max(df: pd.Series, threshold: float):
        if df.sum_box == threshold:
            return ['background-color: red'] * len(df)
        else:
            return ['background-color: black'] * len(df)

    arrange_selected = pd.merge(left= inbound_upload[inbound_upload['article_no']==selected_article][['article_no','model']],
                                right= result_arrange[result_arrange['article_no'] == selected_article],
                                how='left', left_on = 'article_no', right_on='article_no')
    st.table(arrange_selected.style.apply(highlight_max, threshold= arrange_selected['sum_box'].max(),axis=1))

    st.write(f'Test new dimension and qnt_box of {selected_article}')
    dimension_dict = inbound_upload[inbound_upload['article_no']==selected_article].to_dict(orient='records')[0]
   
    test_form = st.form('test_product_dimension')
    test_length = test_form.text_input(label= f'test carton length of {selected_article}', key= 'length', value= dimension_dict['carton_length_cm'])
    test_width = test_form.text_input(label= f'test carton width of {selected_article}', key= 'width', value= dimension_dict['carton_width_cm'])
    test_height= test_form.text_input(label= f'test carton height of {selected_article}', key= 'height', value= dimension_dict['carton_height_cm'])
    test_submitted = test_form.form_submit_button('Test new dimensions')
    try:
        test_length = float(test_length)
        test_width = float(test_width)
        test_height = float(test_height)
    except:
        st.error("dimension and qnt_box must be numbers")
        st.stop()
    temp_df = pd.DataFrame.from_dict([{
        'article_no': int(selected_article),
        'carton_length_cm': test_length,
        'carton_width_cm': test_width,
        'carton_height_cm': test_height,
    }])
    if test_submitted:
        test_arrange, test_max_arrange = box_arrange.calculate_box_arrange(input_df= temp_df)
        st.table(test_arrange.style.apply(highlight_max, threshold= test_arrange['sum_box'].max(),axis=1))

with st.expander("Update measurements in database", expanded= True):
    result_arrange_update = pd.merge(left= result_max_only[['article_no','sum_box','way','qnt_box','status']], right= WHS[['default_article_no','id','size']], how= 'left', left_on= 'article_no', right_on= 'default_article_no')
    with st.form("submit new measurements"):
        measurement_upload = st.file_uploader("upload measurement file", accept_multiple_files= False)
        file_submitted = st.form_submit_button('Submit file')
        if file_submitted:
            try:
                update_measurement(df= pd.read_csv(measurement_upload))
                update_pallet_qty(df=result_arrange_update)
                st.success("Succesfully updated new measurements in database")
            except:
                st.error("Couldn't update measurement in database. Something's wrong!")
