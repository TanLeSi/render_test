import streamlit as st
import numpy as np
import pandas as pd 
import sys, os
from pathlib import Path
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')
pd.options.mode.chained_assignment = None
import plotly.express as px
from plotly.subplots import make_subplots
from article import Article
from datetime import datetime, timedelta
from functions import get_movement, gen_article
from sqlalchemy import create_engine
from urllib.parse import quote
# from dotenv import load_dotenv
# load_dotenv()
rm_port = os.getenv('port')
rm_dbname = os.getenv('dbname')
rm_host = os.getenv('host')
rm_user = os.getenv('user')
rm_password = os.getenv('password')
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':%s@' %quote(rm_password) + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False)


TODAY = datetime.today().strftime('%Y-%m-%d')
TODAY = str(TODAY)
STARTING_PERIOD = ['2022-04-01', '2022-06-30']
st.header('View movement of selected items')
from_date, to_date = st.columns(2)
STARTING_PERIOD[0] = from_date.date_input(label= 'Choose from date', value= datetime.strptime(STARTING_PERIOD[0], "%Y-%m-%d"))
STARTING_PERIOD[1] = to_date.date_input(label= 'Choose to date', value= datetime.strptime(TODAY, "%Y-%m-%d"))
article_no_input = st.text_input('Please type article no in', '11525')


movement, originated_value = get_movement(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= int(article_no_input))
specified_article = gen_article(movement)
specified_bar_data = specified_article.create_bar_data(initial_value= originated_value)
min_y = min(specified_bar_data['movement_quantity']) - 50
max_y = max([max(specified_bar_data['inbound_qnt']),max(specified_bar_data['sum_quantity'])]) +15
fig_specified_qnt_traceback = px.bar(
    specified_bar_data,
    x= specified_bar_data['Posting_Date'],
    y= ['sum_quantity','movement_quantity', 'inbound_qnt'],
    # hover_name= ['sum_quantity','outbound', 'inbound'],
    text_auto= True,
    title= f"<b>Movement of {specified_article.article_no} from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</b>"
)
fig_specified_qnt_traceback.update_layout(yaxis_title = 'Quantity', hovermode = 'x', xaxis_title = 'date')
fig_specified_qnt_traceback.update_xaxes(type = 'category')
fig_specified_qnt_traceback.update_yaxes(range=(min_y, max_y))
st.plotly_chart(fig_specified_qnt_traceback, use_container_width= True)


def get_movement_spec(start: str, end: str, article_no: tuple):
    select_query = f"""
        select Document_Number
        from InventoryAuditReport 
        where Posting_Date between '{start}' and '{end}' and Warehouse in ('40549DUS', 'EbayDUS') and ItemCode in {article_no}
        group by Document_Number, ItemCode
        having sum(Qty) = 0
    """
    DUS_Ebay_transfer = pd.read_sql_query(select_query, con=rm_mydb)
    select_query = f"""
        (select audit.ItemCode as article_no, INV.sum_quantity, audit.Posting_Date, audit.Document_Number, audit.Document, sum(audit.Qty) as movement_quantity,
        PDB.model,SUBSTRING_INDEX(PDB.model, ' ', 2) as model_layout, PDB.status, PDB.factory, PDB.moq,  group_concat(distinct audit.Warehouse order by audit.Warehouse ) as Warehouse_concat
        from InventoryAuditReport audit
        left join product_database PDB
        on PDB.article_no = audit.ItemCode
        left join (select article_no, sum(quantity) as sum_quantity from Warehouse_inventory_DUS where article_no in {article_no} group by article_no) as INV
        on INV.article_no = audit.ItemCode
        where audit.Warehouse in ('40549DUS', 'EbayDUS') and audit.Qty < 0 and audit.ItemCode in {article_no} and audit.Posting_Date between '{start}' and '{TODAY}'
        or (audit.ItemCode in {article_no} and audit.Document = 'GoodsReceiptPO' and audit.Posting_Date between '{start}' and '{TODAY}')
        group by audit.Document_Number, audit.ItemCode
        order by audit.ItemCode, audit.Posting_Date) 
    """
    print(select_query)
    movement = pd.read_sql_query(select_query, con= rm_mydb)
    movement = movement[~movement['Document_Number'].isin(DUS_Ebay_transfer['Document_Number'].values)]
    movement['article_no'] = movement['article_no'].astype(int)
    if len(movement) == 0:
        return pd.DataFrame()
    return movement


