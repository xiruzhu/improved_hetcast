#Messaging system for the system ... 
#Here we define network of nodes
from data_system import complete_data_system
from wireless_simulation import wireless_simulation
from vehicle import vehicle

class message_queue:
    def __init__(self, current_time, time_decay, message_system, message_delay=[0.2, 0.2]):
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.message_delay = max(0, message_delay);
        self.message_system = message_system;
        self.message_queue = {};

    def add_message(self, packet):
        delay = np.random.normal(self.message_delay[0], self.message_delay[1]);
        packet.delay_value = delay;
        new_id = packet.sender_id + ":" + str(packet.seq_num);
        self.message_queue[new_id] = packet;

    def update(self):
        packets_to_send = [];
        for packet in self.message_queue:
            self.message_queue[packet].delay_value -= self.time_decay;
            packets_to_send.append(packet)
        for packet_id in packets_to_send:
            self.message_system.pass_message_to_packet_system(self.message_queue.pop(packet_id));
        self.current_time += self.time_decay;



class messaging_system:
    def __init__(self, current_time, traci, time_decay=0.1, num_lte=100, num_rsu=1000):
        #So in this system, we must keep track of all elements which can receive and send messages ... 
        self.wireless_system = wireless_simulation(num_lte, num_rsu);
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.traci = traci;

        #These two list does not change unless one of these go down
        self.rsu_list = {};
        self.lte_list = {};

        for access_node in self.wireless_system.rsu_list:
            self.rsu_list[access_node.access_id] = message_queue(current_time, time_decay, self);
        
        for access_node in self.wireless_system.lte_list:
            self.rsu_list[access_node.access_id] = message_queue(current_time, time_decay, self);

        #Data system ... 
        self.complete_data_system = complete_data_system(self.current_time, self.wireless_system.map_size)
        
        #This list does change if it goes down
        self.vehicle_dict = {};
        self.update_vehicle_dict();

    def send_packet_to_destination(self, packet):
        print("TBD")
        # if packet.receiver_id in self.vehicle_dict:
        #     #At this point compute an error rate 
        #     self.vehicle_dict[packet.receiver_id].receive_message(packet);

    def pass_message_to_packet_system(self, packet):
        print("TBD")
        # if packet.receiver_id in self.vehicle_dict:
        #     self.vehicle_dict[packet.receiver_id].receive_message(packet);
        # elif packet.receiver_id in self.vehicle_dict:
        #     self.vehicle_dict[packet.receiver_id].receive_message(packet);

    def update_vehicle_dict(self):
        updated_vehicle_list = self.traci.vehicle.getIDList();
        new_vehicle_dict = {};
        for vehicle_id in updated_vehicle_list:
            if vehicle_id in self.vehicle_dict:
                new_vehicle_dict[vehicle_id] = self.vehicle_dict[vehicle_id];
            else:
                new_vehicle_dict[vehicle_id] = vehicle(vehicle_id, self, self.complete_data_system, self.traci, self.current_time);
        self.vehicle_dict = new_vehicle_dict;
        self.current_time += self.time_decay;


            


