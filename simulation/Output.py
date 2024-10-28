from typing import DefaultDict
from Loader import loadData
from Simulation import *
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import numpy as np

def outputFigs(out_path, vehicleInfo, stop_df):
        #vehicle output spreadsheet
        output_vehicle = pd.DataFrame(vehicleInfo,\
        columns=['time','id','route_id','route_name','state','speed','goal_speed','track', \
                    'speed_limit','location_id','location_distance', 'track_distance', 'master_block','sub_block','route_direction','signal'])
        #edit out 'Prepare to Pull-in' state
        output_vehicle = output_vehicle[output_vehicle.state != 'Prepare to pull in']
        output_vehicle.to_csv(out_path + 'test_vehicle_output.csv')
        ######
        output_vehicle = output_vehicle.assign(track_route_segment = \
                            #   (output_vehicle.sort_values(['id','time'],ascending=True).track != \
                            #     output_vehicle.sort_values(['id','time'],ascending=True).track.shift(1)).cumsum())
                              (
                                (output_vehicle.sort_values(['id','time'],ascending=True).track != output_vehicle.sort_values(['id','time'],ascending=True).track.shift(1)) | \
                                (output_vehicle.sort_values(['id','time'],ascending=True).id != output_vehicle.sort_values(['id','time'],ascending=True).id.shift(1))
                                ).cumsum())
        # output_vehicle.loc[:,['time','track_distance','track_route_segment','track']].head(50)
        ######

        # output run graph
        unique_tracks = set(output_vehicle.track.unique().tolist())
        num_tracks = len(unique_tracks)

        NCOLS = 2 #3
        NROWS = num_tracks//NCOLS + 1 if num_tracks > NCOLS else 1
        DICT_COLORS = { route_name:f'C{i}' for i,route_name in enumerate(output_vehicle.route_name.unique())}

        fig, ax_arr = plt.subplots(figsize=(20,10*NROWS), ncols=NCOLS,nrows=NROWS, sharex=True, sharey=False)
     
        # for ax in ax_arr.flatten():
        for i,track in enumerate(unique_tracks):
            if num_tracks > NCOLS:
                aux_ax = ax_arr[i//NCOLS][i%NCOLS]
            else:
                aux_ax = ax_arr[i%NCOLS]
            aux_stop_df = stop_df.query(f"Track=={track}")

            ############
            aux_y_lims_by_track = output_vehicle.query("track_distance!=0").groupby('track').track_distance.agg(['min','max']).rename(columns={'min':'min_distance','max':'max_distance'})
            aux_y_lims_by_track['distance'] = aux_y_lims_by_track.max_distance - aux_y_lims_by_track.min_distance
            aux_y_lims_by_track['max_distance'] = aux_y_lims_by_track.min_distance.values + aux_y_lims_by_track.distance.max()
            ############


            aux_output_df = output_vehicle.sort_values(['id','time'],ascending=True).query(f"track_distance!=0 and track=={track:0.0f}")
            for name, group in aux_output_df.groupby('track_route_segment'): # .groupby('route')
                # group.plot(kind='scatter',x='time',y='track_distance', ax=aux_ax) #label = routeDict[name].name
                aux_ax.plot(group.time,group.track_distance, color=DICT_COLORS.get(group.route_name.iloc[0])) #label = routeDict[name].name
            #filter stops information to each track
                
                
            aux_ax.set_yticks(aux_stop_df.loc[:,'East_bound'].sort_values(ascending=True))
            aux_ax.set_yticklabels(aux_stop_df.sort_values('East_bound',ascending=True).Stop_name, fontsize = 9) ## .map(lambda x: x.rstrip('_5'))
            aux_ax.set_xlabel('Time', fontsize = 10)
            if i%NCOLS == 0:
                aux_ax.set_ylabel('Location', fontsize = 10)
            else:
                aux_ax.set_ylabel('')
            aux_ax.yaxis.grid(True)
            aux_ax.set_ylim(aux_y_lims_by_track.loc[track].min_distance,aux_y_lims_by_track.loc[track].max_distance)
            # aux_ax.set_xlim(aux_output_df.time.min(),aux_output_df.time.max())
            # aux_ax.set_xlim(0,36000)
            # aux_ax.set_xticks(np.arange(19000,36000, 60*60))
            # aux_ax.set_xticklabels([f'{t//3600:2.0f}' for t in xticks], fontsize = 30)
        # handles, labels = aux_ax.get_legend_handles_labels()
        # fig.legend(handles, labels, loc='upper center')
        

        handles = [Line2D([0],[0],color=DICT_COLORS.get(route_name), label=str(route_name)) for route_name in DICT_COLORS]
        labels = [str(route_name) for route_name in DICT_COLORS]
        if num_tracks > NCOLS:
            ax_arr[0][NCOLS-1].legend(handles,labels,bbox_to_anchor=(1.0,1.0))
        else:
            ax_arr[NCOLS-1].legend(handles,labels,bbox_to_anchor=(1.0,1.1))

        plt.tight_layout()
        plt.savefig(out_path + 'runGraph.png')

