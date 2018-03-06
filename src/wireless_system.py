#Complete Simulation System ... 
from enum import Enum
from wireless_simulation import map_system, gaussian_placement
import numpy as np 

class node_type(Enum):
    VEHICLE = 0
    RSU = 1
    LTE = 2

#Kind of an interface class for what we need ... 
class network_access_point:
    def __init__(self, node_id, position, upload_speed=1000, download_speed=1000):
        self.node_id = node_id;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.position = position;

    def set_speeds(self, upload_speed, download_speed):
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;

    def get_position(self):
        return self.position;

    def get_id(self):
        return self.node_id;

    def update(self):
        print("ERROR")
        quit(1);

    #Immediately send data
    def __upload_data_now__(self, packet_list):
        print("TBD")

    def upload_data(self, packet_list):
        #Not Implemented in this class, should be implemented in child class
        print("ERROR")
        quit(1);

    def download_data(self, packet):
        #Not Implemented in this class, should be implemented in child class
        print("ERROR")
        quit(1);

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

    def handle_data_request(self, packet):
        #Handle a request from a packet system ... 
        print("TBD");

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
        updated_vehicle_list = self.traci.vehicle.getIDList();
        new_vehicle_dict = {};
        for vehicle_id in updated_vehicle_list:
            if vehicle_id in self.vehicle_dict:
                new_vehicle_dict[vehicle_id] = self.vehicle_dict[vehicle_id];
            else:
                new_vehicle_dict[vehicle_id] = None;
        self.vehicle_dict = new_vehicle_dict;
        self.current_time += self.time_decay;
