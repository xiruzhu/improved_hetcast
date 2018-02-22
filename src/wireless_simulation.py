#The main simulation system
#This time, will attempt to make it fairly object oriented ...
from access_node import access_node
from access_node import node_type

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
            for j in range(self.drop):
                x_new_range = [x_range[0] + i * x_split, x_range[0] + (i + 1) * x_split];
                y_new_range = [y_range[0] + j * y_split, y_range[0] + (j + 1) * y_split];
                if access_point.in_range_of_rect(x_new_range, y_new_range):
                    print(i, j, x_new_range, y_new_range);
                    if levels == 1:
                        access_dict[str(i) + ":" + str(j)][access_point.id] = access_point;
                    else:
                        self.add_access_resursive(access_point, x_new_range, y_new_range, access_dict[str(i) + ":" + str(j)], levels - 1)
                    break;
                    
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
            i = (position[0]%self.drop);
            j = (position[1]%self.drop);
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


class wireless_simulation:
    #This class will be for the overall simulation where we build from top down
    #In this class, it contains the network system over a region. 
    
    def __init__(self, num_rsu, num_lte, map_size=(32000, 32000)):
        #Hence, given a set of rsu and LTE, we will attempt to place the towers in a method. 
        self.num_rsu = num_rsu;
        self.num_lte = num_lte;
        self.map_size = map_size;

map_system = map_system();
new_access_point = access_node("beast", [1000, 1], node_type.LTE, 5000);
map_system.add_access_point(new_access_point);

# point_2 = access_node("not_so_beast", [300,4200], node_type.RSU, 1000);
# map_system.add_access_point(point_2);

# point_3 = access_node("wot_so_beast", [1500,3900], node_type.RSU, 1500);
# map_system.add_access_point(point_3);

point_4 = access_node("not so nice", [12300,1], node_type.LTE, 8000);
map_system.add_access_point(point_4);


for i in range(map_system.drop):
    for j in range(map_system.drop):
        print(str(i) + ":" + str(j), map_system.bucket_system[str(i) + ":" + str(j)])
print(map_system.get_access_points_in_range([1, 1]))