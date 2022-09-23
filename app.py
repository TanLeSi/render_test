import streamlit as st
import os
import mysql.connector
from sqlalchemy import create_engine
import pandas as pd
st.header("Test")

rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':' + rm_password +  '@' + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False) 

a = pd.read_sql_query("""
    select * from InventoryAuditReport where Posting_Date = '2022-09-23'
""", con = rm_mydb)

st.write(a.head())