#Complete Simulation System ... 
from enum import Enum
from map_system import map_system, gaussian_placement
from message_system import messaging_system
import numpy as np 
import math

class node_type(Enum):
    VEHICLE = 0
    RSU = 1
    LTE = 2

class wireless_system:
    def __init__(self, traci, map_size=(32000, 32000), time_decay=0.1, simulation_time=1200, random_seed=0):
        self.current_time = 0;
        self.map_size = map_size;
        self.time_decay = time_decay;
        self.traci = traci;

        #seed the random seed to constant to prevent too much randomness
        np.random.seed(random_seed);

        #skip initial simulation time 
        for i in range(simulation_time):
            self.traci.simulationStep();
        self.current_time = simulation_time;
        
        #Initialize the map system ... 
        self.map_system = map_system(levels=3, drop=5);
        self.add_lte();
        self.add_rsu();

        #Vehicle list ... 
        self.vehicle_dict = {};
        self.fixed_node_dict = {};
        self.message_system = messaging_system(self.traci, self, self.current_time, time_decay=self.time_decay);

    def get_local_access_point(self, location):
        map_points = self.map_system.get_access_points_in_range(location);
        if len(map_points) == 0:
            return None:
        else:
            return map_points[0][1];


    def upload_data(self, packet):
        self.message_system.upload_data(packet);

    def handle_data_request(self, packet):
        print("TO BE IMPLEMENTED")

    def add_lte(self, num_lte=100, lte_range=5000, lte_placement=gaussian_placement):
        self.lte_list = lte_placement(num_lte, self.map_size, node_type.LTE, lte_range);
        for i in range(num_lte):
            self.map_system.add_access_point(self.lte_list[i]);
            self.fixed_node_dict[self.lte_list[i].access_id] = None;

    def add_rsu(self, num_rsu=1000, rsu_range=1000, rsu_placement=gaussian_placement):
        self.rsu_list = rsu_placement(num_rsu, self.map_size, node_type.RSU, rsu_range);
        for i in range(num_rsu):
            self.map_system.add_access_point(self.rsu_list[i]);
            self.fixed_node_dict[self.rsu_list[i].access_id] = None;

    def update_vehicle_dict(self):
        new_vehicle_dict = {};
        for vehicle_id in self.updated_vehicle_list:
            if vehicle_id in self.vehicle_dict:
                new_vehicle_dict[vehicle_id] = self.vehicle_dict[vehicle_id];
            else:
                new_vehicle_dict[vehicle_id] = None;
        self.vehicle_dict = new_vehicle_dict;
        self.current_time += self.time_decay;

    def update(self):
        self.updated_vehicle_list = self.traci.vehicle.getIDList();
        if math.ceil(self.current_time) == self.current_time:
            self.update_vehicle_dict();
        self.message_system.update();
        self.current_time += self.time_decay;
