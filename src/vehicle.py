#Definines the vehicle class
from data_system import vehicle_data_system
from message_system import message_queue
from access_node import access_node
from wireless_system import network_access_point
import math

class vehicle(network_access_point):
    def __init__(self, vehicle_id, wireless_system, packet_system, traci, current_time, time_decay=0.1, upload_speed=100, download_speed=100):
        self.vehicle_id = vehicle_id;
        self.traci = traci;
        self.time_decay = time_decay;
        self.wireless_system = wireless_system;
        self.packet_system = packet_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.vehicle_data_system = vehicle_data_system(self, wireless_system.complete_data_system, current_time)
        self.location = traci.vehicle.getPosition(self.vehicle_id);

    def print_network_speeds_per_second(self):
        up_speed = self.upload_speed/self.time_decay * self.packet_system.packet_size;
        down_speed = self.download_speed/self.time_decay * self.packet_system.packet_size;
        print("Upload Speed: " + str(up_speed) + ", Download Speed: " + str(down_speed));

    def update(self):
        self.current_time += self.time_decay;
        if math.ceil(self.current_time) == self.current_time:
            self.location = self.traci.vehicle.getPosition(self.vehicle_id);
        self.vehicle_data_system.update();

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