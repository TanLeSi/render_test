from pallette import Palette
from box import Box
import numpy as np

class SubPallete(Palette):
    def __init__(self, length):
        super().__init__()
        self.length = length
        # self.width = width
        
   
        
        
    def length_rest(self, box_width):
        shape = box_width.create_Box()
        shape = Box.flip_right(shape)
        box_height = Box(length= np.max(shape[:,2]), width= np.max(shape[:,0]), height= np.max(shape[:,1]))
        shape = box_width.create_Box()
        shape = Box.turn_right(shape)
        box_length_height = Box(length= np.max(shape[:,2]), width= np.max(shape[:,0]), height= np.max(shape[:,1]))
        shape = box_width.create_Box()
        shape = Box.flip_right(shape)
        shape = Box.turn_right(shape)
        box_length_width = Box(length= np.max(shape[:,2]), width= np.max(shape[:,0]), height= np.max(shape[:,1]))
        shape = Box.flip_right(shape)
        box_up = Box(length= np.max(shape[:,2]), width= np.max(shape[:,0]), height= np.max(shape[:,1]))
        
        same_max = 0
        unsame = 0
        box_sample = [box_width,box_length_height,box_length_width,box_height, box_up]
        for i in range(5):
            current_box = box_sample[i]
            if self.length > np.min(current_box.dimension):
                extra = self.same2(box= current_box)
                if type(extra) != int and same_max > extra[0] * extra[2]:
                    same_max = extra[0] * extra[2]
        if self.length > box_length_width.length and self.width > box_length_width.width + box_up.width:
            left_h_count = np.floor(self.height/box_length_width.height)
            right_h_count = np.floor(self.height/box_up.height)
            unsame = left_h_count + right_h_count
        if same_max > unsame:
            return same_max
        if unsame > same_max:
            return unsame
        else:
            return 0

        
            
        
