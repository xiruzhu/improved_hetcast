#Packet Object ... 
from enum import Enum
from functools import total_ordering
from collections import deque

class message_type(Enum):
    ACK = 0
    DATA = 1
    REQ = 2

class packet:
    def __init__(self, sender_id, original_sender_id, receiver_id, final_receiver_id, task_id, send_time, seq_num, deadline, data_type=message_type.DATA, request=None, num_packets=1):
        self.sender_id = sender_id;
        self.original_sender_id = original_sender_id;
        self.receiver_id = receiver_id;
        self.final_receiver_id = final_receiver_id;
        self.send_time = send_time;
        self.data_type = data_type;
        self.seq_num = seq_num;
        self.request = request;
        self.task_id = task_id;
        self.deadline = deadline;
        self.ack = True;
        self.num_packets = num_packets; #Number of packets for this chain ... 

    def print_packet(self):
        print("Original Sender: ", self.original_sender_id);
        print("Sender: ", self.sender_id);
        print("Final Receiver: ", self.final_receiver_id);
        print("Receiver: ", self.receiver_id);
        print("Task ID:", self.task_id);
        print("Data Type: ", self.data_type);
        print("Deadline: ", self.deadline);
        print("Request: ", self.request);
        print("Num packets: ", self.num_packets)

    def clone(self):
        return packet(self.sender_id, self.original_sender_id, self.receiver_id, self.final_receiver_id, 
        self.task_id, self.send_time, self.seq_num, self.deadline, self.data_type,
        self.request, num_packets=self.num_packets); 

class packet_system:
    def __init__(self, system_id, wireless_system, message_system, log_dir="../logs/", time_decay=0.1, up_speed=1000, down_speed=1000,current_time=0, packet_size=2000, resend_rate=5):
        self.packet_size=packet_size;
        self.sequence_number = 0;
        self.task_number = 0;

        self.system_id = system_id;
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.message_system = message_system;
        self.wireless_system = wireless_system;

        self.resend_rate = resend_rate;

        self.send_speed = up_speed;
        self.receive_speed = down_speed;
        self.receive_queue = deque();
        self.send_queue = deque();
        self.ack_wait_queue = {};
        # self.log_file = log_dir + system_id + ".txt";
        # log_file = open(self.log_file, "w");
        # log_file.close();

    def transfer_packet(self, packet):
        packet.sender_id = self.system_id;
        packet.receiver_id = None;
        self.message_system.schedule_packet(packet);

    def get_request_packet(self, task_id, data_size, request, original_sender_id, final_receiver_id, deadline):
        new_packet = self.create_req_packet(original_sender_id, None, final_receiver_id, task_id, request, deadline);
        return new_packet;

    def get_upload_packets(self, task_id, data_size, original_sender_id, final_receiver_id, deadline):
        num_packets = int((data_size + self.packet_size - 1)//self.packet_size);
        packet_list = [];
        for i in range(num_packets):
            new_packet = self.create_data_packet(original_sender_id, None, final_receiver_id, task_id, deadline, num_packets);
            packet_list.append(new_packet);
        return packet_list;

    def receive_packet(self, packet):
        self.receive_queue.append(packet);

    def send_packet(self, packet):
        if packet.data_type == message_type.DATA or packet.data_type == message_type.REQ and packet.ack is True:
            #Here, if the message contains data
            #Add to messages waiting to acknowlegement queue.
            #Note broadcasts do not receive acknowledgements
            self.ack_wait_queue["receiver:" + packet.receiver_id + "|seq_number:" + str(packet.seq_num)] = packet;
        self.send_queue.append(packet);

    def log_data(self, message_type, message, sender):
        try:
            log_file = open(self.log_file, "a+");
            log_file.write(str(message_type) + "," + message + ", " + sender + "\n")
            log_file.close();
        except:
            print("Log file failed");

    def create_data_packet(self, original_receiver_id, receiver_id, final_receiver_id, task_id, deadline, num_packets, data_type=message_type.DATA):
        new_packet = packet(self.system_id, original_receiver_id, receiver_id, final_receiver_id, task_id, self.current_time, self.sequence_number, deadline, data_type=data_type, num_packets=num_packets);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_req_packet(self, original_receiver_id, receiver_id, final_receiver_id, task_id, request, deadline, data_type=message_type.REQ):
        new_packet = packet(self.system_id, original_receiver_id, receiver_id, final_receiver_id, task_id, self.current_time, self.sequence_number, deadline, data_type, request=request);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_ack_packet(self, received_packet):
        new_packet = packet(self.system_id, self.system_id, received_packet.sender_id, received_packet.sender_id, received_packet.task_id, self.current_time, received_packet.seq_num, self.current_time + self.resend_rate, data_type=message_type.ACK);
        return new_packet;

    def get_time(self):
        return self.current_time;

    def update(self):
        #First we receive data ....
        self.current_time = self.message_system.get_time();
        for i in range(min(self.receive_speed, len(self.receive_queue))):
            received_data = self.receive_queue.popleft();
            if received_data.deadline < self.current_time:
                continue;
            elif received_data.receiver_id != received_data.final_receiver_id:
                #This means we need to transfer data ...
                self.transfer_packet(received_data);
                #self.log_data(received_data.data_type, ", Send Time: "+ str(received_data.send_time) + ", Current Time: " + str(self.current_time), "Sender: " + received_data.sender_id)                    
            elif received_data.data_type == message_type.DATA:
                if received_data.ack is True:
                    #Broadcasts do not receive acknowledgements 
                    self.send_packet(self.create_ack_packet(received_data));
                self.wireless_system.receive_data_packet(received_data);
                #self.log_data(message_type.DATA, ", Send Time: "+ str(received_data.send_time) + ", Current Time: " + str(self.current_time), "Sender: " + received_data.sender_id)                    
            elif received_data.data_type == message_type.REQ:
                #....
                self.send_packet(self.create_ack_packet(received_data));
                self.wireless_system.receive_request_packet(received_data);
                #self.log_data(message_type.REQ, ", Send Time: "+ str(received_data.send_time) + ", Current Time: " + str(self.current_time), "Sender: " + received_data.sender_id)                    
            else:
                #Received an acknowledgement ... 
                ack_id = "receiver:" + received_data.sender_id + "|seq_number:" + str(received_data.seq_num)
                if ack_id in self.ack_wait_queue:
                    self.ack_wait_queue.pop(ack_id);
                    #self.log_data(message_type.ACK, ", Send Time: "+ str(received_data.send_time) + ", Current Time: " + str(self.current_time), "Sender: " + received_data.sender_id)                    
        
        #Now after we handled all the received data we can handle 
        #We must handle the data with acknowledgement we have not received which is past the deadline ... 
        key_list = list(self.ack_wait_queue.keys());
        for item in key_list:
            if self.ack_wait_queue[item].deadline < self.current_time:
                #Thus, this item can no longer be send and has failed ... 
                old_packet = self.ack_wait_queue.pop(item);
            elif self.ack_wait_queue[item].send_time + self.resend_rate > self.current_time:
                #We need to resend the data as we did not receive the acknowledgement ....  
                old_packet = self.ack_wait_queue.pop(item);
                old_packet.send_time = self.current_time;
                self.transfer_packet(old_packet);
            #otherwise just wait for it to finish
        #Finally, we must handle sending data
        for i in range(min(self.send_speed, len(self.send_queue))):
            new_packet = self.send_queue.popleft();
            if new_packet.ack == False:
                self.message_system.broadcast_packet(new_packet);
            else:
                self.message_system.unicast_packet(new_packet);



    