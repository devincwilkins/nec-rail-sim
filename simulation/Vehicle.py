from Stop import Stop
from Event import *
from Track import Section
from scipy import integrate
import numpy as np
import math
import time

#Global Variables
g = 9.8 #gravitational constant in m/s^2

class Vehicle(object):
    def __init__(self,ID,pullout_time,pullin_time,route_sequence,max_speed,max_acc,\
                 max_dec,normal_dec,capacity,length, signal_system, max_cant_deficiency, \
                 track_resistance, initial_acceleration, power, mass, brake_coef, brake_power):
        self.id = ID
        self.route_sequence = route_sequence
        self.pulloutTime = pullout_time
        self.pullinTime = pullin_time
        self.state = 'Prepare to pull in'
        self.maxSpeed = max_speed
        self.maxAcc = max_acc
        self.maxDec = max_dec
        self.normalDec = normal_dec
        self.capacity = capacity
        self.length = length
        self.totalDistance = 0
        self.trackSection = None
        self.signalAspect = 'g'
        self.signalSystem = signal_system
        self.maxCantDeficiency = max_cant_deficiency
        self.trackResistance = track_resistance
        self.initialAcceleration = initial_acceleration

        self.idealSpeed = max_speed
        self.constrainedSpeed = max_speed * 0.5
        self.goalSpeed = 0

        self.route = route_sequence[0]   
        self.tripNo = 0

        self.futureEvents = self.route.components
        self.futureEvents = self.route.components           # update when vehicle tail leaves a block or stop
        self.passengers = []

        self.currentTrack = None #set to 7 for OB's and 5 for IB's
        self.currentSpeed = 0
        self.currentAcceleration = 0
        self.nextSpeed = 0
        self.nextAcceleration = 0
        self.movement = 0
        self.currentHeadLocation = None        # vehicle head location: A facility (block or stop)
        self.currentTailLocation = None
        self.currentHeadLocationDistance = 0   # distance from the origin of that facility (0 to length)
        self.currentTailLocationDistance = 0 
        self.nextHeadLocation = None
        self.nextTailLocation = None
        self.nextHeadLocationDistance = 0
        self.nextTailLocationDistance = 0
        self.newState = True             # a newly trainsitioned state is True
        self.stopSlotId = 0              # stop slot id for stations
        self.expectedDwellTime = 0       # expected dwell time
        self.expectedTurnAroundTime = 0  # expected turn around time
        self.expectedPulloutTime = 0     # expected time to pull out
        self.decTime = 0                 # duration to decelerate to 0 with normaldec
        self.expectedDecTime = 0         # expected time before decelerating
        self.expectedDecDistance = 0     # expected deceleration distance before stopping
        self.expectedStopTime = 0        # expected time to stop
        self.relatedSignal = 'g'       # update whenerver head location changes
        self.power = power
        self.mass = mass
        self.brakeCoef = brake_coef
        self.brakePower = brake_power
        self.segment_index = int(self.route.start_block.trackSegment)
        #set track distance depending on direction of movement
        if self.route.direction_id == 0:
            self.trackDistance = self.route.start_block.startLocation
        elif self.route.direction_id == 1:
            self.trackDistance = self.route.start_block.endLocation
        else:
            print("Error processing route direction")
            exit()
        self.trackSequence = None
        self.stopsSequence = None
        self.stops_idx = 0
        self.track_idx = 0
        self.trackRefLocations = None
        self.nextTrackSection = None
        self.nextTrackDistance = self.trackDistance

    def checkSignals(self):
        #This function needs to absorb all the differences in the possible signalling systems
        #Each signal system should be its own class with its own signalling system, with a function that returns "g", "y", "r"
        None

    def dwellAtStation(self):
        None

    def runningResistance(self):
        #current speed is kept in m/s but track resistance (drag) terms needs v in km/hr
        v = self.currentSpeed
        return (self.trackResistance[0] + self.trackResistance[1]*v \
                + self.trackResistance[2]*(v**2))/self.mass

    def getNextAcceleration(self):
        running_resistance = self.runningResistance()
        if self.currentSpeed != 0:
            normalAcceleration = (self.power/self.mass)/self.currentSpeed - running_resistance
            # acceleration = min(normalAcceleration ,self.initialAcceleration)
            acceleration = +1 / max(1/normalAcceleration ,1/self.initialAcceleration)
        else:
            acceleration = self.initialAcceleration
        # print(f"acceleration is {acceleration:>6.2f} - V: {self.currentSpeed:>6.2f}")
        return acceleration 
    
    def getNextDeceleration(self):
        running_resistance = self.runningResistance()
        normalDeceleration = ((self.power/self.mass)/self.currentSpeed) + running_resistance 
        deceleration = -1 / max(1/normalDeceleration ,1/self.initialAcceleration)
        # print(f"deceleration is {deceleration:>6.2f} - V: {self.currentSpeed:>6.2f}")
        return deceleration 

    def updateDecelDistance(self, vf):
        func = lambda x : max((x**2)/(self.power/self.mass + \
            (self.trackResistance[0]/self.mass)*x + (self.trackResistance[1]/self.mass)*x**2 + \
                (self.trackResistance[2]/self.mass)*x**3),x/self.initialAcceleration)

        def integratel(f,a,b,n):
            a1 = float(a)
            b1 = float(b)
            y = 0
            for i in range(0,n):
                y = y + f(a1 + (b1-a1)*i/n)
            return y*(b1-a1)/n
        braking_distance = integratel(func,vf,self.currentSpeed,60)
        return max(0,braking_distance)

    def updateMaxSpeed(self):
        # track_speed = self.calculateSectionSpeed(self.trackSection)
        track_speed = self.trackSection.calculateSectionSpeed(self)
        return(track_speed)
    
    def transitionState(self,currentTime):
        print(self.state)
        #  'Prepare to pull in' case
        if self.state == 'Prepare to pull in':
            self.trackSequence, self.stopsSequence, self.trackRefLocations = self.getSectionsSequence
            track = self.route.components[0].track
            stop = self.futureEvents[1].stop
            self.currentTrack = track
            self.trackSection = self.currentTrack.components[self.segment_index] #DWREV
            self.nextTrackSection = self.trackSection ## DWREV
            #  'Prepare to pull in' -> 'Dwell at station'
            if currentTime >= self.pullinTime and abs(self.trackDistance - stop.eastBound) < 100: #and stop.occupied == False: 
                self.state = 'Dwell at station'
                self.newState = True
                self.currentHeadLocation = stop
                self.currentTailLocation = stop
                self.nextHeadLocation = stop
                self.nextTailLocation = stop
                self.stopLocationId, self.nextHeadLocationDistance = \
                    stop.setVehicleStopSlot(self)
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length*(2*self.route.direction_id - 1)
                self.futureEvents = self.route.components[1:]
            #   'Prepare to pull in' -> 'Constrained Move'
            #   'Prepare to pull in' -> 'Free Move'
            elif currentTime >= self.pullinTime:
                self.state = 'Free move'
                self.newState = True
                self.currentHeadLocation = self.route.start_block
                self.currentTailLocation = self.route.start_block
                self.nextHeadLocation = self.route.start_block
                self.nextHeadLocationDistance = 0
                self.nextTailLocation = self.route.start_block
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length*(2*self.route.direction_id - 1)
                self.futureEvents = self.route.components[1:]
            else:
                self.state = 'Prepare to pull in'

        #  'Dwell at station' case
        elif self.state == 'Dwell at station':
            #  A vehicle stops ahead, cannot move
            if self.currentHeadLocation.checkVehicleAhead(self.stopSlotId) == True:
                self.state = 'Dwell at station'
            #  Terminal station case
            elif len(self.futureEvents) <= 1:
                #  'Dwell at station' -> 'Ready to pull out'
                if self.expectedDwellTime <= 0 and currentTime >= self.pulloutTime:
                    self.state = 'Ready to pull out'
                    self.newState = True
                # elif self.expectedDwellTime <= 0 and len(self.route_sequence) == 0: #and there are NO routes left in route sequence
                #     self.deactivate(simulation)
                #     self.state = 'Ready to pull out'
                #     self.newState = True       
                #  'Dwell at station' -> 'Turn around'
                elif self.expectedDwellTime <= 0 and currentTime < self.pulloutTime:
                    self.state = 'Turn around'
                    self.newState = True
                #  'Dwell at station' -> 'Dwell at station'
                elif self.expectedDwellTime > 0:
                    self.state = 'Dwell at station'
            #  Nonterminal station case
            elif self.currentHeadLocation != self.route.components[-1]:
                # 'Dwell at station' -> 'Free move'
                if self.expectedDwellTime <= 0 and self.signalAspect == 'g':
                    self.state = 'Free move'
                    self.newState = True
                    self.futureEvents = self.futureEvents[1:]
                    self.stops_idx +=1
                # 'Dwell at station' -> 'Constrained move'
                elif self.expectedDwellTime <= 0 and self.signalAspect == 'y':
                    self.state = 'Constrained move'
                    self.newState = True
                # 'Dwell at station' -> 'Dwell at station'
                elif self.expectedDwellTime > 0 or self.signalAspect == 'r':
                    self.state = 'Dwell at station'
                else:
                    print("Error with Vehicle Object in Dwell At Station Case")
                    print("Expected dwell time is " + str(self.expectedDwellTime))
                    print("Signal aspect is " + str(self.signalAspect))
                    exit()

        #  'Free move' case
        elif self.state == 'Free move':
            self.currentHeadLocation = self.trackSection
            #  'Free move' -> 'Decelerate to stop at red'
            brake_distance = self.updateDecelDistance(0) + self.currentSpeed
            print("="*100)
            print(f"instance check: {isinstance(self.futureEvents[0],StationStop)}")
            print(f"brake_distance check: {brake_distance}")
            try:
                print(f"bounds check: {self.futureEvents[0].stop.eastBound - self.trackDistance}")
            except:
                print("bounds check: Next event not a stop")
                print(f"Next event is CP {self.futureEvents[0].controlPoint.name}")
            print("="*100)
            #if next event is a stop event type
            #if distance to stop less than brake distance
            if self.signalAspect == 'r': #AND distance to that related signal <= self.stopping distance 
                self.state = 'Decelerate to stop at red'
                self.newState = True
            #  'Free move' -> 'Constrained move'
            elif self.signalAspect == 'y':
                self.state = 'Constrained move'
                self.newState = True
            #  'Free move' -> 'Move and stop at station'
            elif isinstance(self.futureEvents[0],StationStop) and \
                    brake_distance > self.futureEvents[0].stop.eastBound - self.trackDistance \
                        and self.route.direction_id == 0: 
                self.state = 'Move and stop at station'
                self.newState = True
            elif isinstance(self.futureEvents[0],StationStop) and \
                brake_distance > - self.futureEvents[0].stop.westBound + self.trackDistance \
                    and self.route.direction_id == 1: #west_bound for oopposite direction trains
                self.state = 'Move and stop at station'
                self.newState = True
            elif isinstance(self.futureEvents[0],ControlPointManeuver) and \
                    self.updateDecelDistance(self.futureEvents[0].controlPoint.speed) > \
                        self.futureEvents[0].controlPoint.controlTrackLocation - (self.trackDistance):
                if self.futureEvents[0].controlPoint.controlTrackLocation - (self.trackDistance) < 0:
                    self.state = 'Maneuver at Control Point'
                    self.newState = True
                else:
                    self.state = 'Decelerate to Control Point'
                    self.newState = True
            #  'Free move' -> 'Free move'
            else: 
                self.state = 'Free move'

        elif self.state == 'Maneuver at Control Point': 
            if self.expectedOperationTime <= 0 and self.signalAspect == 'g':
                control_point = self.futureEvents[0].controlPoint
                self.currentTrack = control_point.aheadTrack
                self.trackDistance = control_point.aheadTrackLocation
                #locate segment index from location?
                self.segment_index = int(control_point.aheadTrackSegment)
                # self.trackSection = self.currentTrack.components[self.segment_index] #DWREV
                # self.nextTrackSection = self.trackSection #DWREV
                #deal with trackSection and segment_index too!
                self.state = 'Free move'
                self.newState = True
                self.futureEvents = self.futureEvents[1:]
                # print(self.futureEvents)
            else:
                # print("check 2")
                # exit()
                self.state = 'Maneuver at Control Point'

        elif self.state == 'Decelerate to Control Point':
            if self.route.direction_id == 0:
                move_difference = self.futureEvents[0].controlPoint.controlTrackLocation - (self.trackDistance) #(pos direction/ towards DC)
            else:
                move_difference = - self.futureEvents[0].controlPoint.controlTrackLocation + self.trackDistance #(neg direction/ towards BOS)
            print(f"cp speed: {self.futureEvents[0].controlPoint.speed}")
            print(f"move difference: {move_difference}")
            if self.currentSpeed <= self.futureEvents[0].controlPoint.speed and move_difference <= 0:
                self.state = 'Maneuver at Control Point'
                self.newState = True
            else:
                self.state = 'Decelerate to Control Point' 


        # 'Constrained move' case
        elif self.state == 'Constrained move':
            #  'Constrained move' -> 'Decelerate to stop at red'
            if self.signalAspect == 'r':
                self.state = 'Decelerate to stop at red'
                self.newState = True
            #  'Constrained move' -> 'Move and stop at station'
            elif isinstance(self.headFutureRoute[1],Stop) and \
                self.signalAspect == 'g'and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=500: 
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Constained move' -> 'Free move'
            elif self.signalAspect == 'g':
                self.state = 'Free move'
                self.newState = True
            #  'Constrained move' -> 'Constrained move'
            else: 
                self.state = 'Constrained move'

        
        #  'Decelerate to stop at red'
        elif self.state == 'Decelerate to stop at red':
            #  'Decelerate to stop at red' -> 'Stop at red'
            if self.currentSpeed == 0:
                self.state = 'Stop at red'
                self.newState = True
            #  'Decelerate to stop at red' -> 'Move and stop at station'
            elif isinstance(self.headFutureRoute[1],Stop) and \
                self.signalAspect == 'g'and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=200 and \
                        self.headFutureRoute[1].id not in self.route.skips: 
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Decelerate to stop at red' -> 'Free move'
            elif self.signalAspect == 'g':
                self.state = 'Free move'
                self.newState = True
            #  'Decelerate to stop at red' -> 'Constrained move'    
            elif self.signalAspect == 'y':
                self.state = 'Constrained move'
                self.newState = True
            #  'Decelerate to stop at red' -> 'Decelerate to stop at red'
            else:
                self.state = 'Decelerate to stop at red'


        # 'Stop at red' case
        elif self.state == 'Stop at red':
            #  'Stop at red' -> 'Move and stop at station'
            if isinstance(self.headFutureRoute[1],Stop) and self.signalAspect == 'g':
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Stop at red' -> 'Free move'
            elif self.signalAspect == 'g':
                self.state = 'Free move'
                self.newState = True
            #  'Stop at red' -> 'Constrained move'    
            elif self.signalAspect == 'y':
                self.state = 'Constrained move'
                self.newState = True
            #  'Stop at red' -> 'Stop at red'
            else:
                self.state = 'Stop at red'
        

        # 'Move and stop at station' case
        elif self.state == 'Move and stop at station':
            #  'Move and stop at station' -> 'Dwell at station'
            if self.currentSpeed == 0:
                self.state = 'Dwell at station'
                self.newState = True
                self.currentHeadLocation = self.futureEvents[0].stop
            #  'Move and stop at station' -> 'Move and stop at station'
            if self.currentSpeed > 0:
                self.state = 'Move and stop at station'


        # 'Turn around' case
        elif self.state == 'Turn around':
            #  'Turn around' -> 'Dwell at station'
            if self.expectedTurnAroundTime <= 0 and self.route.components[0].occupied == False:
                self.state = 'Dwell at station'
                self.newState = True
                self.stopLocationId, self.nextHeadLocationDistance = \
                self.route.components[0].setVehicleStopSlot(self)
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length
                self.headFutureRoute = self.route.components
                self.tailFutureRoute = self.route.components
                self.relatedSignal = None
            #  'Turn around' -> 'Turn around'
            else:
                self.state = 'Turn around'


        # 'Ready to pull out' case
        elif self.state == 'Ready to pull out':
            self.state = 'Ready to pull out'



    def action(self,timestep,simulation):


        #  'Prepare to pull in' case
        if self.state == 'Prepare to pull in':
            if self.newState == True:
                pass
                self.newState = False
            elif self.newState == False:
                pass 


        #  'Dwell at station' case
        elif self.state == 'Dwell at station':
            if self.newState == True:
                # a dwell time model needed to replace here
                self.expectedDwellTime = self.currentHeadLocation.passengerAlightBoard(self,simulation.currentTime)
                self.nextSpeed = 0
                self.nextAcceleration = 0
                self.newState = False
            else:
                self.expectedDwellTime -= timestep


        #  'Free move' case
        elif self.state == 'Free move':
            if self.newState == True:
                self.newState = False
            #  determine the acceleration in the next time step
            if self.currentSpeed < self.goalSpeed:
                if self.currentSpeed + self.getNextAcceleration() * timestep <= self.goalSpeed:
                    self.nextAcceleration = self.getNextAcceleration()
            elif self.currentSpeed == self.goalSpeed:
                self.nextAcceleration = 0
            else:
                self.nextAcceleration = self.getNextDeceleration()
            # move
            # try:
            self.move(timestep,simulation)
            # except:
            #     print(f"error at {self.trackSection.id}")
            #     print(f"segment not in {self.currentTrack.id} components")
            #     exit()

        
        #  'Constrained move' case
        elif self.state == 'Constrained move':
            if self.newState == True:
                self.newState = False
            # determine the acceleration in the next time step
            if self.currentSpeed <= self.constrainedSpeed:
                if self.currentSpeed + self.getNextAcceleration() * timestep >= self.constrainedSpeed:
                    self.nextAcceleration = self.getNextAcceleration()
                else:
                    self.nextAcceleration = self.getNextAcceleration()
            if self.currentSpeed > self.constrainedSpeed:
                if self.currentSpeed +  self.getNextDeceleration() * timestep <= self.constrainedSpeed:
                    self.nextAcceleration = self.getNextDeceleration()
                else:
                    self.nextAcceleration =  self.getNextDeceleration()
            # move
            self.move(timestep,simulation)
        

        #  'Decelerate to stop at red' case
        elif self.state == 'Decelerate to stop at red':
            # determine the acceleration in the next time step
            if self.newState == True:
                self.decTime = ((-self.currentSpeed/self.normalDec)//timestep+1)*timestep    # with buffer
                self.expectedDecDistance = 0.5*self.decTime*self.currentSpeed                # with buffer                         
                self.expectedDecTime = \
                    ((self.currentHeadLocation.length - self.currentHeadLocationDistance - self.expectedDecDistance)/max(self.currentSpeed,0.1))//timestep*timestep                               # with buffer
                self.expectedStopTime = self.expectedDecTime + self.decTime
                self.nextAcceleration = 0
                self.expectedDecTime -= timestep #time until starting to decelerate
                self.expectedStopTime -= timestep #time until finished decelerating 
                self.newState = False
            else:
                if self.expectedDecTime > 0:
                    self.nextDeceleration = 0
                elif self.expectedDecTime <= 0:
                    if self.currentSpeed + self.normalDec < 0:
                        self.nextDeceleration = self.getNextDeceleration()
                    else:
                        self.nextAcceleration = self.normalDec
                self.expectedDecTime -= timestep
                self.expectedStopTime -= timestep
            # move
            self.move(timestep,simulation)


        #  'Stop at red' case
        elif self.state == 'Stop at red':
            if self.newState == True:
                self.nextSpeed = 0
                self.nextAcceleration = 0
                self.newState = False
            else:
                pass

        # 'Move and stop at station' case
        elif self.state == 'Move and stop at station':
            if self.newState == True:
                self.stopSlotId, distance = self.futureEvents[0].stop.setVehicleStopSlot(self)
                if self.currentSpeed > 0:
                    self.nextAcceleration = self.getNextDeceleration()
                self.newState = False
            else:
                if self.currentSpeed > 0:
                    self.nextAcceleration = self.getNextDeceleration()
            # move
            self.move(timestep,simulation)

        
        #  'Turn around' case
        elif self.state == 'Turn around':
            if self.newState == True:
                self.tripNo +=1
                if self.tripNo == len(self.route_sequence):
                    self.deactivate(simulation)
                    # print('trip number: ' + str(self.tripNo))
                    self.currentHeadLocation.stopSlots[self.stopSlotId] = None    # clear the terminal
                else:
                    self.route = self.route_sequence[self.tripNo]
                    self.nextHeadLocation,self.nextTailLocation = None, None
                    self.nextSpeed = 0
                    self.expectedTurnAroundTime = self.currentHeadLocation.turnaroundTime
                    self.newState = False
                    self.currentHeadLocation.stopSlots[self.stopSlotId] = None    # clear the terminal
            else:
                self.expectedTurnAroundTime -= timestep
            

        #  'Ready to pull out' case
        elif self.state == 'Ready to pull out':
            if len(self.route_sequence) == 0:
                self.deactivate(simulation)
            if self.newState == True:
                self.nextHeadLocation,self.nextTailLocation = None, None
                self.nextSpeed = 0
                self.expectedPulloutTime = self.currentHeadLocation.turnaroundTime / 2 
                self.newState = False
                self.currentHeadLocation.stopSlots[self.stopSlotId] = None    # clear the terminal
            else:
                self.expectedPulloutTime -= timestep
            if self.expectedPulloutTime <= 0:
                self.deactivate(simulation)
        
        elif self.state == 'Maneuver at Control Point':
            if self.currentSpeed < self.goalSpeed:
                if self.currentSpeed + self.getNextAcceleration() * timestep <= self.goalSpeed:
                    self.nextAcceleration = self.getNextAcceleration()
            elif self.currentSpeed == self.goalSpeed:
                self.nextAcceleration = 0
            else:
                self.nextAcceleration = self.getNextDeceleration()
            if self.newState == True:
                self.track = self.futureEvents[0].controlPoint.aheadTrack
                try:
                    self.expectedOperationTime = self.length/self.currentSpeed
                except:
                    self.expectedOperationTime = 0
                self.newState = False
            else:
                self.expectedOperationTime -= timestep
            # move
            self.move(timestep,simulation)

        elif self.state == 'Decelerate to Control Point':
            print(f"CP ID: {self.futureEvents[0].controlPoint.id}")
            if self.currentSpeed < self.goalSpeed:
                if self.currentSpeed + self.getNextAcceleration() * timestep <= self.goalSpeed:
                    self.nextAcceleration = self.getNextAcceleration()
            if self.currentSpeed == self.goalSpeed:
                self.nextAcceleration = 0
            elif self.currentSpeed == 0:
                self.nextAcceleration = 0
                print("stopped before moved thru CP")
                exit()
            else:
                self.nextAcceleration = self.getNextDeceleration()
            if self.newState == True:
                self.newState = False
            # move
            self.move(timestep,simulation)

    def update(self, simulation):
        '''
        update the vehicle location, speed, acceleration (next->current)
        update the block/stopslot occupancy
        update related signal of vehicle
        '''

        if self.nextHeadLocation == None:    # terminal station case (pull in/pull out/turn around)) 
            self.currentHeadLocation = self.nextHeadLocation
            self.currentTailLocation = self.nextTailLocation
            self.totalDistance = 0
            return
        
        # enter a new block
        # enter stop case realized in action function
        if self.nextHeadLocation != self.currentHeadLocation:
            self.nextHeadLocation.vehicles.append(self)
        # leave a stop or block        
        if self.nextTailLocation != self.currentTailLocation:
            if isinstance(self.currentTailLocation,Section):
                self.currentTailLocation.vehicles.remove(self) 
            elif isinstance(self.currentTailLocation,Stop):
                self.currentTailLocation.stopSlots[self.stopSlotId] = None
                self.currentTailLocation.vehicles.remove(self) 
        # update
        self.currentSpeed = self.nextSpeed
        self.currentTailLocation = self.nextTailLocation
        self.currentHeadLocationDistance = self.nextHeadLocationDistance
        self.currentTailLocationDistance = self.nextTailLocationDistance
        ## UPDATE currentTrack
        if self.nextTrackSection.track != self.trackSection.track:
            self.currentTrack = simulation.trackDict[self.nextTrackSection.track]
        self.trackDistance = self.nextTrackDistance
        self.trackSection = self.nextTrackSection
        # if self.trackSection not in self.currentTrack.components:
        #     print("Error: trackSection not in currentTrack.")
        #     print(f"self.trackSection is on : {self.trackSection.track}")
        #     print(f"while self.currentTrack is: {self.currentTrack.id}")
        #     exit()

    def deactivate(self,simulation):
        simulation.activeVehicles.remove(self)
        print('deactivating vehicle ' + str(self.id))

    def updateDangerPoint(self):
        #Danger points are the end locations of all currently moving trains
        None

    def updateSignalAspect(self): #Moving block
        #signal aspect yellow if distance to next train is < braking distance + safety_margin
        #signal aspect red if distance to next train is < braking distance
        None

    def getLastSegment(self,prev_last_segment):
            for event in self.futureEvents:
                if isinstance(event,ControlPointManeuver):
                    last_segment_id = int(event.controlPoint.controlTrackSegment)
                    last_segment = event.controlPoint.controlTrack.components[last_segment_id]
                    if last_segment not in prev_last_segment:
                        cp = event.controlPoint
                        return(last_segment,cp)
            last_segment = self.currentTrack.components[-1]
            return(last_segment, None)
    
    def getNextStop(self):
        for event in self.futureEvents:
            if isinstance(event,StationStop):
                next_stop = event.stop
                return(next_stop)

    ###########################################

    @property
    def getSectionsSequence(self):
        """Translate self.futureEvents into lists of Sections and Stops."""
        sequence = []
        stops = []
        tracks_reference_locations = {}
        last_cp = None
        components_start_idx = self.segment_index
        components_end_idx = -1

        ## Traverse all future events and append in its respective list
        for _,e in enumerate(self.route.components):
        # for _,e in enumerate(self.futureEvents):
            if isinstance(e,ControlPointManeuver):
                components_end_idx = int(e.controlPoint.controlTrackSegment) #adding everything between the last cp and this one

                sequence += e.controlPoint.controlTrack.components[components_start_idx:(components_end_idx + 1)]
                
                ## Necesary to translate self.trackDistance into relative distance
                tracks_reference_locations[e.controlPoint.controlTrack.id] = {
                    'start': e.controlPoint.controlTrack.components[0].startLocation,
                    'end': e.controlPoint.controlTrack.components[-1].endLocation
                }

                last_cp = e.controlPoint
                components_start_idx = int(e.controlPoint.aheadTrackSegment) #CP ahead track segment utilizes ordered_id

            elif isinstance(e,StationStop):
                stops.append(e.stop)

        ## INSERT THE LAST GROUP OF SECTIONS FROM CP.aheadTrack.components
        if last_cp:
            seq_idx = sequence.index(last_cp.controlTrack.components[components_end_idx ])
            sequence = sequence[:(seq_idx+1)] + \
                last_cp.aheadTrack.components[components_start_idx:] + \
                sequence[(seq_idx+1):]
            
            tracks_reference_locations[last_cp.aheadTrack.id] = {
                    'start': last_cp.aheadTrack.components[0].startLocation,
                    'end': last_cp.aheadTrack.components[-1].endLocation
                }
        return sequence, stops, tracks_reference_locations


    def setGoalSpeed(self,simulation):
        """Based on brake distance, review the speed limit of the next sections to determine if need to decelerate"""

        ## CALCULATE REFERENCE DISTANCES
        distance_to_section_end  = (self.trackSection.length - self.currentHeadLocationDistance)
        BRAKE_DIST = self.updateDecelDistance(0)

        ## CALCULATE DISTANCE TO NEXT STOP
        #something not working here, why is new haven being detected as early as kingston?
        if self.stopsSequence[self.stops_idx].track != self.currentTrack.id:
            distance_to_next_stop = self.trackSection.endLocation - self.trackDistance
            for elem in self.trackSequence[self.track_idx:]:
                if elem.track == self.stopsSequence[self.stops_idx].track:
                    if self.stopsSequence[self.stops_idx].eastBound <= elem.endLocation:
                        distance_to_next_stop += self.stopsSequence[self.stops_idx].eastBound - elem.startLocation
                        break
                    else:
                        distance_to_next_stop += elem.length
                else:
                    distance_to_next_stop += elem.length
                if distance_to_next_stop > BRAKE_DIST:
                    distance_to_next_stop = np.inf
                    break
        else:
            distance_to_next_stop = (self.stopsSequence[self.stops_idx].eastBound + self.stopsSequence[self.stops_idx].length/2) - self.trackDistance

        ## CHECK IF THE NEXT STOP IS IN BRAKE DISTANCE
        if BRAKE_DIST + self.currentSpeed > abs(distance_to_next_stop): #refine (abs)
            print(f"UPDATED SPEED AT SEC. {self.trackSection.id} to 0 (Ref: STOP. {self.stopsSequence[self.stops_idx].id})")
            print(f"current speed: {self.currentSpeed}")
            print(f"brake distance: {BRAKE_DIST}")
            print(f"distance to stop: {distance_to_next_stop}")
            return 0

        ## CHECK IF TRAIN CAN STOP WITHIN CURRENT SECTION (i.e. no need to check other sections)
        if distance_to_section_end > BRAKE_DIST:
            return self.updateMaxSpeed()

        ## IF DIST TO END OF SECTION IS LESS THAN BRAKING DIST, 
        ## CHECK THE FOLLOWING SECTIONS WITHIN THE brake_dist RANGE
        
        ## SET BENCHMARK min_distance_to_decelerate
        max_distance_needed_to_decelerate = 0
        goal_speed = self.updateMaxSpeed()
        relative_distance = distance_to_section_end #- self.currentSpeed ## TBD

        if len(self.trackSequence) > 0:
            print(f"total_distance is {self.totalDistance}")
            idx = self.track_idx
            while relative_distance < BRAKE_DIST and len(self.trackSequence) >= idx+2:
                ## For each item 
                ## 1) calculate max_speed and distance to achieve that speed
                ## 2) compare distance needed to reach element speed constraint
                ## 3) if lower distance, update benchmark
                ## 4) update relative_distance and idx
                # print(f"Distance to section end  : {relative_distance}")
                idx += 1
                event = self.trackSequence[idx]
                # print(f"trying section {event.id} of length {event.length}")
                # print(f"Relative distance  : {relative_distance}")
                tmp_speed = event.calculateSectionSpeed(self)
                tmp_distance = self.updateDecelDistance(tmp_speed)
                if (
                    tmp_distance > relative_distance and
                    (tmp_distance - relative_distance)  > max_distance_needed_to_decelerate
                ):
                    max_distance_needed_to_decelerate = tmp_distance - relative_distance
                    goal_speed = tmp_speed
                    print(f"UPDATED SPEED AT SEC. {self.trackSection.id} to {goal_speed} (Ref: SEC. {event.id})")
                relative_distance += event.length

        print(f"TIME: {simulation.currentTime}")
        if goal_speed >= 89:
            print("ALERT")
        return goal_speed


    ###########################################

    # def setGoalSpeedOLD(self,simulation):
    #     print("UNIQUE FCN CALL")
    #     print(f"BRAKE DIST: {(self.updateDecelDistance(0))}")
    # # INIT VALUES
    #     i = 1                               #counts how many track segments ahead we are looking at
    #     distance_to_i = 1                   #distance until the track segment we are looking at
    #     distance_to_s = np.inf
    #     next_stop = self.getNextStop()
    #     new_deceleration_distance = np.inf  #start with a high number as a place holder
    #     next_stop_speed = np.inf
    #     need_to_decelerate = False          #start with not needing to decelerate as a default assumption
    #     final_speed = None                  #placeholder
    #     new_speed = None                    #placeholder
    #     new_distance = None                 #placeholder
    #     priority_deceleration_distance = 0  #placeholder
    #     look_track = self.currentTrack      #dont look at an ahead track unless necessary
    #     look_segment_index = self.segment_index
    #     prev_last_segment = []
    #     last_segment, cp = self.getLastSegment(prev_last_segment)
    #     prev_last_segment.append(last_segment)
    #     tracks_covered = []
    #     distance_to_i = (self.trackSection.length - self.currentHeadLocationDistance)
    #     print(f"INTLIZED distance to i: {distance_to_i}")
    #     brake_dist = (self.updateDecelDistance(0))
    # ## IF DIST TO END OF SECTION IS LESS THAN BRAKING DIST, LOOK SECTIONS AHEAD 
    #     while distance_to_i < brake_dist - 10:
    #         if self.route.direction_id == 0:
    #             #first look at track segments and their speeds
    #         # If the idx of last_segment is not inmediately before look_segment_index use this loop
    #             while last_segment.trackSegment < (look_segment_index + i - 1) and cp!= None: #dont worry about this while still on current track, it wont be true
    #                 look_track = cp.aheadTrack
    #                 look_segment_index = cp.aheadTrackSegment
    #                 next_section = look_track.components[look_segment_index]
    #                 i = 1
    #                 last_segment, cp = self.getLastSegment(prev_last_segment)
    #                 prev_last_segment.append(last_segment)
    #                 tracks_covered.append(look_track)
    #         ## UPDATE VALUES TO NEXT  SECTION
    #             try: 
    #                 next_section = look_track.components[look_segment_index + i - 1]
    #                 print(f"NEW SECTION: {next_section.id}")
    #             except:
    #                 pass
    #             next_section_speed = self.calculateSectionSpeed(next_section)
    #             distance_to_i += next_section.length
    #             print(f"distance to i now {distance_to_i} after adding section of length {next_section.length}")
    #             if next_stop.track == look_track.id and next_stop!= None:
    #                 distance_to_s = distance_to_i + (next_stop.eastBound - next_section.endLocation)
    #                 next_stop_speed = 0
    #             if next_section_speed < self.currentSpeed: 
    #                 new_deceleration_distance = self.updateDecelDistance(next_section_speed)
    #                 new_distance = distance_to_i
    #         #if distance needed to decelerate to speed of upcoming slow zone is more than the distance to the zone
    #                 if new_deceleration_distance + self.currentSpeed >= new_distance:
    #                     # print(f"new_distance is {new_distance}")
    #                     # print(f"new_deceleration_distance is {new_deceleration_distance}")
    #                     # print(f"current speed is {self.currentSpeed}")
    #                     if new_deceleration_distance > priority_deceleration_distance: #set as 'most urgent' or 'controlling' curve 
    #                         # priority_deceleration_distance = new_deceleration_distance
    #                         # print(f"cp priority decel distance is {priority_deceleration_distance}")
    #                         print(f"section {next_section.id} on track {look_track.id} at speed {next_section_speed} is my new priority")
    #                         priority_object = next_section.id
    #                         final_speed = next_section_speed
    #             if next_stop_speed < self.currentSpeed:
    #                 new_deceleration_distance = self.updateDecelDistance(next_stop_speed)
    #                 if new_deceleration_distance + self.currentSpeed >= distance_to_s:
    #                     if new_deceleration_distance > priority_deceleration_distance: #set as 'most urgent' or 'controlling' portion of route 
    #                         priority_deceleration_distance = new_deceleration_distance
    #                         priority_object = next_stop.name
    #                         final_speed = next_stop_speed
    #             i += 1
    #         if priority_deceleration_distance > 0:
    #             need_to_decelerate = True
    #         else:
    #             need_to_decelerate = False
    #     if need_to_decelerate == True:
    #         print(f"SLOWING to {final_speed} for {priority_object} on track {look_track.id}")
    #         print(f"MY LOCATION IS at {self.trackDistance} on track {self.currentTrack.id}")
    #         print(f"TIME: {simulation.currentTime}")
    #         print (f"GOAL SPEED IS: {final_speed}")
    #         print("="*100)
    #         self.nextAcceleration = self.getNextDeceleration()
    #         return(final_speed)
    #     else:
    #         print (f"GOAL SPEED IS MAX SPEED: {self.updateMaxSpeed()}")
    #         print("="*100)
    #         return(self.updateMaxSpeed())


    def move(self,timestep,simulation):
        '''
        calculate the vehicle's speed, location in next timestep with given current speed and acceleration next time step
        '''
        self.goalSpeed = self.setGoalSpeed(simulation)
        self.nextSpeed = max(0, self.currentSpeed + self.nextAcceleration * timestep)
        self.movement = self.currentSpeed * timestep + 0.5 * self.nextAcceleration * timestep * timestep
        # print(f"movement is {self.movement}")
        if self.route.direction_id == 1:
            self.movement = self.movement * -1 
        self.totalDistance += abs(self.movement)
        if math.isnan(self.trackDistance):
            print("Error: Track Distance is not a number")
            exit()
        
        # qualifies how much i will "Overshoot" my current track segment
        # move_difference = (self.trackDistance) - self.trackSection.endLocation 
        move_difference = (
            (self.currentHeadLocationDistance + self.movement) 
            - self.trackSection.length # Already accounts for the current track section
        )
        
        ## GET SEQUENCE OF OBJECTS TO REVIEW AHEAD
        # idx = self.trackSequence.index(self.trackSection) #DWREV
        idx = self.track_idx 

        if (
                move_difference > 0 and #if I overshot my track segment
                self.route.direction_id == 0 and #if I'm a northbound train
                len(self.trackSequence) > idx + 1
            ): #if advanced to next block
            print(f"move_difference is {move_difference}")
            ## START REVIEWING NEXT SEGMENT with + 1
            n = 1
            aux_sum_sections = 0
            k = int(np.floor(move_difference/self.trackSequence[idx+1].length))
            while k > 1 and len(self.trackSequence) > (idx + n):
                aux_sum_sections += self.trackSequence[idx + n].length
                n += 1 # n should count how many track sections ahead to look
                k = int(np.floor((move_difference-aux_sum_sections)/self.trackSequence[idx + n].length))
                print(f"n is {n}")

            self.nextTrackSection = self.trackSequence[idx + n] #add back +1?
            self.track_idx = idx + n 
            print(f"NTS CASE 1: {self.nextTrackSection.id}")


            ## CHECK IF PASSED A CONTROL POINT
            # if self.trackSequence[idx].track != self.trackSequence[idx + n].track:
            #     # self.currentTrack = simulation.trackDict[track_sequence[idx + n].track]
            #     print(f"track section: {self.trackSection.id}")
            #     print(f"currentTrack: {self.currentTrack.id}")
            #     self.track_idx = #fill in here?
            # else:
            #     self.track_idx += n # TBD

            # self.nextHeadLocationDistance =  move_difference - aux_sum_sections ## TBD
            self.nextHeadLocationDistance =  move_difference - aux_sum_sections
            if self.nextHeadLocationDistance < 0:
                print("error: NHLD negative!")
                exit()
            self.nextTrackDistance = self.nextTrackSection.startLocation + self.nextHeadLocationDistance 
        elif (
                move_difference < 0 and
                self.route.direction_id == 1 and
                (self.segment_index - 1) >= 0
            ):
            next_section = self.currentTrack.components[self.segment_index]
            k = int(np.floor(move_difference/next_section.length))
            n = 0
            while k > 1 and len(self.currentTrack.components) > (self.segment_index + n):
                next_section = self.currentTrack.components[self.segment_index + n]
                k = int(np.floor(move_difference/next_section.length))
            self.segment_index -= (n+1)
            try:
                self.nextTrackSection = self.currentTrack.components[self.segment_index]
                print(f"NTS CASE 2: {self.nextTrackSection.id}")
            except:
                self.nextTrackSection = self.trackSection
                print(f"NTS CASE 3: {self.nextTrackSection.id}")
                exit()
            self.nextHeadLocationDistance =  self.movement - (self.trackSection.length - self.currentHeadLocationDistance)
            if self.nextHeadLocationDistance < 0:
                print("error: NHLD negative!2")
                exit()
            # time.sleep(0.5)
        else: #if on the same block
            # time.sleep(0.5)
            self.nextTrackDistance = self.trackDistance + self.movement #OK
            self.nextHeadLocation = self.currentHeadLocation
            self.nextHeadLocationDistance = self.currentHeadLocationDistance + self.movement
            if self.nextHeadLocationDistance < 0:
                print("error: NHLD negative!3")
                exit()
        # update the tail location in the next timestep
        if self.currentTailLocationDistance + self.movement > self.currentTailLocation.length:
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement - self.currentTailLocation.length
        else:
            self.nextTailLocation = self.currentTailLocation
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement