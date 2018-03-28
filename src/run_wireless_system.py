import os, sys
from wireless_system import wireless_system

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
simulation = wireless_system(traci, simulation_time=1200);
for i in range(8000):
    if i % 400 == 0:
        simulation.save_results("../logs/result_" + str(i) + ".json");
    simulation.update();

