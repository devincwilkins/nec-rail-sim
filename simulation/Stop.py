class Stop(object):
    def __init__(self,ID,name,opposite_stop,max_dwell,min_dwell,turnaround_time,capacity,length,east_bound, west_bound,stop_slot_distance,stop_slot_time, ahead_block,max_speed, track):
        self.id = ID
        self.name = name
        self.oppositeStopID = opposite_stop
        self.MaxDwell = max_dwell
        self.MinDwell = min_dwell
        self.turnaroundTime = turnaround_time
        self.passengers = []
        self.signals = []
        self.capacity = capacity
        self.length = length
        self.eastBound = east_bound
        self.westBound = west_bound
        self.stopSlots = [None]*self.capacity
        self.stopSlotDistances = stop_slot_distance     # locations of vehicle head stop point               
        self.vehicles = []
        self.occupied = False
        self.aheadBlock = ahead_block
        self.maxSpeed = max_speed
        self.track = track


    def setVehicleStopSlot(self,vehicle):
        '''
        only used for stations with available capacity
        allocate the first unoccupied slot for a vehicle entering the station (in case that capacity > 1)
        return the allocated slot index, distance and the time moving to the slot
        '''
        for idx in range(self.capacity+10):
            if idx == self.capacity -1:    # the last slot
                self.stopSlots[idx] = vehicle
                return idx, self.stopSlotDistances[idx]
            elif self.stopSlots[idx] == None:
                if self.stopSlots[idx+1] == None:
                    self.stopSlots[idx] = vehicle
                    return idx, self.stopSlotDistances[idx] 


    def checkVehicleAhead(self,slotId):
        '''
        check whether there is a vehicle stopping in the front slots (cannot move in this case)
        # if there is a vehicle stopping ahead, return True
        '''
        for idx in range(self.capacity):
            if idx == slotId:
                return False
            elif self.stopSlots[idx] != None:
                return True

    
    def passengerAlightBoard(self,vehicle,currentTime):
        num_alighting, num_boarding = 0,0
        for p in vehicle.passengers.copy():
            if p.nextDestination == self:
                p.alightAndTransfer(currentTime)
                vehicle.passengers.remove(p)
                num_alighting += 1
        available_capacity = vehicle.capacity - len(vehicle.passengers)
        for p in self.passengers.copy():
            if (p.nextDestination in vehicle.headFutureRoute) and (p.arrivalTime <= currentTime):
                if available_capacity > 0:
                    self.passengers.remove(p)
                    vehicle.passengers.append(p)
                    p.board(currentTime)
                    num_boarding += 1
                    available_capacity -= 1
                else:
                    p.deniedBoard()
        dwell_time = self.calDwellTime(num_alighting,num_boarding)
        return self.MinDwell
                

    def calDwellTime(self,num_alighting,num_boarding):
        return self.MinDwell

    
    def updateOccupancy(self):
        if self.stopSlots[-1] == None:
            self.occupied = False
        #elif len(self.vehicles) == 0 #and this stop is skippped on this route, 
            #self.occupied = False
        else:
            # if self.id == 3:
            #     print("stop Framingham occupied by" + str(self.stopSlots[-1].id))
            self.occupied = True 