import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime
sys.path.append(Path.cwd().parents[0])
from functions import rm_mydb
from inbound_functions import qnt_box

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

st.table(inbound_upload.style.format(format_dict))
inbound_upload.to_csv('inbound_test.csv', index= False)
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

# 