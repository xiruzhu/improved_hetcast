import os, sys, json
from wireless_system import wireless_system
from tqdm import tqdm
import numpy as np
# sumo -c cologne.sumocfg --remote-port=8813

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants as tc

PORT = 8813
traci.init(PORT)
simulation_data = {};
edge_id_list = traci.edge.getIDList();
random_failure = True
slowed_down_edges = {};
slow_down_incidence = 0.01

edge_dict = {};
for edge_id in edge_id_list:
    edge_dict[edge_id] = {};
for lane_id in traci.lane.getIDList():
    edge_dict[traci.lane.getEdgeID(lane_id)][lane_id] = traci.lane.getMaxSpeed(lane_id);
    
for i in tqdm(range(7200)):
    if i % 300:
        data_file = open("../data/precomputed_data_" + str(i) + ".json", "w");
        data_file.write(json.dumps(simulation_data));
        data_file.close();

    if random_failure:
        new_slowed_down_edges = {};
        for edge_id in slowed_down_edges:
            #Check slowdown time left ... 
            if slowed_down_edges[edge_id] == 0:
                #If slowdown over, restore original condition
                for lane_id in edge_dict[edge_id]:
                    traci.lane.setMaxSpeed(lane_id, edge_dict[edge_id][lane_id]);
            else:
                #Otherwise, decrement by one time left
                slowed_down_edges[edge_id] -= 1;
                new_slowed_down_edges[edge_id] = slowed_down_edges[edge_id]
        slowed_down_edges = new_slowed_down_edges;
        #At each set interval, we set a set of edges to be slowed down by certain amount of time ... 
        slow_down_mat = np.random.uniform(size=(len(edge_dict), ));
        #Generate a uniform distribution
        slow_down_mat[ slow_down_mat < slow_down_incidence] = 0;
        #Set values below threshold to zero
        selected_indices = np.nonzero(slow_down_mat)[0].tolist();
        #Select nonzero indices are slow down edges 

        selected_ids = []
        for index in selected_indices:
            selected_ids.append(edge_id_list[index]);
        #Get the list
        #Generate the speed and duration from normal distribution
        speed_distribution = np.clip(np.random.normal(loc=1.0, scale=0.2, size=(len(selected_ids), )), 0, 2);
        duration_distribution = np.clip(np.random.normal(loc=120, scale=50, size=(len(selected_ids), )), 5, 400);

        #Set the slowdown .... 
        i = 0;
        for edge_id in selected_ids:
            slowed_down_edges[edge_id] = int(duration_distribution[i])
            for lane_id in edge_dict[edge_id]:
                traci.lane.setMaxSpeed(lane_id, speed_distribution[i]);
            i += 1;

    simulation_data[i] = {};
    simulation_data[i]["vehicle_id_list"] = traci.vehicle.getIDList();
    simulation_data[i]["position"] = {};
    simulation_data[i]["current_route"] = {};
    simulation_data[i]["current_index"] = {};
    for vehicle_id in simulation_data[i]["vehicle_id_list"]:
        simulation_data[i]["position"][vehicle_id] = traci.vehicle.getPosition(vehicle_id);
        simulation_data[i]["current_route"][vehicle_id] = traci.vehicle.getRoute(vehicle_id);
        simulation_data[i]["current_index"][vehicle_id] = traci.vehicle.getRouteIndex(vehicle_id);
        if i % 50 == 0:
            traci.vehicle.rerouteTravelTime(vehicle_id);
    simulation_data[i]["edge_average_speed"] = {};
    for edge_id in edge_id_list:
        simulation_data[i]["edge_average_speed"][edge_id] = traci.edge.getLastStepMeanSpeed(edge_id);
    self.traci.simulationStep();
