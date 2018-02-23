#Base wireless node
from enum import Enum
from numpy.random import ranf
import math
from packet_system import packet_system;

class node_type(Enum):
    VEHICLE = 0
    RSU = 1
    LTE = 2

class access_node:
    def __init__(self, access_id, position, access_node_type, wireless_radius, upload_speed=1000, download_speed=1000, distance_error=None, collision_error=None):
        self.id = access_id;
        self.position = position;
        self.access_node_type = access_node_type;
        self.wireless_radius = wireless_radius;
        self.upload_speed = upload_speed;
        self.download_speed = download_speed;

        self.distance_error = distance_error;
        self.interference_error = collision_error;
        self.error_rate = 0;

    def compute_distance(self, position):
        dist = (position[0] - self.position[0]) ** 2 + (position[1] - self.position[1]) ** 2;
        dist = math.sqrt(dist);
        return dist;

    def is_within_rectangle(self, x_range, y_range):
        point = self.position;
        #Thus a point is within a rectangle if it's point is between x_range and y_range
        return point[0] >= x_range[0] and point[0] <= x_range[1] and point[1] >= y_range[0] and point[1] <= y_range[1]

    def line_intersect(self, line, points=20):
        d_x = (line[0][0] - line[1][0])/(points - 1);
        d_y = (line[0][1] - line[1][1])/(points - 1);
        points_in_line = [];
        current_point = line[0];
        for i in range(points):
            points_in_line.append(current_point);
            current_point = [current_point[0] - d_x, current_point[1] - d_y]
        
        for point in points_in_line:
            if self.compute_distance(point) < self.wireless_radius:
                return True;
        return False;

    def in_range_of_rect(self, x_rect, y_rect, points=30):
        if self.is_within_rectangle(x_rect, y_rect):
            return True;
        result = self.line_intersect([(x_rect[0], y_rect[0]), (x_rect[1], y_rect[0])]) or self.line_intersect([(x_rect[1], y_rect[0]), (x_rect[1], y_rect[1])])
        if result:
            return True;
        result = self.line_intersect([(x_rect[1], y_rect[1]), (x_rect[0], y_rect[1])]) or self.line_intersect([(x_rect[0], y_rect[1]), ([x_rect[0], y_rect[0]])])
        if result:
            return True;
        return False;

    def is_in_range(self, position):
        dist = self.compute_distance(position);
        return self.wireless_radius > dist;

    def update_access_node(self):
        self.error_rate = self.compute_error_rate();

    def compute_error_rate(self):
        #Returns an error rate between 0-1.00 representing how likely for a message sent to this node will fail
        print("TBD");

    def message_failed_check(self):
        #Randomly gives boolean result
        #This is based on the error rate
        #Return true if success, false if failed
        return ranf() > self.error_rate;

