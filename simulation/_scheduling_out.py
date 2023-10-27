import pandas as pd
from Simulation import Simulation
from pathlib import Path
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(
                  os.path.dirname(__file__), 
                  os.pardir)
)
sys.path.append(PROJECT_ROOT)

import scheduling
choice = scheduling.choice

settings = pd.read_csv(str(Path(__file__).parent.parent) + '/scheduling/outputs/' + choice +'/settings.csv')
settings_dict = dict(zip(settings.attribute,settings.value))
scenario = settings_dict['scenario']
schedule = settings_dict['schedule']

inputs_description = pd.read_csv(str(Path(__file__).parent.parent)+ '/inputs_description.csv')
inputs_dict = dict(zip(inputs_description.Scenario_id.astype(str),inputs_description.File_name))
input_path =  str(Path(__file__).parent.parent) + '/scenarios/' + inputs_dict[scenario]

out_path = str(Path(__file__).parent.parent) + '/scheduling/outputs/' + choice +'/graphs/'
settings_path = str(Path(__file__).parent.parent) + '/scheduling/outputs/' + choice + '/'

start_time = int(settings_dict['start_time'])
end_time = int(settings_dict['end_time'])
time_step = int(settings_dict['time_step'])

def run_simulation(start_time,end_time, time_step, schedule, input_path, settings_path, direction):
    s = Simulation(start_time,end_time,time_step)
    s.load(schedule, input_path, settings_path, direction)
    print('loading complete')
    s.run()
    print('run complete')
    s.outputFigs(out_path, direction)
    print('output complete')

for direction in [0,1]:
    run_simulation(start_time,end_time, time_step, schedule, input_path, settings_path, direction)