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
import math

class data_type(Enum):
    LOW = 0
    MID = 1
    HIG = 2
    HUG = 4

GLOBAL_DATA = "GLOBAL_DATA"

class vehicular_data:
    def __init__(self, origin, data_id, location):
        self.origin = origin;
        self.data_id = data_id;
        self.rank_value = self.generate_rank_value();
        self.location = location;
        self.base_data_size =  max(200, np.random.normal(1000, 500));

    def check_origin(self, checked_origin):
        return self.origin == checked_origin;

    def get_data_size(self, data_type):
        result = self.base_data_size;
        if data_type == data_type.MID:
            result *= 10;
        elif data_type == data_type.HIG:
            result *= 100;
        elif data_type == data_type.HUG:
            result *= 1000;
        return result;
    
    def get_location(self):
        return self.location;

    def generate_rank_value(self):
        #The rank value is generated based on a normal distribution curve
        normal_rank_values = max(0, np.random.normal(1, .5));
        return normal_rank_values;

#First, each vehicle generates data each second 
#There is a decay which reduces each data's ranking 
#Data with negative or zero rank value are removed from the system 
class decaying_data_system:
    def __init__(self, current_time, location, max_dist, value_decay=0.3, time_decay=0.1, global_system=False):
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

    def get_distance(self, position):
        return math.sqrt(abs(position[0] - self.location[0]) ** 2 + abs(position[1] - self.location[1]) ** 2)

    #Thus, when we add an item, it depends on the distance ... 
    def add_data_item(self, data_item):
        # Adding Data ... 
        self.data_item_dict[data_item.data_id] = data_item;
        #Ranking is based upon distance and its randomly pulled value ... 
        if self.global_system:
            self.current_rank_system[data_item.data_id] = data_item.rank_value;
        else:
            self.current_rank_system[data_item.data_id] = data_item.rank_value * self.get_distance(data_item.get_location())/self.max_dist;
        self.item_added_flag = True;

    #Updates the decay system 
    def update(self):
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
        self.current_time += self.time_decay;   
             
    def select_item(self):
        if len(self.dist_freq) > 0:
        #Select data based on a zipf distribution .... 
            zipf_index = len(self.dist_freq)
            while not zipf_index < len(self.dist_freq):
                zipf_index = np.random.zipf(1.1);
            return self.dist_freq[zipf_index];
        return None;

