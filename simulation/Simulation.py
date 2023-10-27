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
        loadData(self, schedule, input_path, settings_path)

    
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
                        total_distance = (vehicle.totalDistance)
                    else:
                        total_distance = vehicle.route.length - (vehicle.totalDistance)
                    block_speed = vehicle.currentHeadLocation.maxSpeed
                except Exception as e: 
                    # print('find the exception')
                    # print(e)
                    try: 
                        location_id = vehicle.currentHeadLocation.id
                    except:
                        location_id = None
                    location_distance = None
                    total_distance = (vehicle.totalDistance)
                    block_speed = None
                try:
                    master_block = vehicle.masterBlock.id
                    sub_block = vehicle.subBlock.id,
                except:
                    master_block = None
                    sub_block = None
                try:
                    signal_name = vehicle.relatedSignal.name
                except:
                    signal_name = ''
                self.vehicleInfo.append([self.currentTime,vehicle.id,vehicle.route.id,vehicle.state, vehicle.currentSpeed,vehicle.currentTrack.id, \
                    block_speed,location_id,location_distance, total_distance, master_block, sub_block, vehicle.route.direction_id, signal_name])
    
        return(self.vehicleInfo, self.stops)
            

