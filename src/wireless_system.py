#Complete Simulation System ... 
from enum import Enum
from map_system import map_system, gaussian_placement
from message_system import messaging_system
from data_system import complete_data_system
import numpy as np 
import math
from network_access_point import fixed_network_node, vehicle_network_node, global_network_node

class node_type(Enum):
    VEHICLE = 0
    RSU = 1
    LTE = 2

class wireless_system:
    def __init__(self, traci, map_size=(32000, 32000), time_decay=0.25, simulation_time=1200, random_seed=0):
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
        self.updated_vehicle_id_list = self.traci.vehicle.getIDList();

        #Initialize the map system ... 
        self.map_system = map_system(levels=3, drop=5);
        self.add_lte();
        self.add_rsu();
        self.updated_vehicle_id_list = self.traci.vehicle.getIDList();
        #Vehicle list ... 
        self.vehicle_dict = {};
        self.fixed_node_dict = {};
        self.message_system = messaging_system(self.traci, self, self.current_time, time_decay=self.time_decay);
        self.complete_data_system = complete_data_system(self.current_time, map_size, time_decay=self.time_decay);

        self.fixed_network_access = {};
        for access_node in self.rsu_list:
            self.fixed_network_access[access_node.get_id()] = fixed_network_node(access_node, self, self.complete_data_system, self.traci, self.current_time, time_decay=time_decay);
        for access_node in self.lte_list:
            self.fixed_network_access[access_node.get_id()] = fixed_network_node(access_node, self, self.complete_data_system, self.traci, self.current_time, time_decay=time_decay);
        self.fixed_network_access["GLOBAL_DATA"] = global_network_node(self, self.complete_data_system, self.traci, self.current_time, time_decay=time_decay)
        self.vehicle_network_access = {};
        self.update();
        
    def get_vehicle_id_list(self):
        return self.updated_vehicle_id_list;

    def get_local_access_point(self, location):
        map_points = self.map_system.get_access_points_in_range(location);
        if len(map_points) == 0:
            return None;
        else:
            return map_points[0][1];

    def schedule_packet(self, packet):
        #First, find which network node is necessary
        if packet.receiver_id in self.fixed_node_dict:
            network_node = self.fixed_node_dict[packet.receiver_id]
        elif packet.receiver_id in self.vehicle_dict:
            network_node = self.vehicle_dict[packet.receiver_id]
        else:
            #Can't find receiver id 
            return;
        network_node.schedule_packet(packet);

    def add_packet_to_send_queue(self, packet):
        self.message_system.add_packet_to_send_queue(packet);

    def get_data_packets(self, sender_id, task_id, data_size, receiver_id, deadline):
        self.message_system.get_data_packets(sender_id, task_id, data_size, receiver_id, deadline);

    def get_request_packet(self, sender_id, task_id, data_size, request, receiver_id, deadline):
        self.message_system.get_request_packet(sender_id, task_id, data_size, request, receiver_id, deadline);

    def is_fixed_node(self, target_id):
        return target_id in self.fixed_network_access;

    def is_vehicle_node(self, target_id):
        return target_id in self.vehicle_network_access;

    def get_node_position(self, target_id):
        #First, find which network node is necessary
        if target_id in self.fixed_node_dict:
            network_node = self.fixed_node_dict[target_id]
        elif target_id in self.vehicle_dict:
            network_node = self.vehicle_dict[target_id]
        else:
            #Can't find receiver id 
            return None;
        return network_node.get_location();

    def get_vehicle_in_range(self, packet):
        #First, find which network node is necessary
        if packet.sender_id in self.fixed_node_dict:
            network_node = self.fixed_node_dict[packet.receiver_id]
        elif packet.receiver_id in self.vehicle_dict:
            network_node = self.vehicle_dict[packet.receiver_id]
        else:
            #Can't find receiver id 
            return;
        location = network_node.get_location();
        max_range = network_node.get_wireless_range() ** 2;
        id_list = []
        for veh_id in self.updated_vehicle_id_list:
            if self.vehicle_dict[veh_id].get_distance(location) < max_range:
                id_list.append(veh_id);

    def receive_data_packet(self, packet):
        #First, find which network node is necessary
        if packet.receiver_id in self.fixed_node_dict:
            network_node = self.fixed_node_dict[packet.receiver_id]
        elif packet.receiver_id in self.vehicle_dict:
            network_node = self.vehicle_dict[packet.receiver_id]
        else:
            #Can't find receiver id 
            return;
        network_node.receive_data_packet(packet);

    def receive_request_packet(self, packet):
        #First, find which network node is necessary
        if packet.receiver_id in self.fixed_node_dict:
            network_node = self.fixed_node_dict[packet.receiver_id]
        elif packet.receiver_id in self.vehicle_dict:
            network_node = self.vehicle_dict[packet.receiver_id]
        else:
            #Can't find receiver id 
            return;
        network_node.receive_request_packet(packet);
        
    def add_lte(self, num_lte=100, lte_range=5000, lte_placement=gaussian_placement):
        self.lte_list = lte_placement(num_lte, self.map_size, node_type.LTE, lte_range);
        for i in range(num_lte):
            self.map_system.add_access_point(self.lte_list[i]);

    def add_rsu(self, num_rsu=1000, rsu_range=1000, rsu_placement=gaussian_placement):
        self.rsu_list = rsu_placement(num_rsu, self.map_size, node_type.RSU, rsu_range);
        for i in range(num_rsu):
            self.map_system.add_access_point(self.rsu_list[i]);

    def update_fixed_nodes(self):
        for network_node in self.fixed_network_access:
            self.fixed_network_access[network_node].update();

    def update_vehicle_dict(self):
        new_vehicle_dict = {};
        for vehicle_id in self.updated_vehicle_id_list:
            if vehicle_id in self.vehicle_dict:
                new_vehicle_dict[vehicle_id] = self.vehicle_dict[vehicle_id];
                new_vehicle_dict[vehicle_id].update();
            else:
                new_vehicle_dict[vehicle_id] = vehicle_network_node(vehicle_id, self, self.complete_data_system, self.traci, self.current_time, time_decay=self.time_decay);
        self.vehicle_dict = new_vehicle_dict;

    def update(self):
        print(self.current_time)
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            self.traci.simulationStep();
            self.updated_vehicle_id_list = self.traci.vehicle.getIDList();
        self.complete_data_system.update();
        self.update_fixed_nodes();
        self.update_vehicle_dict();
        self.message_system.update();
        self.current_time += self.time_decay;