class complete_data_system:
    def __init__(self, current_time, map_size=(32000, 32000), grid_size=(5, 5), global_data_system_size=250000, value_decay=0.3, time_decay=0.01):
        self.map_size = map_size;
        self.grid_size = grid_size;
        self.current_time = current_time;
        self.value_decay = value_decay;
        self.time_decay = time_decay;
        position = [0, 0]
        self.decay_system_mat = [];

        #Global Data System
        self.global_data_size = global_data_system_size;
        self.global_data_system = decaying_data_system(current_time, [0, 0], 0, 0, time_decay=time_decay, global_system=True);
        for i in range(global_data_system_size):
            self.global_data_system.add_data_item(vehicular_data(GLOBAL_DATA, GLOBAL_DATA + ":" + str(i), [0, 0]));
        self.global_data_system.update();

        #Create a final system which includes all data item without distance 
        self.global_decay_system = decaying_data_system(current_time, [0, 0], 0, value_decay=value_decay, time_decay=time_decay, global_system=True);

        #Local data system
        x_half = (map_size[0]/grid_size[0])/2;
        y_half = (map_size[0]/grid_size[0])/2;
        max_dist = math.sqrt(x_half ** 2 + y_half ** 2)
        for i in range(grid_size[0]):
            self.decay_system_mat.append([])
            for j in range(grid_size[1]):
                self.decay_system_mat[i].append(decaying_data_system(current_time, [position[0] + x_half, position[1], y_half], max_dist, value_decay, time_decay));
                position[1] += map_size[1]/grid_size[1];
            position[0] += map_size[0]/grid_size[0];
    
    def add_data_item(self, data_item):
        for mat_list in self.decay_system_mat:
            for system in mat_list:
                system.add_data_item(data_item);
        self.global_decay_system.add_data_item(data_item);
    
    def update(self):
        for mat_list in self.decay_system_mat:
            for system in mat_list:
                system.update();
        self.global_decay_system.update();
        self.current_time += self.time_decay;

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
    
    def __init__(self, network_access_node, global_data_system, current_time, global_data_rate=0.10, local_data_rate=0.20, time_decay=0.1, data_request_rate=1, status_size=1000, deadline_range=[5, 200]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.data_item_dict = {};
        self.global_data_system = global_data_system;
        self.status_size = status_size;
        self.deadline_range = deadline_range;
        self.global_data_rate = global_data_rate * time_decay;
        self.local_data_rate = local_data_rate * time_decay;
        self.time_decay = time_decay;

    def get_data(self, data_id):
        if data_id in self.data_item_dict:
            return self.data_item_dict[data_id];
        else:
            return None;

    def handle_data_request(self, packet):
        requested_item = self.get_data(packet.request["data_id"]);
        if requested_item is None:
            #Fail the task
            return;
        data_size = packet.request["data_size"];     
        deadline = packet.request["deadline"];
        self.network_access_node.upload_data(self.network_access_node.get_id() ,"data:" + self.network_access_node.get_id() + ":" + str(self.current_time), data_size, packet.sender_id, deadline);

    def select_data(self, local=False, decayed=False):
        if local:
            data_need = self.global_data_system.select_data_local(self.network_access_node.get_location());
        else:
            if decayed:
                data_need = self.global_data_system.select_global_decayed_data();
            else:
                data_need = self.global_data_system.select_data_global();
        if data_need is None:
            return;
        if not data_need.check_origin(self.network_access_node.get_id()):
            data_size = np.random.randint(0, 4);
            if data_size == 0:
                data_size = data_need.get_data_size(data_type.LOW);
            elif data_size == 1:
                data_size = data_need.get_data_size(data_type.MID);
            elif data_size == 2:
                data_size = data_need.get_data_size(data_type.HIG);
            else:
                data_size = data_need.get_data_size(data_type.HUG);

            deadline = np.random.uniform(self.deadline_range[0], self.deadline_range[1]);
            request = {"data_id":data_need.data_id, "data_size":data_size, "deadline":deadline};
            self.network_access_node.request_data(self.network_access_node.get_id(), "request:" + self.network_access_node.get_id() + ":" + str(self.current_time), self.status_size, request, data_need.origin, deadline);

    #Note we send status messages once every second
    def update(self):
        new_data_id = "data_id:" + self.network_access_node.get_id() + "," + str(self.current_time);
        self.data_item_dict[new_data_id] = vehicular_data(self.network_access_node.get_id(), new_data_id, self.network_access_node.get_location());
        self.global_data_system.add_data_item(self.data_item_dict[new_data_id]);
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            #Time to send a status message ... we can directly send data as such without need for scheduler ... 
            deadline = np.random.uniform(self.deadline_range[0], self.deadline_range[1]);
            local_rsu_id = self.network_access_node.get_local_access_node_id();
            if local_rsu_id != None:
                self.network_access_node.upload_data(self.network_access_node.get_id(),"status:" + self.network_access_node.get_id() + ":" + str(self.current_time), self.status_size, local_rsu_id, deadline);
        
        data_rate = self.local_data_rate;
        while data_rate > 0:
            likelihood = np.random.ranf();
            if likelihood <= data_rate:
                self.select_data(True);
                data_rate -= likelihood;
            else:
                break;
        data_rate = self.global_data_rate;
        while data_rate > 0:
            likelihood = np.random.ranf();
            if likelihood <= data_rate:
                self.select_data(False);
                data_rate -= likelihood;
            else:
                break;

class fixed_data_system(vehicle_data_system):
    def __init__(self, network_access_node, global_data_system, current_time, time_decay=0.1, data_request_rate=1, status_size=1000, deadline_range=[5, 200]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.data_item_dict = {};
        self.global_data_system = global_data_system;
        self.status_size = status_size;
        self.failures = 0;
        self.success = 0;
        self.deadline_range = deadline_range;        
        self.time_decay = time_decay;    
    #Note we send status messages once every second

    def update(self):
        self.current_time += self.time_decay;

class global_data_system(vehicle_data_system):
    def __init__(self, network_access_node, global_data_system, current_time, data_rate=50, time_decay=0.1, data_request_rate=25, status_size=1000, deadline_range=[5, 200]):
        self.current_time = current_time;
        self.network_access_node = network_access_node;
        self.data_item_dict = {};
        self.global_data_system = global_data_system;
        self.failures = 0;
        self.success = 0;
        self.status_size = status_size;
        self.deadline_range = deadline_range;        
        self.time_decay = time_decay;    
        self.data_rate = data_rate * time_decay;
    #Note we send status messages once every second
    
    def update(self):
        self.current_time += self.time_decay;
        data_rate = self.data_rate;
        while data_rate > 0:
            likelihood = np.random.ranf();
            if likelihood <= data_rate:
                self.select_data(False, True);
                data_rate -= likelihood;
            else:
                break;