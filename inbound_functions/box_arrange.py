from box import Box
from pallette import Palette
from Sub_Palette import SubPallete
import numpy as np
import pandas as pd
from pathlib import Path
print(Path.cwd())
import sys
sys.path.append(str(Path.cwd().parents[0]))
# sys.exit()
# from functions import rm_mydb

inbound_input = pd.read_csv(Path.cwd().parents[0] / 'inbound_test.csv')
# inbound_input = pd.read_csv('inbound_test.csv')
PUFFER = 0
counter = 0

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


result_same2 = pd.DataFrame(
    columns=['article_no', 'way', 'length_count', 'height_count', 'top_rest',
            'left_height_count', 'right_height_count','left_length_count', 'sum_box']
)


for index, row in inbound_input.iterrows():
    if counter != 0:
        break
    counter += 1
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
    
    a = pd.concat([W2,H2,L2H,L2W,WH_Sym,LH_Asym,LW_Asym], ignore_index= True)
    a['article_no'] = row['article_no']
print(a)
print(box_W2.dimension)
print(box_H2.dimension)
print(box_L2H.dimension)
print(box_L2W.dimension)