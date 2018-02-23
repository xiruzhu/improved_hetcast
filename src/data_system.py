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

class data_type(Enum):
    STATUS = 0
    BROWSING = 1
    SENSING = 2
    VIDEOS = 4

class vehicular_data:
    def __init__(self, vehicle_data_type, data_id, priority):
        self.priority = priority;
        self.data_id = data_id;
        if self.priority == data_type.STATUS:
            self.data_size = max(200, np.random.normal(1000, 500));
        elif self.priority == data_type.BROWSING:
            self.data_size = max( 4000, np.random.normal(50000, scale=200000));
        elif self.priority == data_type.SENSING:
            self.data_size = max( 4000, np.random.normal(200000, scale=500000));
        elif self.priority == data_type.VIDEOS:
            self.data_size = max( 100000, np.random.normal(1000000, scale=2000000));

class decaying_data_generator:
    
