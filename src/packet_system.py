#Packet Object ... 
from enum import Enum

class task_outcome(Enum):
    ONGOING = 0
    FAILED = 1
    SUCCESS = 2

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

class task:
    def __init__(self, task_id, data_size, packet_size, task_callback, deadline):
        self.num_packets = (data_size + packet_size - 1)//packet_size;
        self.data_size = data_size;
        self.task_callback = task_callback;
        self.deadline = deadline;
        self.packet_ack = {};
        self.ack_count = 0;
        self.outcome = task_outcome.ONGOING;

    #initializes a packet
    def init_packet_ack(self, seq_num):
        self.packet_ack[seq_num] = None;

    #Gets task status
    def get_task_status(self):
        return self.outcome;

    #Set the ack status of a task's packet to status
    def set_packet_ack(self, seq_num, status):
        if status == False:
            self.outcome = task_outcome.FAILED;
        else:
            self.packet_ack[seq_num] = True;
            self.ack_count += 1;
            if self.ack_count == len(self.packet_ack):
                self.outcome = True;
    
    #Returns false if failed check
    #True otherwise
    def check_deadline(self, current_time):
        if current_time > self.deadline:
            self.outcome = False;
            return False;
        return True;

class packet_system:
    def __init__(self, system_id, wireless_system, message_system, log_dir="../logs/", time_decay=0.1, up_speed=1000, down_speed=1000,current_time=0, packet_size=2000, deadline=3):
        self.packet_size=packet_size;
        self.sequence_number = 0;
        self.task_number = 0;
        self.deadline = deadline;
        self.system_id = system_id;
        self.current_time = current_time;
        self.time_decay = time_decay;
        self.message_system = message_system;
        self.wireless_system = wireless_system;

        self.send_speed = up_speed;
        self.receive_speed = down_speed;
        self.receive_queue = [];
        self.send_queue = [];
        self.ack_wait_queue = {};
        self.log_file = log_dir + system_id;
        print(self.log_file)
        log_file = open(self.log_file, "w");
        log_file.close();
        self.tasks_queue = {};
    
    def get_request_packet(self, task_id, data_size, request, receiver_id, callback_function):
        new_task = task(task_id, data_size, self.packet_size, callback_function, self.deadline + self.current_time);
        new_packet = self.create_req_packet(receiver_id, task_id, request);
        self.tasks_queue[task_id] = new_task;
        return new_packet;

    #Uploads data ... 
    def get_upload_packets(self, task_id, data_size, receiver_id, callback_function, deadline):
        new_task = task(task_id, data_size, self.packet_size, callback_function, deadline);
        packet_list = [];
        for i in range(new_task.num_packets):
            new_packet = self.create_data_packet(receiver_id, task_id);
            packet_list.append(new_packet);
        self.tasks_queue[task_id] = new_task;
        return packet_list;

    #Send a request for a specific data ... To simplify matters, each request is for one data type
    def request_data(self, task_id, data_size, request, receiver_id, callback_function):
        new_task = task(task_id, data_size, self.packet_size, callback_function, self.deadline + self.current_time);
        new_packet = self.create_req_packet(receiver_id, task_id, request);
        self.send_packet(new_packet);
        new_task.init_packet_ack(new_packet.seq_num);
        self.tasks_queue[task_id] = new_task;

    #Uploads data ... 
    def upload_data(self, task_id, data_size, receiver_id, callback_function, deadline=None):
        if deadline == None:
            deadline = self.deadline;
        new_task = task(task_id, data_size, self.packet_size, callback_function, deadline + self.current_time);
        for i in range(new_task.num_packets):
            new_packet = self.create_data_packet(receiver_id, task_id);
            self.send_packet(new_packet);
            new_task.init_packet_ack(new_packet.seq_num);
        self.tasks_queue[task_id] = new_task;

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
            if task.get_task_status() == task_outcome.FAILED or task.check_deadline() == False:
                #Task failed .... 
                failed_task = self.tasks_queue.pop(task);
                failed_task.task_callback(failed_task);
            elif task.get_task_status() == task_outcome.SUCCESS:
                success_task = self.tasks_queue.pop(task);
                success_task.task_callback(success_task);
        #First we receive data ....
        for i in range(min(self.receive_speed, len(self.receive_queue))):
            received_data = self.receive_queue.pop(0);            
            if received_data.data_type == message_type.DATA:
                self.send_packet(self.create_ack_packet(received_data));
                self.log_data(message_type.DATA, str(received_data.send_time) + "," + str(self.current_time))                    
            elif received_data.request_data == message_type.REQ:
                #....
                self.send_packet(self.create_ack_packet(received_data));
                self.wireless_system.handle_data_request(received_data);
                self.log_data(message_type.REQ, str(received_data.send_time) + "," + str(self.current_time))                    
            else:
                #Received an acknowledgement ... 
                ack_id = "receiver:" + received_data.sender_id + "|seq_number:" + str(received_data.seq_num)
                if ack_id in self.ack_wait_queue:
                    original_packet = self.ack_wait_queue.pop(ack_id);
                    self.log_data(message_type.ACK, str(original_packet.send_time) + "," + str(self.current_time))                    
                    self.tasks_queue[original_packet.task_id].set_packet_ack(original_packet.seq_num ,True);
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
            self.message_system.upload_data(new_packet);
        self.current_time += self.time_decay;

    def create_data_packet(self, receiver_id, task_id, data_type=message_type.DATA):
        new_packet = packet(self.system_id, receiver_id, task_id, self.current_time, self.sequence_number, data_type);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_req_packet(self, receiver_id, task_id, request, data_type=message_type.REQ):
        new_packet = packet(self.system_id, receiver_id, task_id, self.current_time, self.sequence_number, data_type, request=request);
        self.sequence_number += 1;
        if self.sequence_number % 2147483647 == 0:
            self.sequence_number = 0;
        return new_packet;

    def create_ack_packet(self, received_packet):
        new_packet = packet(self.system_id, received_packet.sender_id, received_packet.task_id, self.current_time, received_packet.seq_num, data_type=message_type.ACK);
        return new_packet;

    