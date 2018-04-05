# This module is meant to simulate the data system of vehicle access node
# We assume for the base model there is no data requests targeted towards specific vehicles 
#
# Each VEH generates data gathered from its surrouding and its passengers. 
# The data generated has a level of urgency for uploading
# Each VEH generates data requests due to its passengers and situation 
# The data requests also has a level of urgency for downloading 
# 
# In terms of data usage, we utilize 3 categories; low, medium, high
# Data based on size
# Status Messages: Small
# Internet Browsing: Medium
# Sensing data: Medium
# Online Games: Medium
# Video streaming: High
#
# In terms of responsiveness, we utilize 3 categories, low, medium, high
# This will depend on what the user needs and is not assigned ahead of time  

import numpy as np
from enum import Enum
from scipy.ndimage.filters import gaussian_filter
import math
import scipy.misc
import matplotlib.pyplot as plt;

class data_type(Enum):
    LOW = 0
    MID = 1
    HIG = 2
    HUG = 4

GLOBAL_DATA = "GLOBAL_DATA"

#Revamp of the data system of our simulator. 
#Based on the following data logic
#In the map exist several point of interests which affects a data point's 

class sensing_data():
    def __init__(self, sensor_id, data_id, location_sensed, sensing_rank):
        self.sensor_id = sensor_id;
        self.data_id = data_id;
        self.location_sensed = location_sensed;
        self.sensing_rank = sensing_rank;
        self.base_data_size = max(200, np.random.normal(1000, 500));

    def get_origin(self):
        return self.sensor_id;

    def check_origin(self, checked_origin):
        return self.sensor_id == checked_origin;

    def get_rank(self):
        return self.sensing_rank;

    def get_location(self):
        return self.location_sensed;

    def get_data_size(self, data_type):
        result = self.base_data_size;
        if data_type == data_type.MID:
            result *= 4;
        elif data_type == data_type.HIG:
            result *= 16;
        elif data_type == data_type.HUG:
            result *= 64;
        return result;

class pov_data():
    def __init__(self, rank, position, deadline, duration, update_rate):
        self.rank = rank;
        self.position = position;
        self.deadline = deadline;
        self.rank_decay = rank/duration * update_rate;
    
    def get_rank(self):
        return self.rank;

    def decay_rank(self):
        self.rank -= self.rank_decay;

    def is_expired(self, current_time):
        return current_time >= self.deadline;

    def update_position(self, position):
        self.position = position;

    def get_position(self):
        return self.position;

class sensing_priority_system:
    def __init__(self, data_manager, map_size=(32000, 32000), scale=32, update_rate=10, num_povs=300, mean_pov_duration=200): 
        self.data_manager = data_manager;
        self.map_size = map_size;
        self.scale = scale;
        self.update_rate = update_rate;
        self.num_povs = num_povs;
        self.mean_pov_duration = mean_pov_duration;
        self.sensing_map = None;
        #self.base_sensing_map = np.abs(np.random.normal(size=(int(self.map_size[0]/self.scale), int(self.map_size[1]/self.scale))));
        self.pov_list = [];

    def set_map_value(self, position, value):
        scaled_position = [int(position[0]/self.scale), int(position[1]/self.scale)];
        self.sensing_map[scaled_position[0], scaled_position[1]] += value;
    
    def get_map_value(self, position):
        scaled_position = [int(position[0]/self.scale), int(position[1]/self.scale)];
        return self.sensing_map[scaled_position[0], scaled_position[1]] * 1/(1 + abs(np.random.normal()))

    def update_sensing_map(self, sigma=25):
        #so the map is set up
        current_time = self.data_manager.get_time();
        self.sensing_map = np.abs(np.random.normal(0, 0.08, (int(self.map_size[0]/self.scale), int(self.map_size[1]/self.scale))))
        #self.sensing_map = np.copy(self.base_sensing_map);
        new_pov_list = [];
        for item in self.pov_list:
            if not item.is_expired(current_time):
                #we update the object 
                item.decay_rank();
                self.set_map_value(item.get_position(), item.get_rank());
                new_pov_list.append(item);
        self.pov_list = new_pov_list;
        while len(self.pov_list) < self.num_povs:
            #Add a new point of interest ... 
            x = np.random.uniform(0, self.map_size[0])
            y = np.random.uniform(0, self.map_size[1])
            data_rank = np.random.uniform(1, 10);
            deadline = abs(np.random.normal(self.mean_pov_duration + data_rank, self.mean_pov_duration/2)) + current_time;
            self.pov_list.append(pov_data(data_rank, [x, y], deadline, deadline - current_time, self.update_rate));
            self.set_map_value([x, y], data_rank);
        self.sensing_map = gaussian_filter(self.sensing_map, sigma);
        max_val = np.amax(np.amax(self.sensing_map));
        min_val = np.amin(np.amin(self.sensing_map));
        self.sensing_map = (self.sensing_map - min_val)/(max_val - min_val)
        self.save_sensing_map(str(current_time));

    def save_sensing_map(self, name, directory="../figures/"):
        fig = plt.imshow(self.sensing_map, cmap='jet', interpolation='sinc')
        plt.savefig(directory + name + '_coverage_visualization.png')
        plt.close();
        del fig;

    def update(self):
        current_time = self.data_manager.get_time();
        if current_time == math.ceil(current_time) and round(current_time) % self.update_rate == 0:
            self.update_sensing_map();            

