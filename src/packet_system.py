#Packet Object ... 
from enum import Enum

class message_type(Enum):
    ACK = 0
    DATA = 1

class packet:
    def __init__(self, sender_id, receiver_id, send_time, seq_num, data_type=message_type.DATA):
        self.sender_id = sender_id;
        self.receiver_id = receiver_id;
        self.send_time = send_time;
        self.data_type = data_type;
        self.seq_num = seq_num;

class packet_system:
    def __init__(self, system_id, message_system, send_speed_per_tick=1000, receive_speed_per_tick=1000,current_time=0, packet_size=2000, deadline=3):
        self.packet_size=packet_size;
        self.sequence_number = 0;
        self.deadline = deadline;
        self.system_id = system_id;
        self.current_time = current_time;
        self.message_system = message_system;

        self.send_speed = send_speed_per_tick;
        self.receive_speed = receive_speed_per_tick;

        self.receive_queue = [];
        self.send_queue = [];
        self.ack_wait_queue = [];

    def upload_data(self, data_size, receiver_id):
        num_packets = (data_size + self.packet_size - 1)//self.packet_size;
        for i in range(num_packets):
            self.send_packet(self.create_packet(receiver_id));

    def receive_packet(self, packet):
        self.receive_queue.append(packet);

    def send_packet(self, packet):
        self.send_queue.append(packet);

    def update(self):
        #First we receive data ....
        for i in range(min(self.receive_speed, len(self.receive_queue))):
            if self.receive_queue[i].data_type == message_type.DATA:
                self.send_packet(self.create_ack_packet(self.receive_queue[i]));

    def create_packet(self, receiver_id, data_type=message_type.DATA):
        new_packet = packet(self.system_id, receiver_id, self.current_time, self.sequence_number, data_type);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_ack_packet(self, received_packet):
        new_packet = packet(self.receive_speed, self.receive_speed, self.current_time, received_packet.seq_num, data_type=message_type.ACK);
        return new_packet;

    