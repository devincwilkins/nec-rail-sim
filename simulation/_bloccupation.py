import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import math
from testing import run_simulation
import csv

settings = pd.read_csv(str(Path(__file__).parent.parent) + '/settings.csv')
settings_dict = dict(zip(settings.attribute,settings.value))
scenario = settings_dict['scenario']
inputs_description = pd.read_csv(str(Path(__file__).parent.parent) + '/inputs_description.csv')
inputs_dict = dict(zip(inputs_description.Scenario_id,inputs_description.File_name))
input_path = str(Path(__file__).parent.parent) + '/scenarios/'+ inputs_dict[str(scenario)]

in_path = input_path
out_path = input_path + 'bloccupation/'

consider_routes = settings_dict['consider_routes'].split(',')

for i in range(11,13):
    if str(i) in consider_routes:
        #read input files
        route = i
        route_info = pd.read_csv(in_path + 'route.csv')
        block_info = pd.read_csv(in_path + 'block.csv')
        stop_info = pd.read_csv(in_path + 'stop.csv')
        signal_info = pd.read_csv(in_path + 'signal.csv')
        name_dict = dict(zip(stop_info["Stop_id"],stop_info["Stop_name"]))
        name_dict_r = dict(zip(stop_info["Stop_name"],stop_info["Stop_id"]))
        opp_stop_dict = dict(zip(stop_info["Stop_id"],stop_info["Opposite_stop_id"]))
        stop_list = route_info[route_info['Route_id'] == route]['Stop_id_list'].iloc[0].split(',')
        print(stop_list)
        try:
            skip_list = route_info[route_info['Route_id'] == route]['Skip_id_list'].iloc[0].split(',')
        except:
            skip_list = []
        print(skip_list)
        real_stop_list = []
        for item in stop_list:
            if item not in skip_list:
                real_stop_list.append(item)
        stop_list = real_stop_list
        named_stop_list = []
        for stop in stop_list:
            named_stop_list.append(name_dict[int(stop)])
            #get named stops
        print(named_stop_list)

        print("print i check " + str(i))
        #edit schedule.csv
        with open(in_path + 'schedule.csv', 'w', newline = '') as schedule:
            writer = csv.writer(schedule, delimiter=',', quotechar='|')
            schedule.truncate()
            writer.writerow(['Vehicle_id','Pullin_time','Pullout_time','If_turnaround','Vehicle_type','Route_sequence'])
            writer.writerow([1, 0, 95000, 0, 2, i])

        #run sim    
        run_simulation(0, 95000, 1, input_path, 'None', 1)

        #Create matrix 
        df_sig = pd.read_csv('/Users/work/Documents/GitHub/woosta/outputs/test_signal_output.csv')
        df_sig['time'] = df_sig['time']//60
        # df_sig = df_sig.drop_duplicates(subset = ['time','id','name','occupied']).pivot(index='id', columns='time', values='occupied').fillna(0)

        # occupation = np.zeros((signal_info['id'].max()+1, 1440))
        # coords = zip(df_sig.id, df_sig.time) 
        # for k,v in coords: #k is block, v is time
        #     occupation[int(k),int(v)] = 1 

        #Create matrix 
        df = pd.read_csv('/Users/work/Documents/GitHub/woosta/outputs/test_vehicle_output.csv')
        df['time'] = df['time']//60
        time_min = df.time.min()
        time_max = df.time.max()
        route_name = df['route'].iloc[0]

        #USE BIDIRECTIONAL NUMBERS
        tt_mat = np.zeros((18,18)) #opp_stop_dict
        # Create travel time dictionary
        for stop_i in range(len(named_stop_list)-1):
            for stop_j in range(stop_i+1,len(named_stop_list)):
                df_sub_i = df[df['location_id'] == named_stop_list[stop_i]]
                depart_i = df_sub_i['time'].iloc[-1]
                df_sub_j = df[df['location_id'] == named_stop_list[stop_j]]
                arrive_j = df_sub_j['time'].iloc[0]
                if name_dict_r[named_stop_list[stop_i]] > 18:
                    real_stop_i = int(opp_stop_dict[name_dict_r[named_stop_list[stop_i]]])
                else:
                    real_stop_i = int(name_dict_r[named_stop_list[stop_i]])
                if name_dict_r[named_stop_list[stop_j]] > 18:
                    real_stop_j = int(opp_stop_dict[name_dict_r[named_stop_list[stop_j]]])
                else:
                    real_stop_j = int(name_dict_r[named_stop_list[stop_j]])
                tt_mat[real_stop_i-1,real_stop_j-1] = arrive_j - depart_i


        df['group'] = df['track'].ne(df['track'].shift()).cumsum()
        df = df.groupby('group')
        dfs = []
        

        for name, data in df:
            dfs.append(data)
        print(dfs)


        # #need to identify time spent on reverse section
        # dir = df['route_direction'][0]
        # #At the beginning, masterblock is nan, so get rid of all these rows
        # df = df.dropna(axis = 0, subset=['master_block'])


        # min_reserve = df[df['track'] == 1-dir].time.min()
        # print("MIN RESERVE: " + str(min_reserve))
        # max_reserve = df[df['track'] == 1-dir].time.max()
        # section_blocks = df[df['track'] == 1-dir]['master_block'].to_list()

        occupation = np.zeros((block_info['Master_block'].max()+1, 1440))
        print("SHAPE: " + str(occupation.shape))
        for df_unique in dfs:
            df_unique = df_unique.dropna(axis = 0, subset=['master_block'])
            coords = zip(df_unique['master_block'], df_unique.time) 
            prev_k = None
            yellow_block = None
            for k,v in coords: #k is block, v is time
                if k != prev_k:
                    yellow_block = prev_k
                if yellow_block != None:
                    occupation[int(yellow_block),int(v)] = 1
                occupation[int(k),int(v)] = 1 
                prev_k = k

        # for k in range(len(occupation)):
        #     for v in range(len(occupation[0])):
        #         if int(v)>= min_reserve and int(v)<= max_reserve:
        #             if k in section_blocks:
        #                 occupation[int(k),int(v)] = 1

        # convert array into dataframe

        DF = pd.DataFrame(occupation[:,time_min:(time_max+1)])
        DF = DF.iloc[1:]
        DF.to_csv(out_path + 'master_block_' + str(route_name)+ '.csv', header=False, index=False)
        DF_TT = pd.DataFrame(tt_mat)
        DF_TT.to_csv(out_path +'tt_' + str(route_name) + '.csv', header=False, index=False)
        print("saving " + out_path + 'master_block_' + str(route_name)+ '.csv')
        print("saving " + out_path +'tt_' + str(route_name)+ '.csv')
        