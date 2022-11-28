import numpy as np
from box import Box
import pandas as pd


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
                'top_rest': top_rest_max,
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
                'top_rest': top_rest_max,
                'sum_box': (left_length_count + 2) * left_height_count
            }
        return Palette.empty_result



    # def LW_Asym(self,box1:Box,box2:Box):
    #     pal_left_height_sum, left_height_count = 0, 0
    #     pal_left_length_sum, left_length_count = 0, 0  
    #     if box1.width + box2.width <= self.width and np.floor(self.length/box1.length) == 2:
    #         left_height_count = np.floor(self.height/box2.height)
    #         left_length_count = np.floor(self.length/box2.length)
    #         while pal_left_height_sum < self.height:
    #             pal_left_height_sum += box1.height
    #             if pal_left_height_sum < self.height:
    #                 left_height_count += 1
    #             else:
    #                 break
            
    #         while pal_left_length_sum <= self.length:
    #             pal_left_length_sum += box2.length
    #             if pal_left_length_sum < self.length:
    #                 left_length_count += 1
    #             else:
    #                 break
     
            
    #         return (left_height_count,left_length_count, length_rest)
    #     return Palette.empty_result

    # # def Sub_pallete(self, box):


