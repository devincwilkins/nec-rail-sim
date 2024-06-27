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

    block_path = input_path + 'track.csv'
    route_path = input_path + 'route.csv'
    schedule_path = input_path + 'schedule.csv'
    stop_path = input_path + 'stop.csv'
    vehicle_type_path = input_path + 'vehicle_type.csv'
    control_point_path = input_path + 'control_point.csv'
    loadTrack(simulation, block_path)
    stops_output = loadStop(simulation, stop_path)
    loadControlPoint(simulation, control_point_path)
    loadRoute(simulation, route_path)
    loadVehicle(simulation, vehicle_type_path, schedule_path)
    return stops_output


def loadEvent(simulation, event_path):
    None


def loadStop(simulation, stop_path):
    stop_df = pd.read_csv(stop_path, dtype = {'Stop_location': str})
    stopList = []
    stopDict = {}
    stopNameDict = {}
    for row in stop_df.itertuples():
        ID = row.Stop_id
        name = row.Stop_name
        opposite_stop = row.Opposite_stop_id
        max_dwell = row.Max_dwell
        min_dwell = row.Min_dwell
        turnaround_time = row.Turnaround_time
        capacity = row.Capacity
        length = float(row.Length)
        east_bound = row.East_bound
        west_bound = row.West_bound
        stop_location = [int(round(float(i))) for i in row.Stop_location.split(',')]
        stop_time = [int(round(float(i))) for i in row.Stop_location.split(',')]
        max_speed = row.Max_speed
        track = row.Track
        new_stop = Stop(ID,name,opposite_stop,max_dwell,min_dwell,turnaround_time,capacity,length, east_bound, west_bound, stop_location,stop_time, max_speed, track)
        stopList.append(new_stop)
        stopDict[ID] = new_stop
        stopNameDict[name] = new_stop
    simulation.stops = stopList
    simulation.stopDict = stopDict
    simulation.stopNameDict = stopNameDict
    return(stop_df)


def loadTrack(simulation, track_path):
    dtype = {"Section_id": str}
    track_df = pd.read_csv(track_path, dtype = dtype)
    trackList = []
    track_collect = []
    prev_track = None
    for idx, row in track_df.iterrows():
        ID = str(row.Section_id)
        track_segment = row.Track_segment
        length = float(row.End_location - row.Start_location)
        location = row.Start_location
        max_speed = 320
        track = row.Track_id
        curvature = row.Curve_degree
        curve_direction = row.Curve_direction
        cant = row.Cant
        new_section = Section(ID,track_segment,length,location, max_speed,track, curvature, curve_direction, cant)
        simulation.sectionDict[ID]=new_section
        if idx == track_df.index[-1]:
            components = track_collect
            new_track = Track(track,components)
            simulation.trackDict[track] = new_track
            trackList.append(new_track)
            prev_track = None
            track_collect = []
        elif prev_track == track or prev_track == None:
            track_collect.append(new_section)
            prev_track = track
        else:
            components = track_collect
            new_track = Track(prev_track,components)
            simulation.trackDict[prev_track] = new_track
            trackList.append(new_track)
            prev_track = None
            track_collect = []
    simulation.tracks = trackList

def loadControlPoint(simulation, control_point_path):
    signal_df = pd.read_csv(control_point_path)
    controlPointDict = {}

    for row in signal_df.itertuples():
        ID = row.id
        name = row.Name
        control_track = simulation.trackDict[int(row.Control_track)]
        control_track_location = row.Control_track_location
        ahead_track = simulation.trackDict[row.Ahead_track]
        ahead_track_location = row.Ahead_track_location
        ahead_track_segment = row.Ahead_track_segment
        direction = row.Direction
        speed = row.Speed
        new_control_point = ControlPoint(ID,name,control_track,control_track_location,ahead_track,ahead_track_location,ahead_track_segment,direction,speed)
        simulation.controlPoints.append(new_control_point)
        controlPointDict[ID] = new_control_point
    simulation.controlPointDict = controlPointDict

def loadRoute(simulation, route_path):
    route_df = pd.read_csv(route_path)
    routeDict = {}
    eventDict = {}

    for row in route_df.itertuples():
        first = True
        ID = row.Route_id
        name = row.Route_desc
        direction_id = row.Direc
        route_type =  row.Route_type
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
            try:
                location = event.split('-')[2]
            except:
                location = '0'
            if type == 'SS':
                stop_id = code
                stop_object = simulation.stopDict[int(stop_id)]
                new_event = StationStop(count,stop_object)
                if first == True:
                    first_stop = stop_object
                    first = False
                last_stop = stop_object
            elif type == 'BS':
                track_id = code
                start_block = simulation.sectionDict[location]
                track_object = simulation.trackDict[int(track_id)]
                new_event = BeginService(count,track_object,start_block)
            elif type == 'CP':
                control_point_id = code
                control_point_object = simulation.controlPointDict[int(control_point_id)]
                new_event = ControlPointManeuver(count, control_point_object)
            eventDict[count] = new_event
            event_object_list.append(new_event)
        components = event_object_list
        new_route = Route(ID,name,components,direction_id,start_block,route_type,first_stop,last_stop)
        routeDict[ID] = new_route
    simulation.routeDict = routeDict
                

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
        brake_power = row.Brake_power
        signal_system = row.Signal_system
        new_vehicle = Vehicle(ID, pullout_time, pullin_time, route_sequence, \
        max_speed, max_acc, max_dec, normal_dec, capacity, length, signal_system,\
            max_cant_deficiency, track_resistance, initial_acceleration, power, mass, brake_coef, brake_power)
        simulation.vehicles.append(new_vehicle)