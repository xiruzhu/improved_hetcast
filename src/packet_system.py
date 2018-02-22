#Packet Object ... 
from enum import Enum

class message_type(Enum):
    ACK = 0
    DATA = 1
    REQ = 2

class packet:
    def __init__(self, sender_id, receiver_id, task_id, send_time, seq_num, data_type=message_type.DATA, request=None):
        self.sender_id = sender_id;
        self.receiver_id = receiver_id;
        self.send_time = send_time;
        self.data_type = data_type;
        self.seq_num = seq_num;
        self.request = request;
        self.task_id = task_id;

class packet_system:
    def __init__(self, system_id, message_system, client_system, log_dir="../logs/", time_modifier=1,send_speed_per_tick=1000, receive_speed_per_tick=1000,current_time=0, packet_size=2000, deadline=3):
        self.packet_size=packet_size;
        self.sequence_number = 0;
        self.task_number = 0;
        self.deadline = deadline;
        self.system_id = system_id;
        self.current_time = current_time;
        self.time_modifier = time_modifier;
        self.message_system = message_system;
        self.client_system = client_system;

        self.send_speed = send_speed_per_tick;
        self.receive_speed = receive_speed_per_tick;
        self.receive_queue = [];
        self.send_queue = [];
        self.ack_wait_queue = {};
        self.log_file = log_dir + system_id;
        log_file = open(self.log_file, "w");
        log_file.close();

        self.tasks_queue = {};

    def get_task_id(self):
        self.task_number += 1;
        if self.task_number % 2147483647 == 0:
            self.task_number = 0;
        return self.task_number;

    #Send a request for a specific data ... To simplify matters, each request is for one data type
    def request_data(self, request, receiver_id, callback_function, deadline):
        task_id = self.get_task_id();
        new_task = {"data_size":self.packet_size, "num_packets":1, "task_callback":callback_function, "packet_ack":{}, "deadline":deadline}
        new_packet = self.create_data_packet(receiver_id, task_id);
        self.send_packet(new_packet);
        new_task["packet_ack"][new_packet.seq_num] = None;
        self.tasks_queue[task_id];

    def upload_data(self, data_size, receiver_id, callback_function, deadline):
        task_id = self.get_task_id();
        num_packets = (data_size + self.packet_size - 1)//self.packet_size;
        new_task = {"data_size":data_size, "num_packets":num_packets, "task_callback":callback_function, "packet_ack":{}, "deadline":deadline}
        for i in range(num_packets):
            new_packet = self.create_data_packet(receiver_id, task_id);
            self.send_packet(new_packet);
            new_task["packet_ack"][new_packet.seq_num] = None;
        self.tasks_queue[task_id];

    def receive_packet(self, packet):
        self.receive_queue.append(packet);

    def send_packet(self, packet):
        if packet.data_type == message_type.DATA or packet.data_type == message_type.REQ:
            #Here, if the message contains data
            #Add to messages waiting to 
            self.ack_wait_queue["receiver:" + packet.receiver_id + "|seq_number:" + str(packet.seq_num)] = packet;
        self.send_queue.append(packet);

    def log_data(self, message_type, message):
        log_file = open(self.log_file, "a+");
        log_file.write(str(message_type) + "," + message + "\n")
        log_file.close();

    def update(self):
        #First we clean up the system of completed tasks ... 
        for task in self.tasks_queue:
            task_status = 0;
            for packet in self.tasks_queue[task]["packet_ack"]:
                if self.tasks_queue[task]["packet_ack"][packet] == True:
                    task_status += 1;
                elif self.tasks_queue[task]["packet_ack"][packet] == False:
                    task_status = -1;
                    break;
            if task_status == -1:
                #Task failed .... 
                failed_task = self.tasks_queue.pop(task);
                failed_task["task_callback"](failed_task, False);
            elif task_status == len(self.tasks_queue[task]["packet_ack"]):
                success_task = self.tasks_queue.pop(task);
                success_task["task_callback"](success_task, True);
            elif self.tasks_queue[task]["deadline"] < self.current_time:
                failed_task = self.tasks_queue.pop(task);
                failed_task["task_callback"](failed_task, False);
        #First we receive data ....
        for i in range(min(self.receive_speed, len(self.receive_queue))):
            received_data = self.receive_queue.pop(0);            
            if received_data.data_type == message_type.DATA:
                self.send_packet(self.create_ack_packet(received_data));
                self.log_data(message_type.DATA, str(received_data.send_time) + "," + str(self.current_time))                    
            elif received_data.request_data == message_type.REQ:
                #....
                self.send_packet(self.create_ack_packet(received_data));
                self.client_system.data_request(received_data);
                self.log_data(message_type.REQ, str(received_data.send_time) + "," + str(self.current_time))                    
            else:
                #Received an acknowledgement ... 
                ack_id = "receiver:" + received_data.sender_id + "|seq_number:" + str(received_data.seq_num)
                if ack_id in self.ack_wait_queue:
                    original_packet = self.ack_wait_queue.pop(ack_id);
                    self.log_data(message_type.ACK, str(original_packet.send_time) + "," + str(self.current_time))                    
                    self.tasks_queue[original_packet.task_id][original_packet.seq_num] = True;
                #otherwise, it means an acknowledgement for the item has already been received ... 
        #Now after we handled all the received data we can handle 
        #We must handle the data with acknowledgement we have not received which is past the deadline ... 
        for item in self.ack_wait_queue:
            if self.ack_wait_queue[item].send_time + self.deadline < self.current_time:
                #We need to resend the data as we did not receive the acknowledgement ....  
                old_packet = self.ack_wait_queue.pop(item);
                old_packet.send_time = self.current_time;
                self.send_packet(old_packet);
            #otherwise just wait for it to finish
        #Finally, we must handle sending data
        for i in range(min(self.send_speed, len(self.send_queue))):
            new_packet = self.send_queue.pop(0);
            self.message_system.send_packet(new_packet);
        self.current_time += self.time_modifier;

    def create_data_packet(self, receiver_id, task_id, data_type=message_type.DATA):
        new_packet = packet(self.system_id, receiver_id, task_id, self.current_time, self.sequence_number, data_type);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_req_packet(self, receiver_id, task_id, data_type=message_type.REQ):
        new_packet = packet(self.system_id, receiver_id, task_id, self.current_time, self.sequence_number, data_type);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_ack_packet(self, received_packet):
        new_packet = packet(self.system_id, received_packet.sender_id, received_packet.task_id, self.current_time, received_packet.seq_num, data_type=message_type.ACK);
        return new_packet;

    