class temp_timer:
    def __init__(self):
        self.current_time = 0;

    def get_time(self):
        return self.current_time;

#First, each vehicle generates data each second 
#There is a decay which reduces each data's ranking 
#Data with negative or zero rank value are removed from the system 
class decaying_data_system:
    def __init__(self, current_time, wireless_system, location, max_dist, value_decay=0.3, time_decay=0.2, global_system=False):
        self.current_time = current_time;
        self.current_rank_system = {};
        self.data_item_dict = {};
        self.dist_freq = [];
        self.decay = value_decay;
        self.time_decay = time_decay;
        self.location = location;
        self.max_dist = max_dist;
        self.item_added_flag = False
        self.global_system = global_system;
        self.wireless_system = wireless_system;

    def get_item(self, data_id):
        if data_id in self.data_item_dict:
            return self.data_item_dict[data_id];
        return None;

    def get_distance(self, position):
        return math.sqrt(abs(position[0] - self.location[0]) ** 2 + abs(position[1] - self.location[1]) ** 2)

    #Thus, when we add an item, it depends on the distance ... 
    def add_data_item(self, data_item):
        # Adding Data ... 
        self.data_item_dict[data_item.data_id] = data_item;
        #Ranking is based upon distance and its randomly pulled value ... 
        if self.global_system:
            self.current_rank_system[data_item.data_id] = data_item.get_rank();
        else:
            self.current_rank_system[data_item.data_id] = data_item.get_rank() * min(1, self.max_dist/(self.get_distance(data_item.get_location()) + 1));
        self.item_added_flag = True;

    #Updates the decay system 
    def update(self):
        self.current_time = self.wireless_system.get_time();
        if self.decay > 0:
            remove_list = [];
            for key in self.data_item_dict:
                self.current_rank_system[key] -= self.decay;
                if self.current_rank_system[key] < 0:
                    remove_list.append(key);
            for key in remove_list:
                self.data_item_dict.pop(key);
                self.current_rank_system.pop(key);
        if self.item_added_flag:
            sorted_system = sorted(zip(self.current_rank_system.values(), self.current_rank_system.keys()))
            self.dist_freq = [];
            for item in sorted_system:
                self.dist_freq.append(self.data_item_dict[item[1]]);
            self.item_added_flag = False;
             
    def select_item(self, minimum=1, attempts=3):
        if len(self.dist_freq) >= minimum:
        #Select data based on a zipf distribution .... 
            zipf_index = np.random.zipf(1.1);
            for i in range(attempts):
                if len(self.dist_freq) > zipf_index:
                    return self.dist_freq[zipf_index];
        return None;

