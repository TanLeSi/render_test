import streamlit as st
from pathlib import Path
from inbound_functions.box import Box
from inbound_functions.pallette import Palette
import numpy as np
import pandas as pd
import sys





def create_boxes(length: float, width: float, height: float):
    box_W2 = Box(length, width, height)
    shape = box_W2.create_Box()
    shape = Box.flip_right(shape)
    box_H2 = Box(length= np.max(shape[:,2]),
             width= np.max(shape[:,0]),
             height= np.max(shape[:,1]))
    shape = box_H2.create_Box()
    shape= Box.turn_right(shape)
    box_L2H = Box(length= np.max(shape[:,2]),
             width= np.max(shape[:,0]),
             height= np.max(shape[:,1]))
    shape = box_W2.create_Box()
    shape = Box.turn_right(shape)
    box_L2W = Box(length= np.max(shape[:,2]),
             width= np.max(shape[:,0]),
             height= np.max(shape[:,1]))
    return box_W2, box_H2, box_L2H, box_L2W

def calculate_box_arrange(input_df: pd.DataFrame):
    result = pd.DataFrame()
    max_way = dict()
    for index, row in input_df.iterrows():
        if row['carton_height_cm']*row['carton_length_cm']*row['carton_width_cm'] == 0:
            print(f'{row.article_no} has zero dimension')
            continue
        pallete = Palette()
        box_W2, box_H2, box_L2H, box_L2W = create_boxes(length= row['carton_length_cm'],
            width= row['carton_width_cm'],
            height= row['carton_height_cm'])

        W2 = pallete.same2(box= box_W2)
        W2['way'] = 'W2'
        W2 = pd.DataFrame.from_dict([W2])

        H2 = pallete.same2(box= box_H2)
        H2['way'] = 'H2'
        H2 = pd.DataFrame.from_dict([H2])
        
        L2H = pallete.same2(box= box_L2H)
        L2H['way'] = 'L2H'
        L2H = pd.DataFrame.from_dict([L2H])
        
        L2W = pallete.same2(box= box_L2W)
        L2W['way'] = 'L2W'
        L2W = pd.DataFrame.from_dict([L2W])
        
        WH_Sym = pallete.WH_Sym(box1=box_W2, box2= box_H2)
        WH_Sym['way'] = 'WH_Sym'
        WH_Sym = pd.DataFrame.from_dict([WH_Sym])
        
        LH_Asym = pallete.LH_LW_Asym(box_L2= box_L2H, box2= box_H2)
        LH_Asym['way'] = 'LH_Asym'
        LH_Asym = pd.DataFrame.from_dict([LH_Asym])
        
        LW_Asym = pallete.LH_LW_Asym(box_L2= box_L2W, box2= box_W2)
        LW_Asym['way'] = 'LW_Asym'
        LW_Asym = pd.DataFrame.from_dict([LW_Asym])
        
        temp = pd.concat([W2,H2,L2H,L2W,WH_Sym,LH_Asym,LW_Asym], ignore_index= True)
        temp['article_no'] = row['article_no']
        max_way[f"{row['article_no']}"] = temp.loc[temp['sum_box'] == temp['sum_box'].max(), 'way'].values[0]
        result = pd.concat([result, temp], ignore_index= True)
    result = result.assign(
        article_no = result.article_no.astype(int),
        length_count = result.length_count.astype(int),
        height_count = result.height_count.astype(int),
        left_height_count = result.left_height_count.astype(int),
        right_height_count = result.right_height_count.astype(int),
        left_length_count = result.left_length_count.astype(int),
        sum_box = result.sum_box.astype(int),
        top_rest = result.top_rest.astype(int)
    )
    return result, max_way

if __name__ == '__main__':
    inbound_input = pd.read_csv(Path.cwd().parents[0] / 'inbound_test.csv')
    # inbound_input = pd.read_csv('inbound_test.csv')
    PUFFER = 0
    result, max_way = calculate_box_arrange(input_df= inbound_input)
    print(result)
    print(max_way)