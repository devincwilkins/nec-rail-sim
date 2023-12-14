from typing import DefaultDict
from Loader import loadData
from Simulation import *
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

def outputFigs(out_path, vehicleInfo, stops):
        #vehicle output spreadsheet
        output_vehicle = pd.DataFrame(vehicleInfo,\
        columns=['time','id','route','state','speed','goal_speed','track', \
                    'speed_limit','location_id','location_distance', 'total_distance', 'master_block','sub_block','route_direction','signal'])
        output_vehicle.to_csv(out_path + 'test_vehicle_output.csv')


        # output run graph

        #Needs edit: separate line for each veh id
        #group by Vid column in output_vehicle dataframe
        fig,(ax1)= plt.subplots(nrows=1,ncols=1,figsize=(15,10),sharex=True)
       
        #link stop names (stop in self.stops) to locations (block.csv)
        stopLocationDict_5 = DefaultDict(dict)
        stopLocationDict_7 = DefaultDict(dict) #generate an empty dictionary
        for stop in stops:
            if '_2' in stop.name:
                startLocation = stop.eastBound
                stopDistance = stop.stopSlotDistances[0]
                stopLocationDict_7[stop.name] = startLocation + stopDistance
            # elif '_4' in stop.name:
            #     startLocation = stop.westBound
            #     stopDistance = stop.stopSlotDistances[0]
            #     stopLocationDict_5[stop.name] = startLocation - stopDistance
        stopLocation_7 = pd.DataFrame(list(stopLocationDict_7.items()),columns = ['Stop Name','Stop Location'])
        # stopLocation_5 = pd.DataFrame(list(stopLocationDict_5.items()),columns = ['Stop Name','Stop Location'])

        # #merge stop locations to gtfs on Stop Names
        # data_df = self.gtfs_df.merge(stopLocation_df,how = 'left', left_on = 'stop_name', right_on = 'Stop Name' )

        #give train numbers (route ID) to the legend
        #color by track vehicle is on 
        i = 0
        # colors = ['g','b','r']
        # for name, group in output_vehicle.groupby('track'):
        #     route = group['route'].unique()
        #     group.plot(kind='scatter',x='time',y='total_distance', ax=ax1, label = name, c= colors[i])
        #     i+=1
        #route name dict?
        

        colors = {'1':'g','2':'g','3':'b','4':'b','5':'r','6':'r','7':'y','8':'y','9':'m','10':'m','11':'c','12':'c','13':'k','14':'k','15':'burlywood','16':'burlywood','17':'chartreuse','18':'chartreuse','20':'#000080','22':'#000080','24':'#000040','26':'#000040'}
        for name, group in output_vehicle.groupby('route'):
            group.plot(kind='scatter',x='time',y='total_distance', ax=ax1, c= colors[str(name)]) #label = routeDict[name].name
            i+=1
        #set yticks to be at the location of 'Stop Location' but labeled as 'stop_name'
        ax1.set_yticks(stopLocation_7['Stop Location'])
        ax1.set_yticklabels(stopLocation_7['Stop Name'].map(lambda x: x.rstrip('_5')), fontsize = 20)
        # ax1.set_xticklabels(np.arange(floor(self.startTime/3600), floor(self.endTime/3600), 1), fontsize = 20, rotation=45)
        ax1.set_xlabel('Time', fontsize = 30)
        ax1.set_ylabel('Location', fontsize = 30)
        ax1.yaxis.grid(True)
        ax1.set_ylim(-5000,263000)
        ax2 = ax1.twinx()
        # ax2.set_yticks(stopLocation_7['Stop Location'])
        # ax2.set_yticklabels(stopLocation_7['Stop Name'], fontsize = 25)
        # ax2.yaxis.grid(True)
        # ax2.set_ylim(-5000,240000)
        fig.set_size_inches(28.5, 18.5)
        xticks = np.arange(0,10000, 60*60)
        xticks = np.arange(0,10000, 60*60)
        ax1.set_xticks(xticks)
        ax1.set_xticklabels([f'{t//3600:2.0f}' for t in xticks], fontsize = 30)
        ax1.set_xlim(0,10000)
        ax1.legend(fontsize="25")

        plt.savefig(out_path + 'runGraph.png')