class complete_data_system:
    def __init__(self, current_time, wireless_system, map_size=(32000, 32000), grid_size=(3, 3), global_data_system_size=250000, value_decay=0.3, time_decay=0.01):
        self.map_size = map_size;
        self.grid_size = grid_size;
        self.current_time = current_time;
        self.value_decay = value_decay;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        position = [0, 0]
        self.decay_system_mat = [];
        self.sensing_data_system = sensing_priority_system(self, map_size=map_size);
        #Global Data System
        self.global_data_size = global_data_system_size;
        self.global_data_system = decaying_data_system(current_time, wireless_system, [0, 0], 0, 0, time_decay=time_decay, global_system=True);
        for i in range(global_data_system_size):
            self.global_data_system.add_data_item(sensing_data(GLOBAL_DATA, GLOBAL_DATA + ":" + str(i), [0, 0], np.random.normal()));
        self.global_data_system.update();

        #Create a final system which includes all data item without distance 
        self.global_decay_system = decaying_data_system(current_time, wireless_system, [0, 0], 0, value_decay=value_decay, time_decay=time_decay, global_system=True);

        #Local data system
        x_half = (map_size[0]/grid_size[0])/2;
        y_half = (map_size[0]/grid_size[0])/2;
        max_dist = math.sqrt(x_half ** 2 + y_half ** 2)
        for i in range(grid_size[0]):
            self.decay_system_mat.append([])
            for j in range(grid_size[1]):
                self.decay_system_mat[i].append(decaying_data_system(current_time, wireless_system, [position[0] + x_half, position[1], y_half], max_dist, value_decay, time_decay));
                position[1] += map_size[1]/grid_size[1];
            position[0] += map_size[0]/grid_size[0];
    
    def get_global_no_decay_item(self, data_id):
        return self.global_data_system.get_item(data_id);

    def add_data_item(self, data_item):
        for mat_list in self.decay_system_mat:
            for system in mat_list:
                system.add_data_item(data_item);
        self.global_decay_system.add_data_item(data_item);
    
    def get_time(self):
        return self.wireless_system.get_time();

    def update(self):
        self.current_time = self.wireless_system.get_time();
        self.sensing_data_system.update();
        for mat_list in self.decay_system_mat:
            for system in mat_list:
                system.update();
        self.global_decay_system.update();

    def get_data_rank(self, position):
        return self.sensing_data_system.get_map_value(position);

    def randomly_select_local_data(self):
        #This is meant to randomly select local data ... 
        i = np.random.randint(0, self.grid_size[0]);
        j = np.random.randint(0, self.grid_size[1]);
        return self.decay_system_mat[i][j].select_item();

    def select_data_local(self, location):
        #Given a location, we find the appropriate cell ... 
        i = int(location[0]//(self.map_size[0]/self.grid_size[0]));
        j = int(location[1]//(self.map_size[1]/self.grid_size[1]));
        return self.decay_system_mat[i][j].select_item();

    def select_data_global(self):
        return self.global_data_system.select_item();

    def select_global_decayed_data(self):
        return self.global_decay_system.select_item();

#This class deals with how each vehicle generates data ... 
class vehicle_data_system:
    #Each vehicle must generate data
    #We assume that at each step, a vehicle generates a status message to the server ... 
    #This message can be considered of size low
    #Furthermore, the system stores data available ... 
    
    def __init__(self, network_access_node, global_data_system, current_time, global_data_rate=0.10, local_data_rate=0.20, time_decay=0.1, data_request_rate=1, status_size=1000, deadline_range=[4, 30]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.data_item_dict = {};
        self.global_data_system = global_data_system;
        self.status_size = status_size;
        self.deadline_range = deadline_range;
        self.global_data_rate = global_data_rate;
        self.local_data_rate = local_data_rate;
        self.time_decay = time_decay;

    def get_data(self, data_id):
        if data_id in self.data_item_dict:
            return self.data_item_dict[data_id];
        else:
            return None;

    def receive_request_packet(self, packet):
        requested_item = self.get_data(packet.request["data_id"]);
        if requested_item is None:
            #Fail the task
            return;
        data_size = packet.request["data_size"];     
        deadline = packet.request["deadline"];
        self.network_access_node.upload_data(self.network_access_node.get_id() , packet.task_id, data_size, packet.original_sender_id, deadline);

    def select_data(self, local=False, decayed=False):
        if local:
            data_need = self.global_data_system.select_data_local(self.network_access_node.get_location());
        else:
            if decayed:
                data_need = self.global_data_system.select_global_decayed_data();
            else:
                data_need = self.global_data_system.select_data_global();
        if data_need is None:
            return None;
        if not data_need.check_origin(self.network_access_node.get_id()):
            data_size = round(abs(np.random.normal(loc=0, scale=2)));
            if data_size == 0:
                data_size = data_need.get_data_size(data_type.LOW);
            elif data_size == 1:
                data_size = data_need.get_data_size(data_type.MID);
            elif data_size == 2:
                data_size = data_need.get_data_size(data_type.HIG);
            else:
                data_size = data_need.get_data_size(data_type.HUG);

            deadline = np.random.uniform(self.deadline_range[0], self.deadline_range[1]) + self.current_time;
            request = {"data_id":data_need.data_id, "data_size":data_size, "deadline":deadline};
            self.network_access_node.request_data(self.network_access_node.get_id(), "request:" + self.network_access_node.get_id() + ":" + str(self.current_time), self.status_size, request, data_need.get_origin(), deadline);
        return data_need;

    #Note we send status messages once every second
    def update(self):
        self.current_time = self.network_access_node.get_time();
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            new_data_id = "data_id:" + self.network_access_node.get_id() + "," + str(self.current_time);
            self.data_item_dict[new_data_id] = sensing_data(self.network_access_node.get_id(), new_data_id, self.network_access_node.get_location(), self.global_data_system.get_data_rank(self.network_access_node.get_location()));
            self.global_data_system.add_data_item(self.data_item_dict[new_data_id]);
            #Time to send a status message ... we can directly send data as such without need for scheduler ... 
            local_rsu_id = self.network_access_node.get_local_access_node_id();
            if local_rsu_id != None:
                deadline = np.random.uniform(self.deadline_range[0], self.deadline_range[1]) + self.current_time;
                self.network_access_node.upload_data(self.network_access_node.get_id(),"status:" + self.network_access_node.get_id() + ":" + str(self.current_time), self.status_size, local_rsu_id, deadline);
            data_rate = self.local_data_rate;
            likelihood = np.random.ranf();
            if likelihood <= data_rate:
                self.select_data(True);
            data_rate = self.global_data_rate;
            if likelihood <= data_rate:
                self.select_data(True);

class fixed_data_system(vehicle_data_system):
    def __init__(self, network_access_node, global_data_system, current_time, time_decay=0.1, status_size=1000, deadline_range=[5, 200]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.global_data_system = global_data_system;
        self.status_size = status_size;
        self.failures = 0;
        self.success = 0;
        self.deadline_range = deadline_range;        
        self.time_decay = time_decay;    
    #Note we send status messages once every second
    #Fixed data node doesn't return data ... 
    def get_data(self):
        return None;

    def update(self):
        self.current_time = self.network_access_node.get_time();

class global_data_system(vehicle_data_system):
    def __init__(self, network_access_node, global_data_system, current_time, data_rate=10, time_decay=0.1, status_size=1000, deadline_range=[5, 200]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.global_data_system = global_data_system;
        self.failures = 0;
        self.success = 0;
        self.status_size = status_size;
        self.deadline_range = deadline_range;        
        self.time_decay = time_decay;    
        self.data_rate = data_rate;
    #Note we send status messages once every second

    def get_data(self, data_id):
        return self.global_data_system.get_global_no_decay_item(data_id);

    def update(self):
        self.current_time = self.network_access_node.get_time();
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            data_rate = self.data_rate;
            while data_rate > 0:
                likelihood = np.random.ranf();
                if likelihood <= data_rate:
                    self.select_data(False, True);
                    data_rate -= likelihood;
                else:
                    break;