def prepare_data(movement: pd.DataFrame, end_date: str):
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
    movement['sum_quantity'].fillna(0, inplace= True)
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
    movement = movement[movement['Posting_Date'] <= str(end_date)]
    movement = pd.concat([movement, movement.iloc[-1:]], ignore_index= True)
    movement.loc[len(movement)-1, ['Posting_Date', 'movement_quantity', 'inbound_qnt']] = TODAY, 0, 0
    movement = pd.concat([movement, movement.iloc[-1:]], ignore_index= True)
    movement.loc[len(movement)-1, ['sum_quantity','Posting_Date', 'movement_quantity', 'inbound_qnt']] = originated_quantity, datetime.strftime((datetime.strptime(min(movement['Posting_Date'].values), "%Y-%m-%d") - timedelta(days= 1)),"%Y-%m-%d"), 0, 0
    movement.fillna(0).sort_values(by='Posting_Date', ascending= False, inplace= True)
    return movement, originated_quantity


def create_mult_plot_data(article_no_list: list, annotation_ref: int, df: pd.DataFrame):
    if annotation_ref == 1:
        annotation_ref = ''
    total_movement = pd.DataFrame(columns= ['article_no', 'sum_quantity', 'movement_quanitity', 'inbound_qnt', 'model', 'factory'])
    line_legend = []
    for each in article_no_list:
        print(each)
        each_movement = df[df['article_no'] == each]
        each_movement, each_originated_value = prepare_data(each_movement, STARTING_PERIOD[1])
        each_specified_article = gen_article(each_movement)
        each_specified_bar_data = each_movement.copy().fillna(0)  
        each_specified_bar_data = each_specified_bar_data.groupby(by=['Posting_Date'], as_index= False).agg({
            'article_no': 'first',
            'sum_quantity': 'first',
            'movement_quantity': 'sum',
            'inbound_qnt': 'sum',
            'model': 'first',
            'factory': 'first'
        }).sort_values(by='Posting_Date')
        each_specified_bar_data.reset_index(drop= True, inplace= True) 
        each_specified_bar_data.loc[0, 'sum_quantity'] = each_originated_value
        each_specified_bar_data['article_no'] = each_specified_bar_data['article_no'].astype(int)
        for i in range(len(each_specified_bar_data)):
            if i>0:
                each_specified_bar_data.loc[i, 'sum_quantity'] = each_specified_bar_data.loc[i-1, 'sum_quantity'] + each_specified_bar_data.loc[i, 'movement_quantity'] + each_specified_bar_data.loc[i, 'inbound_qnt']
        each_specified_bar_data.sort_values(by='Posting_Date', inplace= True)
        total_movement = pd.concat([total_movement, each_specified_bar_data], ignore_index= True)
        line_legend.append(dict(
            x= each_specified_bar_data.loc[each_specified_bar_data['sum_quantity'].idxmax(), 'Posting_Date'],
            y= max(each_specified_bar_data['sum_quantity'].values),
            xanchor= 'auto',
            yanchor= 'auto',
            text= str(each_specified_article.article_no) + ' ' + each_specified_article.model, 
            font= {
                'family': 'Arial',
                'size' : 14,
            },
            showarrow= True,
            xref = 'x' + str(annotation_ref),
            yref = 'y' + str(annotation_ref)
        ))
    total_movement =  total_movement[(~total_movement['article_no'].isna())]
    return total_movement, line_legend


