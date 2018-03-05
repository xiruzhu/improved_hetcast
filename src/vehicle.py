#Definines the vehicle class
from data_system import vehicle_data_system
from message_system import message_queue
from access_node import access_node
import math

class vehicle:
    def __init__(self, vehicle_id, message_system, data_system, traci, current_time, time_decay=0.1, upload_speed=100, download_speed=100):
        self.vehicle_id = vehicle_id;
        self.traci = traci;
        self.time_decay = time_decay;
        self.location = traci.vehicle.getPosition(self.vehicle_id);
        self.message_system = message_system;
        self.current_time = current_time;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;
        self.vehicle_data_system = vehicle_data_system(self, message_system, data_system, current_time)
        self.message_queue = message_queue(self.current_time, self.time_decay, self.message_system);

    def sending_message(self, packet):
        self.message_queue.add_message(packet);
    
    def receive_message(self, packet):
        self.vehicle_data_system.packet_system.receive_packet(packet);

    def set_speeds(self, new_upload_speed, new_download_speed):
        self.upload_speed = new_upload_speed;
        self.download_speed = new_download_speed;

    def print_network_speeds_per_second(self):
        up_speed = self.upload_speed/self.time_decay * self.vehicle_data_system.packet_system.packet_size;
        down_speed = self.download_speed/self.time_decay * self.vehicle_data_system.packet_system.packet_size;
        print("Upload Speed: " + str(up_speed) + ", Download Speed: " + str(down_speed));

    def get_vehicle_id(self):
        return self.vehicle_id;

    def get_vehicle_location(self):
        return self.location;

    def update_system(self):
        self.current_time += self.time_decay;
        if math.ceil(self.current_time) == self.current_time:
            self.location = self.traci.vehicle.getPosition(self.vehicle_id);
        self.vehicle_data_system.update();
        self.message_system.update();
