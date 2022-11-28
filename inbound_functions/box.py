import numpy as np

# PUFFER = 0.7 # box get bigger because of compression
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






