#Definines the vehicle class
from data_system import vehicle_data_system, fixed_data_system, global_data_system
from message_system import message_queue
from access_node import access_node
import math
from enum import Enum

class task_outcome(Enum):
    ONGOING = 0
    FAILED = 1
    SUCCESS = 2

class task:
    def __init__(self, task_id, data_size, packet_size, deadline):
        self.num_packets = (data_size + packet_size - 1)//packet_size;
        self.data_size = data_size;
        self.deadline = deadline;
        self.packet_received = {};
        self.outcome = task_outcome.ONGOING;

    #Gets task status
    def get_task_status(self):
        return self.outcome;

    def set_packet_received(self, packet):
        self.packet_received[packet.seq_num] = True;
        if self.num_packets == len(self.packet_received):
            self.outcome = task_outcome.SUCCESS;
    #Returns false if failed check
    #True otherwise
    def check_deadline(self, current_time):
        if current_time > self.deadline:
            self.outcome = False;
            return False;
        return True;

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
        self.data_system = data_system;

        self.task_queue = {};
        self.num_success_task = 0;
        self.num_failed_task = 0;

    def update_tasks(self):
        task_items = list(self.task_queue.keys());
        for item in task_items:
            if self.task_queue[item].outcome == task_outcome.SUCCESS:
                self.task_queue.pop(item);
                self.num_success_task += 1;
            elif self.task_queue[item].outcome == task_outcome.FAILED:
                self.task_queue.pop(item);
                self.num_failed_task += 1;
            elif self.task_queue[item].deadline > self.current_time:
                self.task_queue.pop(item);
                self.num_failed_task += 1;

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
        self.update_tasks();

    def get_distance(self, position):
        current_position = self.get_location();
        return (current_position[0] - position[0]) ** 2 + (current_position[0] - position[0]) ** 2;

    def receive_data_packet(self, packet):
        if packet.task_id in self.task_queue:
            self.task_queue[packet.task_id].set_packet_received(packet);

    def receive_request_packet(self, packet):
        self.data_system.receive_request_packet(packet);

    def naive_scheduling(self, packet):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        #Thus, given this packet, we can deliver now without any regards ...
        
        #The real problem is finding where to send this packet ... 
        print("TBD")

    def print_success_fail_ratio(self):
        print("Node ID: " + self.get_id() + " Success: ", self.num_success_task, "Failures: ", self.num_failed_task, "Total: ", self.num_failed_task + self.num_success_task);

    def schedule_packet(self, packet):
        #Given a packet, we need to decide who to send it to and when ... 
        #This will be different based on node
        self.naive_scheduling(packet);

    def upload_data(self, sender_id, task_id, data_size, receiver_id, deadline):
        self.wireless_system.get_data_packets(sender_id, task_id, data_size, receiver_id, deadline);
        
    #Given size of request packet, this can be sent immediately rather than be scheduled
    def request_data(self, sender_id, task_id, data_size, request, receiver_id, deadline):
        self.task_queue[task_id] = task(task_id, data_size, self.packet_size, deadline);
        self.wireless_system.get_request_packet(sender_id, task_id, data_size, request, receiver_id, deadline);

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
        self.task_queue = {};
        self.num_success_task = 0;
        self.num_failed_task = 0;


    def naive_scheduling(self, packet):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        #Thus, given this packet, we can deliver now without any regards ...
        
        #At the global level, find the RSU/LTE closest to the target to send ... 
        #print("WAS here global")
        # print("\n\n", self.get_id())
        if self.wireless_system.is_fixed_node(packet.final_receiver_id):
            #Directly send the packet to target
            packet.receiver_id = packet.final_receiver_id;
            self.wireless_system.add_packet_to_send_queue(packet);
        #For vehicles
        elif self.wireless_system.is_vehicle_node(packet.final_receiver_id):
            #We have to find the rsu closests ... 
            sorted_list = self.wireless_system.map_system.get_access_points_in_range(self.wireless_system.get_node_position(packet.final_receiver_id));
            if len(sorted_list) > 0:
                packet.receiver_id = sorted_list[0][1]; #Set the receiver id to the closest access node
                self.wireless_system.add_packet_to_send_queue(packet);

    def update(self):
        self.data_system.update();
        self.update_tasks();  
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
        self.task_queue = {};
        self.num_success_task = 0;
        self.num_failed_task = 0;

    def naive_scheduling(self, packet):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        #Thus, given this packet, we can deliver now without any regards ...
        #At the LTE/RSU level, check if target is fixed node ... 
        # print("WAS here LTE")
        #print("\n\n\n" + self.get_id());
        #packet.print_packet();
        if self.wireless_system.is_fixed_node(packet.final_receiver_id):
            #Directly send the packet to target
            packet.receiver_id = packet.final_receiver_id;
            self.wireless_system.add_packet_to_send_queue(packet);
        #For vehicles
        elif self.wireless_system.is_vehicle_node(packet.final_receiver_id):
            #If in range
            position = self.wireless_system.get_node_position(packet.final_receiver_id);
            if self.get_distance(position) < self.wireless_range ** 2:
                #print("Sending data directly to vehicle")
                packet.receiver_id = packet.final_receiver_id;
                self.wireless_system.add_packet_to_send_queue(packet);
            else:
                #Send to global to process ... 
                #print("Sending data directly to global")
                packet.receiver_id = "GLOBAL_DATA";
                self.wireless_system.add_packet_to_send_queue(packet);

    def update(self):
        self.data_system.update();
        self.current_time += self.time_decay;
        self.update_tasks();

class vehicle_network_node(network_access_point):
    def __init__(self, vehicle_id, wireless_system, global_data_system, traci, current_time, packet_size=2000, time_decay=0.1, upload_speed=100, download_speed=100, wireless_range=100):
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
        self.task_queue = {};
        self.num_success_task = 0;
        self.num_failed_task = 0;
    
    def get_local_access_node_id(self):
        return self.wireless_system.get_local_access_point(self.get_location());

    def naive_scheduling(self, packet):
        #Given this is the naive algorithm, we schedule packets the moment we receive the requests
        #Thus, given this packet, we can deliver now without any regards ...
        #For vehicles, if within range of vehicle ... 
        if self.wireless_system.is_vehicle_node(packet.final_receiver_id):
            #If in range, use vehicular network to directly send data ... 
            position = self.wireless_system.get_node_position(packet.final_receiver_id);
            if self.get_distance(position) < self.wireless_range ** 2:
                packet.receiver_id = packet.final_receiver_id;
                self.wireless_system.add_packet_to_send_queue(packet);
                return;
        target_node_location = self.get_location();
        sorted_list = self.wireless_system.map_system.get_access_points_in_range(target_node_location);
        if len(sorted_list) == 0:
            return;
        packet.receiver_id = sorted_list[0][1];
        self.wireless_system.add_packet_to_send_queue(packet);

    def get_time(self):
        return self.current_time;

    def update(self):
        self.current_time = self.wireless_system.get_time();
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            self.location = self.traci.vehicle.getPosition(self.get_id());
        self.data_system.update();
        self.update_tasks();
