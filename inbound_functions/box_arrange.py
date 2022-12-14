import streamlit as st
from pathlib import Path
import numpy as np
import pandas as pd
import sys
import numpy as np

class Box:
    def __init__(self,length, width, height):
        self.length = length #+ PUFFER
        self.width = width #+ PUFFER
        self.height = height #+ PUFFER
        self.dimension = [self.length, self.width, self.height]

        
    def create_Box(self):
        A = np.array([0, self.height, self.length])
        B = np.array([self.width, self.height, self.length])
        C = np.array([self.width, 0, self.length])
        D = np.array([0, 0, self.length])
        E = np.array([0, self.height,0])
        F = np.array([self.width, self.height,0])
        G = np.array([self.width, 0, 0])
        H = np.array([0, 0, 0])
        
        box = np.array([A, B, C, D, E, F, G, H])
        return box


    def flip_right(box):
        box_copy = np.copy(box)
        rotation_matrix = np.array([[np.cos(np.pi/2),-np.sin(np.pi/2),0],
                                    [np.sin(np.pi/2),np.cos(np.pi/2),0],
                                    [0,0,1]])
        x_move = max(box_copy[:,0])
        y_move = max(box_copy[:,1])
        translation_matrix = np.array([x_move/2,y_move/2,0])
        box_copy -= translation_matrix                       
        box_copy = np.matmul(box_copy,rotation_matrix)
        translation_matrix = np.matmul(translation_matrix,rotation_matrix)
        box_copy += np.abs(translation_matrix)
        return np.around(box_copy, decimals= 1)


    def turn_right(box):
        box_copy = np.copy(box)
        rotation_matrix = np.array([[np.cos(np.pi/2), 0 , -np.sin(np.pi/2)],
                                    [0, 1 , 0],
                                    [np.sin(np.pi/2), 0, np.cos(np.pi/2)]])
        z_move = max(box_copy[:,0])        
        translation_matrix = np.array([0, 0, z_move])
        box_copy = np.matmul(box_copy,rotation_matrix)
        box_copy += translation_matrix
        # translation_matrix = np.matmul(translation_matrix,rotation_matrix)
        # box_copy += np.abs(translation_matrix)
        return np.around(box_copy, decimals= 1)

class Palette:

    empty_result= {
        'length_count': 0,
        'height_count': 0,
        'left_height_count': 0,
        'right_height_count': 0,
        'left_length_count': 0,
        'top_rest': 0,
        'sum_box': 0
    }

    def __init__(self):
        self.length = 119.5 + 3
        self.width = 80 + 3
        self.thickness = 14.4
        self.height = 200 - 5 - self.thickness
        

    def same2(self,box: Box):       
        height_count, length_count = 0, 0
        if np.floor(self.width/box.width) != 2:
            return Palette.empty_result

        else:
            length_count = np.floor(self.length/box.length)            
            height_count = np.floor(self.height/box.height)  
            
            height_rest = self.height - height_count*box.height
            top_rest, top_rest_max = 0, 0
            if height_rest > box.length or height_rest > box.width:
                top_rest = np.floor(self.width/box.length) * np.floor(self.length/box.height)
                top_rest_max = top_rest
            
                top_rest = np.floor(self.width/box.height) * np.floor(self.length/box.length)
                if top_rest > top_rest_max:
                    top_rest_max = top_rest                
            else:
                top_rest_max = 0
            if top_rest_max > 5:
                top_rest_max = 0

            return  {
                'length_count': length_count,
                'height_count': height_count,
                'left_height_count': 0,
                'right_height_count': 0,
                'left_length_count': 0,
                'top_rest': int(top_rest_max),
                'sum_box': length_count*2*height_count+top_rest_max
            }


    def WH_Sym(self,box1: Box,box2: Box):
        right_height_count, left_height_count = 0, 0
                
        if (box1.width + box2.width <= self.width) and np.floor(self.length/box1.length) == 2:
                left_height_count = np.floor(self.height/box1.height)
                right_height_count = np.floor(self.height/box2.height)
                return {
                    'length_count': 0,
                    'height_count': 0,
                    'left_height_count': left_height_count,
                    'right_height_count': right_height_count,
                    'left_length_count': 0,
                    'top_rest': 0,
                    'sum_box': 2*(left_height_count + right_height_count)
                }
        return Palette.empty_result

                

    def LH_LW_Asym(self,box_L2: Box,box2: Box):
        left_length_count, left_height_count = 0, 0

        if (box_L2.width + box2.width <= self.width) and np.floor(self.length/box2.length) == 2:
            left_height_count = np.floor(self.height/box_L2.height)
            left_length_count = np.floor(self.length/box_L2.length)

            height_rest = self.height - left_height_count*box_L2.height
            top_rest_max = 0
            if height_rest > box2.width:
                top_rest_max = 2*np.floor(height_rest/box2.width)       
            return {
                'length_count': 0,
                'height_count': 0,
                'left_height_count': left_height_count,
                'right_height_count': 0,
                'left_length_count': left_length_count,
                'top_rest': int(top_rest_max),
                'sum_box': (left_length_count + 2) * left_height_count + top_rest_max
            }
        return Palette.empty_result









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
        if W2['top_rest'] == 0:
            W2['way'] = 'W2'
        else:
            W2['way'] = f"W2 top {W2['top_rest']}"        
        W2 = pd.DataFrame.from_dict([W2])

        H2 = pallete.same2(box= box_H2)
        if H2['top_rest'] == 0:
            H2['way'] = 'H2'
        else:
            H2['way'] = f"H2 top {H2['top_rest']}"        
        H2 = pd.DataFrame.from_dict([H2])
        
        L2H = pallete.same2(box= box_L2H)
        if L2H['top_rest'] == 0:
            L2H['way'] = 'L2H'
        else:
            L2H['way'] = f"L2H top {L2H['top_rest']}"        
        L2H = pd.DataFrame.from_dict([L2H])
        
        L2W = pallete.same2(box= box_L2W)
        if L2W['top_rest'] == 0:
            L2W['way'] = 'L2W'
        else:
            L2W['way'] = f"L2W top {L2W['top_rest']}"        
        L2W = pd.DataFrame.from_dict([L2W])
        
        WH_Sym = pallete.WH_Sym(box1=box_W2, box2= box_H2)
        WH_Sym['way'] = 'WH_Sym'
        WH_Sym = pd.DataFrame.from_dict([WH_Sym])
        
        LH_Asym = pallete.LH_LW_Asym(box_L2= box_L2H, box2= box_H2)
        LH_Asym['way'] = 'LH_Asym'
        LH_Asym = pd.DataFrame.from_dict([LH_Asym])
        
        LW_Asym = pallete.LH_LW_Asym(box_L2= box_L2W, box2= box_W2)
        if LW_Asym['top_rest'] == 0:
            LW_Asym['way'] = 'LW_Asym'
        else:
            LW_Asym['way'] = f"LW_Asym top {LW_Asym['top_rest']}"
        
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