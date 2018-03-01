#Definines the vehicle class

class vehicle:
    def __init__(self, vehicle_id, simulation, traci):
        self.vehicle_id = vehicle_id;
        self.simulation = simulation;
        self.traci = traci;
        self.location = traci.vehicle.getPosition(self.vehicle_id);
        
    def get_vehicle_id(self):
        return self.vehicle_id;

    def get_vehicle_location(self):
        return self.location;

    def update_system(self):
        self.location = self.traci.vehicle.getPosition(self.vehicle_id);

    