def create_subplot(col: int, layout: list, total_movement: pd.DataFrame):
    subplot_fig = make_subplots(
        rows = int(np.ceil(len(layout)/col)),
        cols= col,
        vertical_spacing= 0.03,
        horizontal_spacing= 0.1,
        subplot_titles= layout,
        # print_grid= True
    )
    counter, row, annotation_counter = 0,1,1
    annotations_sum = []
    for each_layout in layout:
        if counter >= col:
            row += 1
            counter = 1
        else:    
            counter += 1
        layout_movement, line_annotation = create_mult_plot_data(
            article_no_list= total_movement.loc[total_movement['model_layout'] == each_layout, 'article_no'].unique(),
            annotation_ref= annotation_counter,
            df= total_movement)
        fig = px.line(
                layout_movement,
                x='Posting_Date',
                y = 'sum_quantity',
                color= 'article_no',
                markers = True,
                title= f"<b>Movement of all {each_layout} from {STARTING_PERIOD[0]} to {STARTING_PERIOD[1]}</b>",
            )            
        for each_data in fig['data']:
            subplot_fig.add_trace(each_data, row= row, col= counter)
        annotation_counter += 1
        annotations_sum += line_annotation
    for each in annotations_sum:
        subplot_fig.add_annotation(
            x= each['x'],
            y= each['y'],
            xanchor= each['xanchor'],
            yanchor= each['yanchor'],
            text= each['text'],
            font= each['font'],
            showarrow= each['showarrow'],
            xref= each['xref'],
            yref= each['yref']
        )
    subplot_fig.update_yaxes(title_text = 'Pcs')
    if len(layout) > 6:
        subplot_fig.update_layout(height= 2000)
    else:
        subplot_fig.update_layout(height= 1000)
    return subplot_fig

compare = st.checkbox(label= 'Compare movement of differents articles')
with st.expander('Explanation for using comparison'):
    st.write(r"""
        This function provides two ways of comparing movements of different articles. 
        1. Compare by article number:\
            Enter article numbers to view their movement in the selected period. The article numbers must be seperated by comma. For example:
            * 11525,11528,11354
        2. Compare by name:\
            There are 3 fields that can be filled in (at least one field must be filled in before clicking submit):
            1. Name:\
                Enter 1 product name at a time. For example: PERIBOARD-512
            2. Layout:\
                Enter 1 layout at a time. For example: US
            3. Color:\
                Enter 1 color at a time. For example: B
    """)
if compare: 
    compare_type = st.radio(
        label= 'Choose compare type:',
        options= ('by article_no', 'by name')
    )
    if compare_type == 'by article_no':
        compare_input = st.text_input('Please type article_no or name in')
        try:
            input_article_nos = [int(each) for each in compare_input.replace(' ','').split(',')]
        except: 
            st.warning('article_no must be a number')
            st.stop()       
        total_movement = get_movement_spec(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= tuple(input_article_nos))
        total_subplot = create_subplot(col= 3, layout= total_movement['model_layout'].unique(), total_movement= total_movement)
        st.plotly_chart(total_subplot, use_container_width= True)

    elif compare_type == 'by name':
        keywords = {'name': '', 'layout': '', 'color': ''}
        with st.form('product_name'):
            keywords['name'] = st.text_input(label= 'name', key= 'name')
            keywords['layout'] = st.text_input(label= 'layout', key= 'layout')
            keywords['color'] = st.text_input(label= 'color', key= 'color')
            submitted = st.form_submit_button('Submit')
            if not submitted:
                st.stop()
        if all([len(each) == 0 for each in list(keywords.values())]):
            st.stop()
        select_query = f"select distinct article_no, SUBSTRING_INDEX(model, ' ', 2) as model_layout, model, factory from product_database PDB where STATUS in ('STD','NEW') "
        for key, value in keywords.items():
            if key == 'color' and len(value) != 0:
                select_query += f" and model regexp '{value}$' "
            elif len(value) != 0:
                select_query += f" and model regexp '{value}' "

        converted_article_no = pd.read_sql_query(select_query, con= rm_mydb)
        converted_article_no['article_no'] = converted_article_no['article_no'].astype(int)
        print(converted_article_no)
        movement = get_movement_spec(start= STARTING_PERIOD[0], end= STARTING_PERIOD[1], article_no= tuple(converted_article_no['article_no'].unique()))
        CEZ_movement = movement[movement['factory'] == 'CEZ']
        CEZ_layout = CEZ_movement['model_layout'].unique()
        normal_movement= movement[movement['factory'] != 'CEZ']
        normal_layout = normal_movement['model_layout'].unique()
        print(normal_movement)
        if len(CEZ_movement) != 0:
            CEZ_subplot = create_subplot(col= 3, layout= CEZ_layout, total_movement= CEZ_movement)
            with st.expander(f'Movement of CEZ {keywords}'):
                st.plotly_chart(CEZ_subplot, use_container_width= True)            
        if len(normal_movement) != 0:
            normal_subplot = create_subplot(col= 2, layout= normal_layout, total_movement= normal_movement)
            with st.expander(f'Movement of normal {keywords}'):
                st.plotly_chart(normal_subplot, use_container_width= True)

