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

from packet_system import packet_system, task_outcome
import numpy as np
from enum import Enum

class data_priority(Enum):
    LOW = 0
    MED = 1
    HIG = 2

class data_type(Enum):
    LOW = 0
    MID = 1
    HIG = 2
    HUG = 4

class vehicular_data:
    def __init__(self, data_id, location):
        self.data_id = data_id;
        self.rank_value = self.generate_rank_value();
        self.location = location;
        self.base_data_size =  max(200, np.random.normal(1000, 500));

    def get_data_size(self, data_type):
        result = self.base_data_size;
        if data_type == data_type.MID:
            result *= 10;
        elif data_type == data_type.HIG:
            result *= 100;
        elif data_type == data_type.HUG:
            result *= 1000;
        return result;

    def generate_rank_value(self):
        #The rank value is generated based on a normal distribution curve
        normal_rank_values = max(0, np.random.normal(10, 3));
        return normal_rank_values;

#First, each vehicle generates data each second 
#There is a decay which reduces each data's ranking 
#Data with negative or zero rank value are removed from the system 
class decaying_data_system:
    def __init__(self, current_time, location, value_decay=0.3, time_decay=0.01):
        self.current_time = current_time;
        self.current_rank_system = {};
        self.data_item_dict = {};
        self.decay = value_decay;
        self.time_decay = time_decay;
        self.location = location;

    def add_data_item(self, data_item):
        # Adding Data ... 
        self.data_item_dict[data_item.data_id] = data_item;
        self.current_rank_system[data_item.data_id] = data_item.rank_value;

    #Updates the decay system 
    def update(self):
        remove_list = [];
        for key in self.data_item_dict:
            self.data_item_dict[key].rank_value -= self.decay;
            self.current_rank_system[key] -= self.decay;
            if self.current_rank_system[key] < 0:
                remove_list.append(key);
        for key in remove_list:
            self.data_item_dict.pop(key);
            self.current_rank_system.pop(key);
        self.current_time += time_decay;
        sorted_system = sorted(zip(self.current_rank_system.values(), self.current_rank_system.keys()), reverse=True)
        self.dist_freq = [];
        for item in sorted_system:
            self.dist_freq.append(item[1]);
        
    def select_item(self):
        #Select data based on a zipf distribution .... 
        return self.dist_freq[np.random.zipf(len(self.dist_freq))];

#This class deals with how the global system generates and request data:
class global_data_system:
    def __init__(self):
        print("TBD")

#This class deals with how each vehicle generates data ... 
class vehicle_data_system:
    #Each vehicle must generate data
    #We assume that at each step, a vehicle generates a status message to the server ... 
    #This message can be considered of size low
    #Furthermore, the system stores data available ... 
    
    def __init__(self, vehicle_object, message_node, data_system, current_time, time_decay=0.01, data_request_rate=1):
        self.current_time = current_time;
        self.vehicle = vehicle_object;
        self.data_item_dict = {};
        self.message_node = message_node;
        self.data_system = data_system;
        self.packet_system = packet_system("packet_system:" + vehicle_object.get_id(), self, message_node, current_time=current_time, time_modifier=time_decay);
        self.failures = 0;
        self.success = 0;
        self.time_decay = time_decay;

    def get_data(self, data_id):
        if data_id in self.data_item_dict:
            return self.data_item_dict[data_id];
        else:
            return None;

    def data_request(self, packet):
        return self.get_data(packet.request);

    def task_callback(self, task):
        if task.outcome == task_outcome.SUCCESS:
            self.success += 1;
        else:
            self.failures += 1;

    def update(self):
        self.current_time += self.time_decay;
        new_data_id = "data_id:" + self.vehicle.get_id() + "," + str(self.current_time);
        self.data_item_dict[new_data_id] = vehicular_data(new_data_id, self.vehicle.get_location());





