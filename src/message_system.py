#Messaging system for the system ... 
#Here we define network of nodes
from packet_system import packet_system
from data_system import complete_data_system
import math
import numpy as np

class message_queue:
    def __init__(self, current_time, time_decay, message_system, message_delay=[0.2, 0.2]):
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.message_delay = message_delay;
        self.message_system = message_system;
        self.message_queue = {};

    def constant_interference_error(self, packet, max_error=0.05):
        return max_error;

    def constant_distance_error(self, packet, max_error=0.05):
        return max_error;

    def add_message(self, packet):
        error_rate = self.constant_interference_error(packet) + self.constant_distance_error(packet);
        if np.random.uniform(0, 1) < error_rate:
            #It failed ... 
            return;
        delay = abs(np.random.normal(self.message_delay[0], self.message_delay[1]));
        packet.delay_value = delay;
        new_id = packet.sender_id + ":" + str(packet.seq_num);
        self.message_queue[new_id] = packet;

    def update(self):
        packets_to_send = [];
        for packet in self.message_queue:
            self.message_queue[packet].delay_value -= self.time_decay;
            packets_to_send.append(packet)
        for packet_id in packets_to_send:
            self.message_system.transfer_to_packet_system(self.message_queue.pop(packet_id));
        self.current_time += self.time_decay;


class messaging_system:
    def __init__(self, traci, wireless_system, current_time, time_decay=0.1, num_lte=100, num_rsu=1000, lte_upload=20000, lte_down=10000, rsu_upload=20000, rsu_down=10000, veh_upload=100, veh_down=400):
        #So in this system, we must keep track of all elements which can receive and send messages ... 
        self.wireless_system = wireless_system
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.traci = traci;
        self.lte_upload = lte_upload;
        self.lte_down = lte_down;
        self.rsu_upload = rsu_upload;
        self.rsu_down = rsu_down;
        self.veh_upload = veh_upload;
        self.veh_down = veh_down;
        #These two list does not change unless one of these go down
        self.fixed_message_queues = {};
        for access_node in self.wireless_system.rsu_list:
            self.fixed_message_queues[access_node.access_id] = message_queue(current_time, time_decay, self);
        for access_node in self.wireless_system.lte_list:
            self.fixed_message_queues[access_node.access_id] = message_queue(current_time, time_decay, self);
        
        #This list does change if it goes down
        self.vehicle_message_queues = {};
        #Next We must keep track of all the packet system
        self.fixed_packet_systems = {};
        for key in self.fixed_message_queues:
            if key in self.wireless_system.lte_list:
                self.fixed_packet_systems[key] = packet_system(key, wireless_system, self, time_decay=time_decay, up_speed=lte_upload, down_speed=lte_down);
            else:
                self.fixed_packet_systems[key] = packet_system(key, wireless_system, self, time_decay=time_decay, up_speed=rsu_upload, down_speed=rsu_down);
        self.vehicle_packet_systems = {};
        #Update everything ... 
        self.update();

    def get_packet_system(self, access_node_id):
        if access_node_id in self.fixed_packet_systems:
            return self.fixed_packet_systems[access_node_id];
        elif access_node_id in self.vehicle_packet_systems:
            return self.vehicle_packet_systems[access_node_id];
        else:
            return None;

    def get_message_queue(self, receiver_id):
        #First we must find the packet system for the receiver
        if receiver_id in self.fixed_message_queues:
            return self.fixed_message_queues[receiver_id];
        elif receiver_id in self.vehicle_message_queues:
            return self.vehicle_message_queues[receiver_id];
        else:
            #Cannot find the packet system and therefore it fails
            return None;

    def schedule_packet(self, packet):
        self.wireless_system.schedule_packet(packet);

    def broadcast_packet(self, packet, broadcast_id_list):
        #Send to all units within range the packet .... 
        for broadcast_id in broadcast_id_list:
            new_packet = packet.clone();
            new_packet.receiver_id = broadcast_id;
            self.unicast_packet(new_packet, ack=False);

    def unicast_packet(self, packet, ack=True):
        packet.ack = ack;
        queue = self.get_message_queue(packet.receiver_id);
        if queue == None:
            return;
        queue.add_message(packet);  

    def get_data_packets(self, sender_id, task_id, data_size, receiver_id, deadline):
        system = self.get_packet_system(sender_id);
        if system == None:
            return;
        data_packet_list = system.get_upload_packets(task_id, data_size, sender_id, receiver_id, deadline);
        for packet in data_packet_list:
            self.schedule_packet(packet);

    def get_request_packet(self, sender_id, task_id, data_size, request, receiver_id, deadline):
        system = self.get_packet_system(sender_id);
        if system == None:
            return;
        request_packet = system.get_request_packet(task_id, data_size, request, sender_id, receiver_id, deadline);
        self.schedule_packet(request_packet);

    def transfer_to_packet_system(self, packet):
        system = self.get_packet_system(packet.receiver_id);
        if system == None:
            return;
        #print("Sending Data To Message System ", packet.task_id, "Receiver: ", packet.sender_id,packet.receiver_id)
        system.receive_packet(packet);     

    def update_vehicle_message_queue(self):
        updated_vehicle_list = self.wireless_system.get_vehicle_id_list();
        new_vehicle_dict = {};
        for vehicle_id in updated_vehicle_list:
            if vehicle_id in self.vehicle_message_queues:
                new_vehicle_dict[vehicle_id] = self.vehicle_message_queues[vehicle_id];
            else:
                new_vehicle_dict[vehicle_id] = message_queue(self.current_time, self.time_decay, self);
        self.vehicle_message_queues = new_vehicle_dict;

    def update_vehicle_packet_system(self):
        updated_vehicle_list = self.wireless_system.get_vehicle_id_list();
        new_vehicle_dict = {};
        for vehicle_id in updated_vehicle_list:
            if vehicle_id in self.vehicle_packet_systems:
                new_vehicle_dict[vehicle_id] = self.vehicle_packet_systems[vehicle_id];
            else:
                new_vehicle_dict[vehicle_id] = packet_system(vehicle_id, self.wireless_system, self, time_decay=self.time_decay, up_speed=self.veh_upload, down_speed=self.veh_down);
        self.vehicle_packet_systems = new_vehicle_dict;

    def update(self):
        if math.ceil(self.current_time) - self.current_time < self.time_decay:
            self.update_vehicle_message_queue();
            self.update_vehicle_packet_system();
        for key in self.fixed_packet_systems:
            self.fixed_message_queues[key].update();
            self.fixed_packet_systems[key].update();
        for key in self.vehicle_packet_systems:
            self.vehicle_message_queues[key].update();
            self.vehicle_packet_systems[key].update();
        self.current_time += self.time_decay;

