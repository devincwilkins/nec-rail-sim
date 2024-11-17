from typing import DefaultDict
from Loader import loadData
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from Output import *

class Simulation(object):
    def __init__(self,start_time,end_time,time_step):
        self.startTime = start_time
        self.endTime = end_time
        self.currentTime = start_time
        self.timeStep = time_step
        self.stops = []
        self.stopDict = {}
        self.stopNameDict = {}
        self.blocks = []
        self.masterblocks = []
        self.trackDict = {}
        self.sectionDict = {}
        self.masterblockDict = {}
        self.stopBlockDict = {}
        self.stopMasterblockDict = {}
        self.starterBlocks = []
        self.stopConnectionDict = None   
        self.expConnectionDict = None
        self.vehicles = []
        self.activeVehicles = []
        self.passengers = []
        self.routeDict = {}
        self.controlPoints = []
        self.vehicleInfo = []
        self.passengerInfo = []
        self.signalInfo = []
        self.gtfs_df = None

    def load(self,schedule, input_path, settings_path):
        return loadData(self, schedule, input_path, settings_path)

    
    def run(self):
        self.activeVehicles = self.vehicles
        for p in self.passengers:
            p.origin.passengers.append(p)
        while self.currentTime <= self.endTime:
            for vehicle in self.activeVehicles:
                vehicle.transitionState(self.currentTime)
                vehicle.action(self.timeStep,self)
            for vehicle in self.activeVehicles:
                vehicle.update(self)
            for block in self.blocks:
                block.updateOccupancy()
            for masterblock in self.masterblocks:
                masterblock.updateOccupancy()
            for stop in self.stops:
                stop.updateOccupancy() 
            self.currentTime += self.timeStep


            # test outputs
            for vehicle in self.activeVehicles:
                try:
                    location_id = vehicle.currentHeadLocation.name
                    location_distance = vehicle.currentHeadLocationDistance
                    if vehicle.route.direction_id == 0: 
                        track_distance = (vehicle.trackDistance)
                    else:
                        track_distance = vehicle.route.length - (vehicle.trackDistance)
                    block_speed = vehicle.updateMaxSpeed()
                except Exception as e: 
                    try: 
                        location_id = vehicle.currentHeadLocation.id
                        block_speed = vehicle.updateMaxSpeed()
                    except:
                        location_id = None
                        block_speed = None
                    location_distance = None
                try:
                    sub_block = vehicle.subBlock.id,
                except:
                    sub_block = None
                try:
                    signal_name = vehicle.relatedSignal.name
                except:
                    signal_name = ''
                self.vehicleInfo.append([self.currentTime,vehicle.id,vehicle.route.id,vehicle.route.name,vehicle.state, vehicle.currentSpeed,vehicle.goalSpeed,vehicle.currentTrack.id, \
                    block_speed,location_id,location_distance, vehicle.trackDistance, vehicle.totalDistance, vehicle.trackSection.id, sub_block, vehicle.route.direction_id, signal_name])
    
        return(self.vehicleInfo)
            

