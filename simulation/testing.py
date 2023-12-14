import pandas as pd
from Simulation import Simulation
from Output import outputFigs
from pathlib import Path

settings = pd.read_csv(str(Path(__file__).parent.parent) + '/settings.csv')
settings_dict = dict(zip(settings.attribute,settings.value))
settings_path = 'None'
scenario = settings_dict['scenario']
schedule = settings_dict['schedule']

inputs_description = pd.read_csv(str(Path(__file__).parent.parent)+ '/inputs_description.csv')
inputs_dict = dict(zip(inputs_description.Scenario_id.astype(str),inputs_description.File_name))

input_path =  str(Path(__file__).parent.parent) + '/scenarios/' + inputs_dict[scenario]
# out_path = str(Path(__file__).parent.parent) + '/outputs/'
out_path = 'outputs/'

start_time = int(settings_dict['start_time'])
end_time = int(settings_dict['end_time'])
time_step = int(settings_dict['time_step'])

def run_simulation(start_time,end_time, time_step,input_path, settings_path):
    s = Simulation(start_time,end_time,time_step)
    s.load(settings,input_path, settings_path)
    print('loading complete')
    vehicle_info, stops = s.run()
    print('run complete')
    outputFigs(out_path, vehicle_info, stops)
    print('output complete')

run_simulation(start_time,end_time, time_step,input_path, settings_path)