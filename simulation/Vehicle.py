from Stop import Stop
from Event import *
from Track import Section
from scipy import integrate

#Global Variables
g = 9.8 #gravitational constant in m/s^2



class Vehicle(object):
    def __init__(self,ID,pullout_time,pullin_time,route_sequence,max_speed,max_acc,\
                 max_dec,normal_dec,capacity,length, signal_system, max_cant_deficiency, \
                 track_resistance, initial_acceleration, power, mass, brake_coef):
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

        self.currentTrack = 5 #set to 7 for OB's and 5 for IB's
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
        self.segment_index = 0

    def checkSignals(self):
        #This needs to absorb all the differences in the possible signalling systems!
        #Each signal system should be its own class with its own signalling system, with a function that simply returns "proceed", "slow", "stop"?
        None

    def dwellAtStation(self):
        #Does this work for a time based sim?
        None

    def runningResistance(self):
        #current speed is kept in m/s but track resistance (drag) terms needs v in km/hr
        v = self.currentSpeed
        return (self.trackResistance[0] + self.trackResistance[1]*v \
                + self.trackResistance[2]*(v**2))/self.mass

    def getNextAcceleration(self):
        if self.currentSpeed != 0:
            normalAcceleration = (self.power/self.mass)/self.currentSpeed
            acceleration = min(normalAcceleration,self.initialAcceleration)
        else:
            acceleration = self.initialAcceleration
        running_resistance = self.runningResistance()
        # print("acceleration is " + str(acceleration - running_resistance))
        return acceleration - running_resistance
    
    def getNextDeceleration(self):
        normalDeceleration = -1*((self.power/self.mass)/self.currentSpeed)
        deceleration = max(normalDeceleration,-1*self.initialAcceleration)
        running_resistance = self.runningResistance()
        print("deceleration is " + str(deceleration + running_resistance))
        return deceleration + running_resistance
    
    def updateBrakeDistance(self, vf):
        # print(brake_dist(0,123400,41.67,0,.0059,.000118,.000022)[0])
        # brake_dist(p,m,v0,vf,a,b,c): 
        #braking_distance is integration of deceleration function
        bet = 0.09 #self.brakeCoef #braking coefficient
        lam = 0 #track gradient
        g = 9.8 #gravity placeholder shouldnt be necessary to keep this line
        a = self.trackResistance[0]
        b = self.trackResistance[1]
        c = self.trackResistance[2]
        m = self.mass
        func = lambda x : (x)/((c/m)*(x**2) + (b/m)*(x) + (a/m) + (g*(bet + lam)))
        def integratel(f,a,b,n):
            a1 = float(a)
            b1 = float(b)
            y = 0
            for i in range(0,n):
                y = y + f(a1 + (b1-a1)*i/n)
            return y*(b1-a1)/n
        braking_distance = integratel(func,vf,self.currentSpeed,1000)
        return braking_distance
    
    def updateMaxSpeed(self):
        tg = 4.7 #track gauge
        g = 32.3 #gravitational constant
        r = 5729.58/self.trackSection.curvature #curve radius derived from degree of curvature
        if self.trackSection.curve_direction == 1 or self.trackSection.curve_direction == 0: #speed formula on curves
            curve_speed =  ((((1+((g**2)*(r**2))))/(tg/(5/12))**2)**0.25)/1.467
            track_speed = curve_speed
            print('calculated track speed: ' + str(curve_speed*0.44))
        else: #speed on straight sections
            track_speed = 42
        return min(track_speed, self.maxSpeed)
    
    def transitionState(self,currentTime):
        #  'Prepare to pull in' case
        if self.state == 'Prepare to pull in':
            track = self.route.components[0].track
            stop = self.futureEvents[1].stop
            self.currentTrack = track
            self.trackSection = self.currentTrack.components[self.segment_index]
            self.nextTrackSection = self.trackSection
            # print('my initial trackSection is: ' + str(self.trackSection.id))
            # print('the first trackSection is: ' + str(self.currentTrack.components[0].id))
            # print('the second trackSection is: ' + str(self.currentTrack.components[1].id))
            # exit()
            #  'Prepare to pull in' -> 'Dwell at station'
            if currentTime >= self.pullinTime: #and stop.occupied == False: 
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
                    print("check 3")
                    self.state = 'Ready to pull out'
                    self.newState = True             
                #  'Dwell at station' -> 'Turn around'
                elif self.expectedDwellTime <= 0 and currentTime < self.pulloutTime:
                    print("check 2")
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
                    print("clearing event: " + str(self.futureEvents[0]))
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
            brake_distance = self.updateBrakeDistance(0)
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
                    brake_distance >= self.futureEvents[0].stop.eastBound - self.totalDistance: 
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Free move' -> 'Free move'
            else: 
                self.state = 'Free move'


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
                else:
                    self.nextAcceleration = 0
            if self.currentSpeed >= self.goalSpeed:
                self.nextAcceleration = 0
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
                    print('check 1')
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
                print("deactivate check 2")

    def update(self, simulation):
        '''
        update the vehicle location, speed, acceleration (next->current)
        update the block/stopslot occupancy
        update related signal of vehicle
        '''

        if self.nextHeadLocation == None:    # terminal station case (pull in/pull out/turn around))
            self.currentHeadLocation = self.nextHeadLocation
            self.currentTailLocation = self.nextTailLocation
            self.totalDistance = 0 #What is the meaning of this line?
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
        # print("Future Events? " + str(self.futureEvents))
        # self.currentTrack = self.currentHeadLocation.track #whats goin on here
        self.trackSection = self.nextTrackSection
        # self.goalSpeed = self.updateMaxSpeed()
    
    def updateTrackSection(self):
        #match 
        #for track section by location
        None

    def deactivate(self,simulation):
        simulation.activeVehicles.remove(self)
        print('deactivating vehicle ' + str(self.id))


    def move(self,timestep):
        '''
        calculate the vehicle's speed, location in next timestep with given current speed and acceleration next time step
        '''
        if isinstance(self.currentHeadLocation, Stop): #DT
            self.goalSpeed = self.updateMaxSpeed()
        else:
            self.goalSpeed = self.updateMaxSpeed()
        self.nextSpeed = max(0, self.currentSpeed + self.nextAcceleration * timestep)
        self.movement = self.currentSpeed * timestep + 0.5 * self.nextAcceleration * timestep * timestep
        # update the total distance along the trip
        self.totalDistance += self.movement
        if self.totalDistance + self.movement > (self.trackSection.location + self.trackSection.length): #if advanced to next block
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