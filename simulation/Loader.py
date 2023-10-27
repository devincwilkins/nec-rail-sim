import pandas as pd
from Track import *
from Route import Route
from ControlPoint import *
from Event import *
from Stop import Stop
from Vehicle import Vehicle
from collections import defaultdict

# Read input files and create object instances
# Below are input file paths

def loadData(simulation,schedule, input_path, settings_path):
    # settings_dict = dict(zip(settings.attribute,settings.value))
    # scenario = settings_dict['scenario']
    # schedule = settings_dict['schedule']

    # inputs_description = pd.read_csv(str(Path(__file__).parent.parent)+ '/inputs_description.csv')
    # inputs_dict = dict(zip(inputs_description.Scenario_id.astype(str),inputs_description.File_name))

    # input_path =  str(Path(__file__).parent.parent) + '/scenarios/' + inputs_dict[scenario]

    gtfs_path = input_path + 'gtfs_output.csv'
    block_path = input_path + 'track.csv'
    route_path = input_path + 'route.csv'
    schedule_path = input_path + 'schedule.csv'
    stop_path = input_path + 'stop.csv'
    vehicle_type_path = input_path + 'vehicle_type.csv'
    control_point_path = input_path + 'control_point.csv'
    loadGTFS(simulation, gtfs_path)
    loadTrack(simulation, block_path)
    loadStop(simulation, stop_path)
    loadRoute(simulation, route_path)
    loadControlPoint(simulation, control_point_path)
    loadVehicle(simulation, vehicle_type_path, schedule_path)

def loadGTFS(simulation,gtfs_path):
    gtfs_df = pd.read_csv(gtfs_path)
    simulation.gtfs_df = gtfs_df

def loadEvent(simulation, event_path):
    None


def loadStop(simulation, stop_path):
    stop_df = pd.read_csv(stop_path, dtype = {'Stop_location': str})
    stopList = []
    stopDict = {}
    stopNameDict = {}
    aheadBlockDict = defaultdict(dict)

    for row in stop_df.itertuples():
        ID = row.Stop_id
        name = row.Stop_name
        opposite_stop = row.Opposite_stop_id
        max_dwell = row.Max_dwell
        min_dwell = row.Min_dwell
        turnaround_time = row.Turnaround_time
        capacity = row.Capacity
        length = row.Length
        east_bound = row.East_bound
        west_bound = row.West_bound
        stop_location = [int(round(float(i))) for i in row.Stop_location.split(',')]
        stop_time = [int(round(float(i))) for i in row.Stop_location.split(',')]
        stop_aheadBlock = aheadBlockDict[ID]
        max_speed = row.Max_speed
        track = row.Track
        new_stop = Stop(ID,name,opposite_stop,max_dwell,min_dwell,turnaround_time,capacity,length, east_bound, west_bound, stop_location,stop_time, stop_aheadBlock, max_speed, track)
        stopList.append(new_stop)
        stopDict[ID] = new_stop
        stopNameDict[name] = new_stop
    simulation.stops = stopList
    simulation.stopDict = stopDict
    simulation.stopNameDict = stopNameDict


def loadTrack(simulation, track_path):
    track_df = pd.read_csv(track_path)
    track_df = track_df.sort_values(by=['Track_id', 'Start_location']).reset_index()
    trackList = []
    track_collect = []
    prev_track = None
    for idx, row in track_df.iterrows(): #[::-1]
        ID = row.Section_id
        length = row.End_location - row.Start_location
        location = row.Start_location
        max_speed = 79
        track = row.Track_id
        curvature = row.Curve_degree
        curve_direction = row.Curve_direction
        cant = row.cant
        new_section = Section(ID,length,location, max_speed,track, curvature, curve_direction, cant)
        if idx == track_df.index[-1]:
            components = track_collect
            new_track = Track(track,components) #ID is wrong
            simulation.trackDict[track] = new_track
            trackList.append(new_track)
            prev_track = None
        elif prev_track == track or prev_track == None:
            track_collect.append(new_section)
            prev_track = track
        else:
            components = track_collect
            new_track = Track(track,components) #ID is wrong
            simulation.trackDict[track] = new_track
            trackList.append(new_track)
            prev_track = None
    simulation.tracks = trackList
    print('TrackDict: ' + str(simulation.trackDict))
    # print(components)
    # exit()

def loadRoute(simulation, route_path):
    # list in sequence all stops and blocks that this route will pass
    route_df = pd.read_csv(route_path)
    routeDict = {}
    eventDict = {}

    for row in route_df.itertuples():
        ID = row.Route_id
        name = row.Route_desc
        direction_id = row.Direc
        if pd.isna(row.Event_list) == False:
            eventList = row.Event_list.split(',')
        else:
            eventList = []
        count = 0
        event_object_list = []
        for event in eventList:
            #create new event
            type = event.split('-')[0]
            code = event.split('-')[1]
            if type == 'SS':
                #code translates to stop id
                stop_id = code
                stop_object = simulation.stopDict[int(stop_id)]
                new_event = StationStop(count,stop_object)
            elif type == 'BS':
                #code translates to track to begin on
                track_id = code #grab track object?
                track_object = simulation.trackDict[int(track_id)]
                new_event = BeginService(count,track_object)
            elif type == 'CP':
                #code translates to track to switch to
                track = code
                new_event = ControlPointManeuver(count,track_object)
            eventDict[count] = new_event
            event_object_list.append(new_event)
        components = event_object_list
        new_route = Route(ID,name,components,direction_id)
        routeDict[ID] = new_route
    simulation.routeDict = routeDict


def loadControlPoint(simulation, control_point_path):
    signal_df = pd.read_csv(control_point_path)

    for row in signal_df.itertuples():
        ID = row.id
        direction = row.Direction
        type = row.Type
        if type == 'Control Point':
            name = row.Name
            new_control_point = ControlPoint(ID,name,direction)
            simulation.controlPoints.append(new_control_point)
                

def loadVehicle(simulation, vehicle_type_path, schedule_path):
    vehicle_type_df = pd.read_csv(vehicle_type_path)
    schedule_df = pd.read_csv(schedule_path)
    vehicle_df = schedule_df.merge(vehicle_type_df,on='Vehicle_type')

    for row in vehicle_df.itertuples():
        ID = row.Vehicle_id
        Route_sequence = str(row.Route_sequence).split(',')
        Route_sequence = [float(i) for i in Route_sequence]
        Route_sequence = [int(i) for i in Route_sequence]
        route_sequence = []
        for route in Route_sequence:
            route_sequence.append(simulation.routeDict[route])
        pullout_time = int(row.Pullout_time)
        pullin_time = int(row.Pullin_time)
        if_turn_around = row.If_turnaround
        max_speed = row.Max_speed
        max_acc = row.Max_acc
        max_dec = row.Max_dec
        normal_dec = row.Normal_dec
        capacity = row.Capacity
        length = row.Vehicle_length
        max_cant_deficiency = row.Max_cant_deficiency
        track_resistance = [row.a,row.b,row.c]
        initial_acceleration = row.Initial_acceleration
        power = row.Power
        mass = row.Mass
        brake_coef = row.Brake_coefficient
        signal_system = row.Signal_system
        new_vehicle = Vehicle(ID, pullout_time, pullin_time, route_sequence, \
        max_speed, max_acc, max_dec, normal_dec, capacity, length, signal_system,\
            max_cant_deficiency, track_resistance, initial_acceleration, power, mass, brake_coef)
        simulation.vehicles.append(new_vehicle)