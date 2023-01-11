import pandas as pd 
import streamlit as st 
import os,sys
from pathlib import Path
import sqlalchemy
direc = Path().cwd()
sys.path.append(f'{direc.parents[0]}')
from functions import file_download, create_AgGrid, rm_mydb


pd.options.display.float_format = "{:,.2f}".format

COUNTRY_LIST = ['AU', 'CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA', 'USA_ACCECOMM']

st.markdown('<h1 style="text-align:center">Inventory Summary</h1>', unsafe_allow_html= True)



def mod_stock(stock_planner: pd.DataFrame):
    stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
    stock_planner['MOI'] = stock_planner['MOI'].astype(float)
    stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
    stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)
    return stock_planner

def get_stock_planner(country_code: str):
    select_query = f"""
        select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
            PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{country_code}' as country
        from stock_planner_temp_{country_code} stock
        left join product_database PDB 
        on PDB.article_no = stock.article_no
        where 1
    """

    stock_planner = pd.read_sql_query(select_query, con= rm_mydb)
    stock_planner = mod_stock(stock_planner= stock_planner)
    return stock_planner

def create_download_button(df: pd.DataFrame, download_header: str, file_name: str, button_key= 0, selection_mode= False):
    df_return, selected_row_std = create_AgGrid(df, button_key= button_key, selection_mode= selection_mode)
    st.download_button(
            label= f'{download_header}',
            data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
            file_name= f'{file_name}.csv',
            mime='csv'
        )
        
@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id})
def get_info_article(article_no: int):
    stock_all = pd.DataFrame()
    for each_country in COUNTRY_LIST:
        select_query = f"""
            select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
                PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{each_country}' as country
            from stock_planner_temp_{each_country} stock
            left join product_database PDB 
            on PDB.article_no = stock.article_no
            where stock.article_no = {article_no}
        """
        each_stock = pd.read_sql_query(select_query, con= rm_mydb)
        stock_all = pd.concat([stock_all,each_stock], ignore_index= True)
    return mod_stock(stock_all)

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id})
def get_stock_overview(country_list: list[str], MOI_threshold: int, operator: str):
    too_much = pd.DataFrame()
    for each_country in country_list:    
        select_query = f"""
                select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
                    PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{each_country}' as country
                from stock_planner_temp_{each_country} stock
                left join product_database PDB 
                on PDB.article_no = stock.article_no
                where 1
            """
        temp = pd.read_sql_query(select_query, con= rm_mydb)
        st.write(temp)
        temp = mod_stock(temp)
        too_much = pd.concat([too_much, temp])
    country_available = too_much.groupby(['article_no']).agg({'country': lambda x: ', '.join(x)}).rename(columns={'country':'country_available_in'})
    country_available = country_available.assign(
        article_no = country_available.index,
        available_in = country_available.country_available_in.apply(lambda x: x.count(',') + 1)
    ).reset_index(drop= True)
    if operator == 'greater than':
        too_much = too_much[too_much['MOI'] > MOI_threshold]
    elif operator == 'less than':
        too_much = too_much[too_much['MOI'] < MOI_threshold]
    else:
        too_much = too_much[(too_much['MOI'] > MOI_threshold[0]) & (too_much['MOI'] < MOI_threshold[1])]    
        
    result = too_much[['article_no', 'sku', 'status', 'factory', 'country']].groupby(by='article_no').agg({
        'article_no': 'count',
        'sku': 'first',
        'status': 'first',
        'factory': 'first',
        'country': lambda x: ', '.join(x)
    })
    result.rename(columns={'article_no':'count_MOI', 'country': 'country_MOI',}, inplace= True)
    result.insert(0, 'article_no', result.index)
    result = pd.merge(left= result.reset_index(drop= True), right= country_available, how= 'left', left_on='article_no', right_on='article_no', left_index= False, right_index= False)
    return result[['article_no','sku','status','factory','count_MOI', 'country_MOI', 'country_available_in', 'available_in']].sort_values(by= ['count_MOI'], ascending= False)

def test_int_input(input):
    try:
        input = int(input)
    except:
        st.warning('MOI must be a number')
        st.stop()

def get_MOI_article(article_nos: str):
    try:
        article_nos_str = article_nos.split(',')
    except:
        article_nos_str = int(article_nos)
    MOI_article_sum = pd.DataFrame()
    for each_article in article_nos_str:
        article_stock = get_info_article(int(each_article))
        MOI_article_sum = pd.concat([MOI_article_sum, article_stock], ignore_index= True)
    return MOI_article_sum


