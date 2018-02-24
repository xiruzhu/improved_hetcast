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

class data_priority(Enum):
    LOW = 0
    MED = 0
    HIG = 0

class data_type(Enum):
    STATUS = 0
    BROWSING = 1
    SENSING = 2
    VIDEOS = 4

class vehicular_data:
    def __init__(self, vehicle_data_type, data_id, priority, location):
        self.priority = priority;
        self.data_id = data_id;
        self.vehicle_data_type = vehicle_data_type;
        self.rank_value = self.generate_rank_value(priority);
        self.location = location;
        if self.vehicle_data_type == data_type.STATUS:
            self.data_size = max(200, np.random.normal(1000, 500));
        elif self.vehicle_data_type == data_type.BROWSING:
            self.data_size = max( 4000, np.random.normal(50000, scale=200000));
        elif self.vehicle_data_type == data_type.SENSING:
            self.data_size = max( 4000, np.random.normal(200000, scale=500000));
        elif self.vehicle_data_type == data_type.VIDEOS:
            self.data_size = max( 100000, np.random.normal(1000000, scale=2000000));

    def generate_rank_value(self):
        #The rank value is generated based on a normal distribution curve
        normal_rank_values = max(1, np.random.normal(10, 3));
        return normal_rank_values;

#First, each vehicle generates data each second 
#There is a decay which reduces each data's ranking 
#Data with negative or zero rank value are removed from the system 
class decaying_data_system:
    def __init__(self, current_time, location, value_decay=0.3):
        self.current_time = current_time;
        self.current_rank_system = {};
        self.data_item_dict = {};
        self.decay = value_decay;
        self.location = location;

    def add_data_item(self, data_item):
        # Adding Data ... 
        self.data_item_dict[len(self.data_item_dict)] = data_item;
        self.current_rank_system[len(self.current_rank_system)] = data_item.rank_value;

    def update(self):
        self.current_time += 1;
        sorted_system = sorted(zip(self.current_rank_system.values(), self.current_rank_system.keys()), reverse=True)
        self.dist_freq = [];
        for item in sorted_system:
            self.dist_freq.append(item[1]);
        
    def select_item(self):
        #Select data based on a zipf distribution .... 
        return self.dist_freq[np.random.zipf(len(self.dist_freq))];
        

#This class deals with how each vehicle generates data ... 




