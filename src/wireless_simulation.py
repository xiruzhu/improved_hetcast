#The main simulation system
#This time, will attempt to make it fairly object oriented ...
from access_node import access_node
from access_node import node_type
import numpy as np

class map_system:
    def __init__(self, map_size=(32000, 32000), levels=1, drop=10):
        self.map_size = map_size;
        #So we'll divide the map into different levels ...
        self.levels = levels;
        self.drop = drop;
        self.access_point_dictionary = {};
        self.bucket_system = {}
        self.build_bucket_system(self.bucket_system, drop, levels);
        
    def build_bucket_system(self, dict_system, drop, levels):
        if levels == 0:
            return {};
        for i in range(drop):
            for j in range(drop):
                dict_system[str(i) + ":" + str(j)] = {};
                self.build_bucket_system(dict_system[str(i) + ":" + str(j)], drop, levels - 1);

    def add_access_resursive(self, access_point, x_range, y_range, access_dict, levels):
        x_split = abs(x_range[0] - x_range[1])/self.drop;
        y_split = abs(y_range[0] - y_range[1])/self.drop;
        for i in range(self.drop):
            #print("\n")
            for j in range(self.drop):
                x_new_range = [x_range[0] + i * x_split, x_range[0] + (i + 1) * x_split];
                y_new_range = [y_range[0] + j * y_split, y_range[0] + (j + 1) * y_split];
                #print(x_new_range, y_new_range)
                if access_point.in_range_of_rect(x_new_range, y_new_range):
                    #print(i, j, x_new_range, y_new_range);
                    if levels == 1:
                        access_dict[str(i) + ":" + str(j)][access_point.id] = access_point;
                    else:
                        self.add_access_resursive(access_point, x_new_range, y_new_range, access_dict[str(i) + ":" + str(j)], levels - 1)
                    
    def add_access_point(self, access_point):
        self.add_access_resursive(access_point, [0, self.map_size[0]], [0, self.map_size[1]], self.bucket_system, self.levels);

    def get_access_points_in_range(self, position):
        #Returns list of all access points in sorted order from closests to farthest ... 
        #that is within range of course ... 
        true_position = position;
        levels = self.levels;
        access_dict = self.bucket_system;
        data_range = self.map_size;
        while levels >= 1:
            i = (position[0]//(data_range[0]//self.drop));
            j = (position[1]//(data_range[1]//self.drop));
            data_range = [data_range[0] // self.drop, data_range[1] // self.drop];
            position = [position[0] % data_range[0], position[1] % data_range[1]];
            access_dict = access_dict[str(i) + ":" + str(j)]
            levels -= 1;
        distance_list = {};
        for wireless_node in access_dict:
            wireless_node = access_dict[wireless_node]
            distance_list[wireless_node.id] = wireless_node.compute_distance(true_position);
        sorted_values = sorted(zip(distance_list.values(),distance_list.keys()))
        return sorted_values;

    def recursive_visualization(self, data_matrix, access_dict, start, range_vals, levels):
        if levels == 1:
            for i in range(self.drop):
                for j in range(self.drop):
                    data_matrix[start[0] + i, start[1] + j] = len(access_dict[str(i) + ":" + str(j)]);
        else:
            new_range_vals = [range_vals[0] // self.drop, range_vals[1] // self.drop]
            for i in range(self.drop):
                for j in range(self.drop):
                    new_access_dict = access_dict[str(i) + ":" + str(j)];
                    new_start = [start[0] + i * new_range_vals[0], start[1] + j * new_range_vals[1]];
                    self.recursive_visualization(data_matrix, new_access_dict, new_start, new_range_vals, levels - 1);

    def visualize_coverage_map(self, figure_size, prefix="", sigma=4, show=False, save=True):
        visualization_size = [self.drop ** self.levels, self.drop ** self.levels];
        data_matrix = np.zeros(visualization_size);
        self.recursive_visualization(data_matrix, self.bucket_system, [0, 0], [data_matrix.shape[0], data_matrix.shape[1]], self.levels);
        # max_val = np.amax(data_matrix);
        # data_matrix /= max_val;
        import matplotlib.pyplot as plt;
        import scipy.ndimage as sp
        directory = '../figures'   
        fig = plt.imshow(sp.gaussian_filter(data_matrix, sigma=sigma), cmap='jet', interpolation='sinc')
        if save:
            plt.savefig(directory + '/'+ prefix + 'coverage_visualization.png')
        if show:
            plt.show()
        plt.close();
        del fig;

#Return a list of access point centered around the center of the map ... 
def gaussian_placement(num_access_node, map_size, access_type, wireless_range):
    access_node_list = []
    for i in range(num_access_node):
        x_pos = np.clip(np.random.normal(loc=map_size[0]/2, scale=map_size[0]/5), 0, map_size[0]);
        y_pos = np.clip(np.random.normal(loc=map_size[1]/2, scale=map_size[1]/5), 0, map_size[1]);
        access_node_list.append(access_node(str(access_type) + ":" + str(i), [x_pos, y_pos], access_type, wireless_range))
    return access_node_list

class wireless_simulation:
    #This class will be for the overall simulation where we build from top down
    #In this class, it contains the network system over a region. 
    
    def __init__(self, num_rsu, num_lte, map_size=(32000, 32000), random_seed=0, LTE_place=gaussian_placement, RSU_place=gaussian_placement, LTE_range=5000, RSU_range=1000):
        #Hence, given a set of rsu and LTE, we will attempt to place the towers in a method. 
        self.num_rsu = num_rsu;
        self.num_lte = num_lte;
        self.map_size = map_size;
        np.random.seed(random_seed);
        self.map_system = map_system(levels=3, drop=5);
        
        self.rsu_list = RSU_place(num_rsu, map_size, node_type.RSU, RSU_range);
        for i in range(num_rsu):
            self.map_system.add_access_point(self.rsu_list[i]);
    
        self.lte_list = LTE_place(num_lte, map_size, node_type.LTE, LTE_range);
        for i in range(num_lte):
            self.map_system.add_access_point(self.lte_list[i]);
        self.map_system.visualize_coverage_map((800, 800));