st.header('Stock overview')
view_MOI = st.sidebar.checkbox(label="View based on MOI", value= True, key= "MOI")
view_markets = st.sidebar.checkbox(label="View based on markets", key= "markets")
if view_MOI:
    with st.expander('Explanation for using comparison'):
        st.write(r"""
            Stock overview shows articles that have MOI greater/less or between given MOI.
        """)
    overview_operator = st.radio(
        label= 'Choose operator',
        options= ('greater than', 'less than', 'between')
    )
    if overview_operator == 'between':
        MOI_under = st.text_input('Please type in MOI under threshold',value= 1000)
        MOI_upper = st.text_input('Please type in MOI upper threshold', value= 1000)
        # test_int_input(MOI_under)
        # test_int_input(MOI_upper)
        MOI_input = [int(MOI_under), int(MOI_upper)]
    else:
        MOI_input = st.text_input('Please type in MOI threshold', value= 1000)
        # test_int_input(MOI_input)
        MOI_input = int(MOI_input)
    st.write("Choose an article to view it across all markets")
    stock_overview = get_stock_overview(country_list= COUNTRY_LIST, MOI_threshold= MOI_input, operator= overview_operator)
    df_return, selected_row_std = create_AgGrid(stock_overview, button_key= "Overview", selection_mode= True)
    st.download_button(
            label= f'Download overview MOI_{MOI_input}',
            data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
            file_name= f'overview_MOI_{MOI_input}.csv',
            mime='csv'
        )
    if selected_row_std[0]:
        selected_article = selected_row_std[0]['article_no']
        create_download_button(df= get_MOI_article(selected_article),
                            download_header= f"Download {selected_article} across all markets",
                            file_name= f"{selected_article} across all markets",
                            button_key= "MOI_article")
                            
if view_markets:
    view_type = st.radio(
            label= 'Choose view type:',
            options= ('by market', 'by article_no')
        )

    with st.expander('Explanation for each view type'):
        st.write(r"""
            This function provides two ways of viewing MOI of different articles. 
            1. View by market:\
                Enter market to view MOI of all articles in that market. The articles are divide into 4 Category: 
                * STD, NEW, CEZ and EOL
            2. View by article_no:\
                Enter article_no to view MOI of te given article_no across all markets.
        """)

    if view_type == 'by market':
        st.write(f"available markets: {', '.join(COUNTRY_LIST)} or type ALL to view all markets")
        country_code = st.text_input("Please type market/partnered warehouse in", 'ES')
        if country_code.lower() == 'all':
            stock_planner_all = pd.DataFrame()
            for each_country in COUNTRY_LIST:
                temp = get_stock_planner(country_code= each_country)
                stock_planner_all = pd.concat([stock_planner_all, temp], ignore_index= True)
            create_download_button(df=stock_planner_all,
                            download_header=f"Download Amazon Inventory for all markets",
                            file_name=f"AMZ_INV_all_markets",
                            button_key=f"AMZ_INV_all")
            st.stop()
        if country_code not in COUNTRY_LIST:
            st.warning(f'{country_code} is not acceptable as a market')
            st.stop()
        stock_planner = get_stock_planner(country_code= country_code)

        # for STD products
        create_download_button(df=stock_planner[(stock_planner['status'] == 'STD') & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
                                download_header=f"Download STD {country_code}",
                                file_name=f"STD_of_{country_code}",
                                button_key=f"std_{country_code}")


        # for NEW products
        create_download_button(df=stock_planner[(stock_planner['status'].isin(['NEW', 'READY'])) & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
                                download_header=f"Download NEW {country_code}",
                                file_name=f"NEW_of_{country_code}",
                                button_key=f"new_{country_code}")


        # for CEZ products
        create_download_button(df= stock_planner[stock_planner['factory'].isin(['CEZ'])].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
                                download_header=f"Download CEZ {country_code}",
                                file_name=f"CEZ_of_{country_code}",
                                button_key=f"cez_{country_code}")

        # for EOL products
        create_download_button(df= stock_planner[stock_planner['status'] == 'EOL'].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
                                download_header=f"Download EOL {country_code}",
                                file_name=f"EOL_of_{country_code}",
                                button_key=f"eol_{country_code}")

    elif view_type == 'by article_no':
        article_no_input = st.text_input("Please type article_no in", '11525')
        # try:
        #     article_no_input = int(article_no_input)
        # except:
        #     st.write("Article_no must be a number!")
        #     st.stop()
        create_download_button(df= get_MOI_article(article_nos=article_no_input),
                            download_header= f"Download {article_no_input} across all markets",
                            file_name= f"{article_no_input} across all markets",
                            button_key= "individual_articles")

