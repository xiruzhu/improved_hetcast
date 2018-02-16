#Base wireless node
class access_node:
    def __init__(self, position, wireless_radius=200):
        self.position = position;
        self.wireless_radius = wireless_radius;
    