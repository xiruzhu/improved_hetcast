#Definines the vehicle class
from data_system import vehicle_data_system
from message_system import message_queue
from access_node import access_node
import math

#Kind of an interface class for what we need ... 
class network_access_point:
    def __init__(self, node_id, position, packet_system, current_time, time_decay=0.1, upload_speed=1000, download_speed=1000):
        self.node_id = node_id;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.position = position;
        self.packet_system = packet_system;
        self.current_time = current_time;
        self.time_decay = time_decay;

    def set_speeds(self, upload_speed, download_speed):
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;

    def print_network_speeds_per_second(self):
        up_speed = self.upload_speed/self.time_decay * self.packet_system.packet_size;
        down_speed = self.download_speed/self.time_decay * self.packet_system.packet_size;
        print("Upload Speed: " + str(up_speed) + ", Download Speed: " + str(down_speed));

    def get_position(self):
        return self.position;

    def get_time(self)
        return self.current_time;

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

#Can be either rsu or lte
class fixed_point(network_access_point):
    def __init__(self, access_node, wireless_system, packet_system, data_system, traci, current_time, time_decay=0.1, upload_speed=100, download_speed=100):
        self.node_id = access_node.access_id;
        self.position = access_node.location;

        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.packet_system = packet_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.data_system = data_system
        self.access_node = access_node;

    def update(self):
        self.current_time += self.time_decay;

    def advanced_upload_scheduling(self, packet_list):
        print("Not yet implemented");

    def naive_upload_scheduling(self, packet_list):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        for packet in packet_list:
            self.wireless_system.upload_data(packet);

    def upload_data(self, task_id, data_size, receiver_id, callback_function, deadline, scheduling_algorithm=naive_upload_scheduling):
        packet_list = self.packet_system.get_upload_packets(task_id, data_size, receiver_id, callback_function, deadline);
        scheduling_algorithm(packet_list);

    #Given size of request packet, this can be sent immediately rather than be scheduled
    def request_data(self, task_id, data_size, request, receiver_id, callback_function):
        request_packet = self.packet_system.get_request_packet(task_id, data_size, request, receiver_id, callback_function);
        self.wireless_system.upload_data(request_packet);

class vehicle(network_access_point):
    def __init__(self, vehicle_id, wireless_system, packet_system, traci, current_time, time_decay=0.1, upload_speed=100, download_speed=100):
        self.node_id = vehicle_id;
        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.packet_system = packet_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.vehicle_data_system = vehicle_data_system(self, wireless_system.complete_data_system, current_time)
        self.location = traci.vehicle.getPosition(self.vehicle_id);

    def get_local_access_node_id(self):
        return self.wireless_system.get_local_access_node_id(self.get_position());

    def update(self):
        if math.ceil(self.current_time) == self.current_time:
            self.location = self.traci.vehicle.getPosition(self.vehicle_id);
        self.vehicle_data_system.update();
        self.current_time += self.time_decay;

    def advanced_upload_scheduling(self, packet_list):
        print("Not yet implemented");

    def naive_upload_scheduling(self, packet_list):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        for packet in packet_list:
            self.wireless_system.upload_data(packet);

    def upload_data(self, task_id, data_size, receiver_id, callback_function, deadline, scheduling_algorithm=naive_upload_scheduling):
        packet_list = self.packet_system.get_upload_packets(task_id, data_size, receiver_id, callback_function, deadline);
        scheduling_algorithm(packet_list);

    #Given size of request packet, this can be sent immediately rather than be scheduled
    def request_data(self, task_id, data_size, request, receiver_id, callback_function):
        request_packet = self.packet_system.get_request_packet(task_id, data_size, request, receiver_id, callback_function);
        self.wireless_system.upload_data(request_packet);