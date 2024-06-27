from Stop import Stop
from Event import *
from Track import Section
from scipy import integrate
import numpy as np
import math

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
        self.goalSpeed = 0 #self.currentHeadLocation.maxSpeed

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
        self.trackDistance = self.route.start_block.location

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
    
    def calculateSectionSpeed(self, section):
        tg = 4.7 #track gauge
        g = 32.3 #gravitational constant
        if section.curve_direction == 1 or section.curve_direction == 0 or section.curve_direction == '1' or section.curve_direction == '0': #speed formula on curves
            r = 5729.58/section.curvature #curve radius derived from degree of curvature
            curve_speed =  ((((1+((g**2)*(r**2))))/(tg/((section.cant + self.maxCantDeficiency)/12))**2)**0.25)/1.467
            track_speed = curve_speed*0.44
        else: #speed on straight sections
            if self.maxSpeed > 50:
                track_speed = 88
            else:
                track_speed = 42
        return min(track_speed, self.maxSpeed)
    
    def updateMaxSpeed(self):
        track_speed = self.calculateSectionSpeed(self.trackSection)
        return(track_speed)
    
    def transitionState(self,currentTime):
        print(self.state)
        #  'Prepare to pull in' case
        if self.state == 'Prepare to pull in':
            track = self.route.components[0].track
            stop = self.futureEvents[1].stop
            self.currentTrack = track
            self.trackSection = self.currentTrack.components[self.segment_index]
            self.nextTrackSection = self.trackSection
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
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length
                self.futureEvents = self.route.components[1:]
            #   'Prepare to pull in' -> 'Constrained Move'
            #   'Prepare to pull in' -> 'Free Move'
            elif currentTime >= self.pullinTime:
                self.state = 'Free move'
                self.newState = True
                self.currentHeadLocation = self.route.start_block
                self.currentTailLocation = self.route.start_block
                self.nextHeadLocation = self.route.start_block
                self.nextTailLocation = self.route.start_block
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length
                self.futureEvents = self.route.components[1:]
            #   'Prepare to pull in' -> 'Move and stop at station'
            # elif isinstance(self.futureEvents[0],StationStop) and \
            #         brake_distance >= self.futureEvents[0].stop.eastBound - self.trackDistance: 
            #     self.state = 'Move and stop at station'
            #     self.newState = True
            #  'Prepare to pull in'-> 'Prepare to pull in'
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
                elif self.expectedDwellTime <= 0:#len(self.route_sequence) == 0: #and there are NO routes left in route sequence
                    self.state = 'Ready to pull out'
                    self.newState = True             
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
                # 'Dwell at station' -> 'Constrained move'
                if self.expectedDwellTime <= 0 and self.signalAspect == 'y':
                    self.state = 'Constrained move'
                    self.newState = True
                # 'Dwell at station' -> 'Dwell at station'
                if self.expectedDwellTime > 0 or self.signalAspect == 'r':
                    self.state = 'Dwell at station'
        

        #  'Free move' case
        elif self.state == 'Free move':
            self.currentHeadLocation = self.trackSection
            #  'Free move' -> 'Decelerate to stop at red'
            brake_distance = self.updateDecelDistance(0)
            # print('current loc: ' + str(self.totalDistance))
            # print('next stop east bound: ' + str(self.futureEvents[0].stop.eastBound))
            # print('brake distance: ' + str(brake_distance))
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
            #if self.nextEvent == "stop at station(?_)"
            elif isinstance(self.futureEvents[0],StationStop) and \
                    brake_distance > self.futureEvents[0].stop.eastBound - self.trackDistance: 
                self.state = 'Move and stop at station'
                self.newState = True
            elif isinstance(self.futureEvents[0],ControlPointManeuver) and \
                    self.updateDecelDistance(self.futureEvents[0].controlPoint.speed) >= \
                        self.futureEvents[0].controlPoint.controlTrackLocation - self.trackDistance: 
                # print("CP Location is " + str(self.futureEvents[0].controlPoint.controlTrackLocation))
                # print("decel distance is " + str(self.updateDecelDistance(self.futureEvents[0].controlPoint.speed)))
                # print("track distance is " + str(self.trackDistance))
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
                self.segment_index = control_point.aheadTrackSegment
                self.trackSection = self.currentTrack.components[self.segment_index]
                self.nextTrackSection = self.trackSection
                #deal with trackSection and segment_index too!
                self.state = 'Free move'
                self.newState = True
                self.futureEvents = self.futureEvents[1:]
            else:
                self.state = 'Maneuver at Control Point'

        elif self.state == 'Decelerate to Control Point':
            if self.currentSpeed <= self.goalSpeed and self.futureEvents[0].controlPoint.controlTrackLocation - self.trackDistance <= 0:
                self.state = 'Maneuver at Control Point'
                self.newState = True
            else:
                self.state = 'Decelerate to Control Point' 


        # 'Constrained move' case
        elif self.state == 'Constrained move':
            # print(str(self.id) + '   HFR[0]: ' + self.headFutureRoute[0].name)
            #  'Constrained move' -> 'Decelerate to stop at red'
            if self.signalAspect == 'r':
                self.state = 'Decelerate to stop at red'
                self.newState = True
            #  'Constrained move' -> 'Move and stop at station'
            elif isinstance(self.headFutureRoute[1],Stop) and \
                self.signalAspect == 'g'and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=500 and \
                        self.headFutureRoute[1].id not in self.route.skips: 
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
                # self.currentHeadLocation = self.route.components[0]
                # self.currentTailLocation = self.route.components[0]
                # self.nextHeadLocation = self.route.components[0]
                # self.nextTailLocation = self.route.components[0]
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
            self.move(timestep)

        
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
            self.move(timestep)
        

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
            self.move(timestep)


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
                self.nextAcceleration = self.getNextDeceleration()
                self.newState = False
            else:
                self.nextAcceleration = self.getNextDeceleration()
                # print('my next speed is ' + str (self.nextSpeed))
            # move
            self.move(timestep)

        
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
                self.expectedOperationTime = self.length/self.currentSpeed
                self.newState = False
            else:
                self.expectedOperationTime -= timestep
            # move
            self.move(timestep)

        elif self.state == 'Decelerate to Control Point':
            if self.currentSpeed < self.goalSpeed:
                if self.currentSpeed + self.getNextAcceleration() * timestep <= self.goalSpeed:
                    self.nextAcceleration = self.getNextAcceleration()
            elif self.currentSpeed == self.goalSpeed:
                self.nextAcceleration = 0
            else:
                self.nextAcceleration = self.getNextDeceleration()
            if self.newState == True:
                self.newState = False
            # move
            self.move(timestep)

    def update(self, simulation):
        '''
        update the vehicle location, speed, acceleration (next->current)
        update the block/stopslot occupancy
        update related signal of vehicle
        '''

        if self.nextHeadLocation == None:    # terminal station case (pull in/pull out/turn around)) #NOT here
            self.currentHeadLocation = self.nextHeadLocation
            self.currentTailLocation = self.nextTailLocation
            self.totalDistance = 0 #What is the meaning of this line?
            # self.trackDistance = 0 #MOD HERE
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
        # self.currentHeadLocationDistance = self.nextHeadLocationDistance
        self.currentTailLocation = self.nextTailLocation
        self.currentTailLocationDistance = self.nextTailLocationDistance
        self.trackSection = self.nextTrackSection
        # self.goalSpeed = self.updateMaxSpeed()
        if self.trackSection not in self.currentTrack.components:
            exit()
    
    def updateTrackSection(self):
        #match 
        #for track section by location
        None

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

    def detectSpeedShifts(self):
        i = 1
        distance_to_i = 1
        new_deceleration_distance = np.inf
        need_to_decelerate = False
        final_speed = None
        new_speed = None
        new_distance = None
        priority_deceleration_distance = 0
        while distance_to_i < (self.updateDecelDistance(0) + 1000) and len(self.currentTrack.components) > (self.segment_index + i):
            next_section = self.currentTrack.components[self.segment_index + i]
            distance_to_i = next_section.location - self.trackDistance
            next_section_speed = self.calculateSectionSpeed(next_section)
            if next_section_speed < self.currentSpeed: 
                new_speed = next_section_speed 
                new_deceleration_distance = self.updateDecelDistance(new_speed)
                new_distance = distance_to_i

                if new_deceleration_distance + self.currentSpeed >= new_distance: #if distance needed to decelerate to speed of upcoming slow zone is more than the distance to the zone
                    if new_deceleration_distance > priority_deceleration_distance: #set as 'most urgent' or 'controlling' curve 
                        priority_deceleration_distance = new_deceleration_distance
                        final_speed = new_speed
            i += 1
        if priority_deceleration_distance > 0:
            need_to_decelerate = True
        else:
            need_to_decelerate = False
        return(need_to_decelerate, final_speed)

    def setGoalSpeed(self):
        decelerate_for_curve,decelerate_to_speed = self.detectSpeedShifts() 
        if self.state == 'Decelerate to Control Point' or self.state == 'Maneuver at Control Point':
            return(min(self.futureEvents[0].controlPoint.speed,self.updateMaxSpeed()))
        elif decelerate_for_curve == True:
            self.nextAcceleration = self.getNextDeceleration() #FLAG???
            return(decelerate_to_speed)
        else:
            return(self.updateMaxSpeed())


    def move(self,timestep):
        '''
        calculate the vehicle's speed, location in next timestep with given current speed and acceleration next time step
        '''
        self.goalSpeed = self.setGoalSpeed()
        self.nextSpeed = max(0, self.currentSpeed + self.nextAcceleration * timestep)
        self.movement = self.currentSpeed * timestep + 0.5 * self.nextAcceleration * timestep * timestep
        # update the total distance along the trip
        self.totalDistance += self.movement
        self.trackDistance += self.movement
        # print("current speed is " + str(self.currentSpeed))
        # print("next acceleration is " + str(self.nextAcceleration))
        # print("new movement is " + str(self.movement))
        # print("new trackDistance is " + str(self.trackDistance))
        if math.isnan(self.trackDistance):
            exit()
        if self.trackDistance + self.movement > (self.trackSection.location + self.trackSection.length): #if advanced to next block
            # self.headFutureRoute = self.headFutureRoute[1:]
            self.segment_index += 1
            try:
                self.nextTrackSection = self.currentTrack.components[self.segment_index]
            except:
                self.nextTrackSection = self.trackSection
            self.nextHeadLocationDistance = self.currentHeadLocationDistance + self.movement - self.trackSection.length
        else: #if on the same block
            self.nextHeadLocation = self.currentHeadLocation
            self.nextHeadLocationDistance = self.currentHeadLocationDistance + self.movement
        # update the tail location in the next timestep
        if self.currentTailLocationDistance + self.movement > self.currentTailLocation.length:
            # self.tailFutureRoute = self.tailFutureRoute[1:]
            # self.nextTailLocation = self.tailFutureRoute[0]
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement - self.currentTailLocation.length
        else:
            self.nextTailLocation = self.currentTailLocation
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement