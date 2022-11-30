from box import Box
from pallette import Palette
from Sub_Palette import SubPallete
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd


import config_py
import mysql.connector
from sqlalchemy import create_engine
rm_port = config_py.port
rm_dbname = config_py.dbname
rm_host = config_py.host
rm_user = config_py.user
rm_password = config_py.password
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':' + rm_password +  '@' + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False) 

mydb = mysql.connector.connect(
    host = rm_host,
    database = rm_dbname,
    user = rm_user,
    password = rm_password,
    port = rm_port
)
mycursor = mydb.cursor()
PDB = pd.read_sql_query('select * from product_database where 1',con=rm_mydb)
PDSA = pd.read_sql_query('select * from product_database_storage_assign where 1',con=rm_mydb)
WHS = pd.read_sql_query('select * from Warehouse_StorageUnit_DUS where 1',con=rm_mydb)
PUFFER = 0

# length = 53.8
# width = 42
# height = 30

# for each in range(11523,11529):
#     updatequery = f'UPDATE `product_database_storage_assign` SET `carton_length_cm`={length}, `carton_width_cm` ={width}, `carton_height_cm` = {height} where article_no = {each}'
#     mycursor.execute(updatequery)
#     mydb.commit()
# import sys
# sys.exit()
# PDB = PDB[(PDB['qnt_box'] != 0) & (PDB['carton_length_cm'] != 0)]
# carton_measurement = PDB[['article_no','carton_length_cm', 'carton_width_cm', 'carton_height_cm', 'qnt_box']]
# carton_measurement.to_csv('carton_measurement.csv', index= False)

df = pd.read_csv('carton_measurement.csv')
debug = 0
box_quant, quantity, how_to = [], [], []
exception = [11168, 11738]
PO_DE = pd.read_sql('po_delivery_static',con=rm_mydb)
container_date = ['2022-05-03']
article_no_list = PO_DE[PO_DE['ETA'].isin(container_date)]['article_no'].values
article_no_list = [float(each) for each in article_no_list]
for index, row in df.iterrows():
    # if row['article_no'] == 11402:
    if row['article_no'] in article_no_list:
        box1 = Box(length= row['carton_length_cm'], width= row['carton_width_cm'], height= row['carton_height_cm'])
        shape = box1.create_Box()
        box1.length += PUFFER
        box1.width += PUFFER
        pallete = Palette()
        if row['article_no'] in exception:
            if row['article_no'] == 11168:
                pallete.length = 126
            elif row['article_no'] == 11738:
                pallete.length = 112
            else:
                continue
        result_box = {}

        a = pallete.same2(box= box1)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
            if a[1] > 2:
                result_box['W2'] = -1
            else:
                result_box['W2'] = a

        shape = Box.flip_right(shape)
        box2 = Box(length= np.max(shape[:,2]) + PUFFER, width= np.max(shape[:,0]) + PUFFER, height= np.max(shape[:,1]))
        
        a = pallete.WH_Sym(box1, box2)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
        
        result_box['WH_Sym'] = a

        a = pallete.same2(box= box2)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
        
        result_box['H2'] = a

        shape = Box.turn_right(shape)
        box3 = Box(length= np.max(shape[:,2]) + PUFFER, width= np.max(shape[:,0]) + PUFFER, height= np.max(shape[:,1]))
        a = pallete.HL_Asym(box1 = box2, box2= box3)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
        
        result_box['HL_Asym'] = a

        a = pallete.same2(box3)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
    
        result_box['L2W'] = a


        shape = box1.create_Box()
        shape = Box.turn_right(shape)
        box4 = Box(length= np.max(shape[:,2]) +  PUFFER, width= np.max(shape[:,0]) + PUFFER, height= np.max(shape[:,1]))
        a = pallete.same2(box4)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
        
        result_box['L2H'] = a


        a = pallete.LW_Asym(box1= box1, box2= box4)
        if a not in [0,-1]:
            sub_pallete = SubPallete(length= a[-1])
            a = list(a)
            a.append(sub_pallete.length_rest(box_width= box1))
            tuple(a)
    
        result_box['LW_Asym'] = a

        # evaluate the best orientation
        result_quantity = {}
        max = 0
        how = ''
        for key, value in result_box.items():
            if type(value) is int:
                value_list = value
            else:
                value_list = list(value)

            if '2' in key:
                if value == -1:
                    result_quantity[key] = -1
                elif value == 0:
                    result_quantity[key] = 0
                elif key not in ["W2", "H2"]: #(2, length_count, height_count, top_rest_max, length_rest, front)
                    result_quantity[key] = np.prod(value_list[:3]) + value_list[3] + value_list[-1]
                else:
                    result_quantity[key] = np.prod(value_list[:3]) + value_list[3]

            elif 'Sym' in key:
                if value == 0 or value == -1:
                    result_quantity[key] = 0
                else: #(left_height_count,right_height_count, length_rest, front)
                    result_quantity[key] = np.sum(value_list[:2])*2 #+ value_list[-1]
            elif 'HL_Asym'in key:
                if value == 0:
                    result_quantity[key] = 0
                else: #(left_height_count, right_length_count, top_rest_max, length_rest, front)
                    result_quantity[key] = value_list[0]*2 + value_list[1]*value_list[0] + value_list[2] + value_list[-1]
            else:
                if value == 0:
                    result_quantity[key] = 0
                else: #(left_height_count,left_length_count, length_rest, front)
                    result_quantity[key] = value_list[0]*2 + value_list[1]*value_list[0]  #+ value_list[-1]
            
            if (max <= result_quantity[key]) and (result_quantity[key] > 0):
                max = result_quantity[key]
                how = key
                if ('2' in key) and (type(value) is not int):
                    if (value_list[3] != 0):
                        how += f" top {value_list[3]}"
                    if (value_list[-1] not in [0,-1]):    
                        how += f" front {value_list[-1]}"
                elif ('HL' in key) and (type(value) is not int):
                    if (value_list[2] != 0):
                        how += f" top {value_list[2]}"          
                    if (value_list[-1] not in [0,-1]):    
                        how += f" front {value_list[-1]}"
                else:
                    if (value_list[-1] not in [0,-1]):    
                        how += f" front {value_list[-1]}"

        WHS_relevant = WHS[(WHS['article_no'] == row['article_no']) | (WHS['default_article_no'] == row['article_no'])]
        for index_WHS, row_WHS in WHS_relevant.iterrows():
            if row_WHS['size'] == 'Quarter':
                max_new = np.floor(max*0.15)
            elif row_WHS['size'] == 'Half':
                max_new = np.ceil(max*0.4)
            else:
                max_new = max
            updatequery = (f"UPDATE `Warehouse_StorageUnit_DUS` SET " +
                        f"`single_quantity_max`={max_new*row['qnt_box']}, " +
                        f"`single_quantity_threshold`={max_new*row['qnt_box']*0.8}"               
                        f"where id = {row_WHS['id']}")
            mycursor.execute(updatequery)
            mydb.commit()    
                        
                        # `carton_width_cm` ={width}, `carton_height_cm` = {height} where article_no = {i}')

        updatequery = (f"UPDATE `product_database_storage_assign` SET " +
                    f"`Full_qty`={max*row['qnt_box']}, `Half_qty`={np.ceil(max*0.4)*row['qnt_box']}, " +
                    f"`Quarter_qty`={np.floor(max*0.15)*row['qnt_box']}, " +
                    f"`Storing_way`='{how}' " +
                    f"where article_no = {row['article_no']}")
        mycursor.execute(updatequery)
        mydb.commit()  
        box_quant.append(max)
        quantity.append(max * row['qnt_box'])
        how_to.append(f"{how}")
        print(debug)
        debug += 1
#     # print(result_box)
#     # print(result_quantity)


# df['box_quant'] = box_quant
# df['quantity'] = quantity
# df['how'] = how_to
# df = df[df['quantity'] != 0]
# df.to_csv('quantity_for_container_after.csv', index= False)