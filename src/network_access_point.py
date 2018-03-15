#Definines the vehicle class
from data_system import vehicle_data_system, fixed_data_system, global_data_system
from message_system import message_queue
from access_node import access_node
import math

#Kind of an interface class for what we need ... 
class network_access_point:
    def __init__(self, node_id, position, wireless_system, data_system, traci, current_time, packet_size=2000, time_decay=0.1, upload_speed=100, download_speed=100, wireless_range=100):
        self.node_id = node_id;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.location = position;
        self.wireless_system = wireless_system;
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.packet_size = packet_size;
        self.wireless_range = wireless_range;

    def get_wireless_range(self):
        return self.wireless_range;

    def set_speeds(self, upload_speed, download_speed):
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;

    def print_network_speeds_per_second(self):
        up_speed = self.upload_speed/self.time_decay * self.packet_size;
        down_speed = self.download_speed/self.time_decay * self.packet_size;
        print("Upload Speed: " + str(up_speed) + ", Download Speed: " + str(down_speed));

    def get_location(self):
        return self.location;

    def get_time(self):
        return self.current_time;

    def get_id(self):
        return self.node_id;

    def update(self):
        print("ERROR")
        quit(1);

    def get_distance(self, position):
        current_position = self.get_location();
        return (current_position[0] - position[0]) ** 2 + (current_position[0] - position[0]) ** 2;

    def handle_request_packet(self, packet):
        self.handle_request_packet(packet);

    def naive_scheduling(self, packet):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        #Thus, given this packet, we can deliver now without any regards ...
        print("TDB");

    def schedule_packet(self, packet):
        #Given a packet, we need to decide who to send it to and when ... 
        #This will be different based on node
        self.naive_scheduling(packet);

    def upload_data(self, sender_id, task_id, data_size, receiver_id, deadline):
        self.wireless_system.get_data_packets(self, sender_id, task_id, data_size, receiver_id, deadline);

    #Given size of request packet, this can be sent immediately rather than be scheduled
    def request_data(self, sender_id, task_id, data_size, request, receiver_id, deadline):
        self.wireless_system.get_receiver_packets(sender_id, task_id, data_size, request, receiver_id, deadline);

class global_network_node(network_access_point):
    def __init__(self, wireless_system, global_system, traci, current_time, node_id="GLOBAL_DATA", packet_size=2000, time_decay=0.1):
        self.node_id = node_id;
        self.location = [0, 0]
        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.current_time = current_time;
        self.data_system = global_data_system(self, global_system, current_time, time_decay=time_decay);
        self.packet_size = packet_size;

    def update(self):
        self.data_system.update();
        self.current_time += self.time_decay;    

#Can be either rsu or lte
class fixed_network_node(network_access_point):
    def __init__(self, access_node, wireless_system, global_data_system, traci, current_time, packet_size=2000, time_decay=0.1, upload_speed=100, download_speed=100):
        self.node_id = access_node.get_id();
        self.location = access_node.get_location();
        self.wireless_range = access_node.get_wireless_range();

        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.data_system = fixed_data_system(self, global_data_system, current_time, time_decay=time_decay);
        self.access_node = access_node;
        self.packet_size = packet_size;

    def update(self):
        self.data_system.update();
        self.current_time += self.time_decay;

class vehicle_network_node(network_access_point):
    def __init__(self, vehicle_id, wireless_system, global_data_system, traci, current_time, packet_size=2000, time_decay=0.1, upload_speed=100, download_speed=100, wireless_range=250):
        self.node_id = vehicle_id;
        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.data_system = vehicle_data_system(self, global_data_system, current_time, time_decay=time_decay)
        self.location = traci.vehicle.getPosition(self.get_id());
        self.packet_size = packet_size;
        self.wireless_range = wireless_range;

    def get_local_access_node_id(self):
        return self.wireless_system.get_local_access_point(self.get_location());

    def update(self):
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            self.location = self.traci.vehicle.getPosition(self.get_id());
        self.data_system.update();
        self.current_time += self.time_decay;
