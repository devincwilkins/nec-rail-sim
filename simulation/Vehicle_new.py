from Stop import Stop
from Track import Section


class Vehicle(object):
    def __init__(self,ID,pullout_time,pullin_time,route_sequence,max_speed,max_acc,max_dec,normal_dec,capacity,length, signal_system):
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
        self.trackSection = None
        self.signalSystem = signal_system

        self.constrainedSpeed = max_speed * 0.9 #Check FRA Regulation

        self.route = route_sequence[0]   
        self.tripNo = 0

        self.trackNumber = None #get initial value from first event
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


    def transitionState(self,currentTime):
        #  'Prepare to pull in' case
        if self.state == 'Prepare to pull in':
            #  'Prepare to pull in' -> 'Dwell at station'
            if currentTime >= self.pullinTime: # and self.route.components[0].occupied == False (change note)
                self.state = 'Dwell at station'
                self.newState = True
                self.currentHeadLocation = self.route.components[0]
                self.currentTailLocation = self.route.components[0]
                self.nextHeadLocation = self.route.components[0]
                self.nextTailLocation = self.route.components[0]
                self.stopLocationId, self.nextHeadLocationDistance = \
                    self.route.components[0].setVehicleStopSlot(self)
                self.nextTailLocationDistance = self.nextHeadLocationDistance - self.length
                self.headFutureRoute = self.route.components
                self.tailFutureRoute = self.route.components
            #  'Prepare to pull in'-> 'Prepare to pull in'
            else:
                self.state = 'Prepare to pull in'


        #  'Dwell at station' case
        elif self.state == 'Dwell at station':
            #  A vehicle stops ahead, cannot move
            if self.currentHeadLocation.checkVehicleAhead(self.stopSlotId) == True:
                self.state = 'Dwell at station'
            #  Terminal station case
            elif self.currentHeadLocation == self.route.components[-1]: 
                #  'Dwell at station' -> 'Ready to pull out'
                if self.expectedDwellTime <= 0 and currentTime >= self.pulloutTime:
                    self.state = 'Ready to pull out'
                    self.newState = True
                if self.expectedDwellTime <= 0 and self.ifTurnAround == 0:
                    self.state = 'Ready to pull out'
                    self.newState = True             
                #  'Dwell at station' -> 'Turn around'
                if self.expectedDwellTime <= 0 and currentTime < self.pulloutTime:
                    self.state = 'Turn around'
                    self.newState = True
                #  'Dwell at station' -> 'Dwell at station'
                if self.expectedDwellTime > 0:
                    self.state = 'Dwell at station'
            #  Nonterminal station case
            elif self.currentHeadLocation != self.route.components[-1]:
                # print('CHL: ' + str(self.currentHeadLocation.name))
                # print('RC: ' + str(self.route.components[-1].name))
                # 'Dwell at station' -> 'Free move'
                if self.expectedDwellTime <= 0 and self.relatedSignal.aspect == 'g':
                    self.state = 'Free move'
                    self.newState = True
                # 'Dwell at station' -> 'Constrained move'
                if self.expectedDwellTime <= 0 and self.relatedSignal.aspect == 'y':
                    #HERE why is my related signal aspect yellow???
                    self.state = 'Constrained move'
                    self.newState = True
                # 'Dwell at station' -> 'Dwell at station'
                if self.expectedDwellTime > 0 or self.relatedSignal.aspect == 'r':
                    # try:
                    #     print("related signal: " + str(self.relatedSignal.aheadBlock.vehicles)) #block case
                    # except:
                    #     print("related signal: " + str(self.relatedSignal.aheadBlock.occupied)) #stop case
                    # print('check 3')
                    self.state = 'Dwell at station'
        

        #  'Free move' case
        elif self.state == 'Free move':
            #  'Free move' -> 'Decelerate to stop at red'
            if self.relatedSignal.aspect == 'r': #AND distance to that related signal <= self.stopping distance 
                self.state = 'Decelerate to stop at red'
                # print('decelerate to stop at red bc of signal: ' + str(self.relatedSignal.name))
                # print('current head location: ' + str(self.currentHeadLocation.name) + ' ID:' +  str(self.currentHeadLocation.id))
                self.newState = True
            #  'Free move' -> 'Constrained move'
            elif self.relatedSignal.aspect == 'y':
                # print('vehicle ' + str(self.id) + ' on ' + str(self.currentHeadLocation.name) + ' decelerating due to vehicle on ' + str(self.relatedSignal.twoAheadBlock.name))
                self.state = 'Constrained move'
                self.newState = True
            #  'Free move' -> 'Move and stop at station'
            elif isinstance(self.headFutureRoute[1],Stop) and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=200 and \
                        self.relatedSignal.aspect == 'g'and \
                            self.headFutureRoute[1].id not in self.route.skips: 
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Free move' -> 'Free move'
            else: 
                self.state = 'Free move'


        # 'Constrained move' case
        elif self.state == 'Constrained move':
            # print(str(self.id) + '   HFR[0]: ' + self.headFutureRoute[0].name)
            #  'Constrained move' -> 'Decelerate to stop at red'
            if self.relatedSignal.aspect == 'r':
                self.state = 'Decelerate to stop at red'
                self.newState = True
            #  'Constrained move' -> 'Move and stop at station'
            # elif isinstance(self.headFutureRoute[1],Stop) and self.relatedSignal.aspect == 'g':
            elif isinstance(self.headFutureRoute[1],Stop) and \
                self.relatedSignal.aspect == 'g'and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=500 and \
                        self.headFutureRoute[1].id not in self.route.skips: 
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Constained move' -> 'Free move'
            elif self.relatedSignal.aspect == 'g':
                self.state = 'Free move'
                self.newState = True
            #  'Constrained move' -> 'Constrained move'
            else: 
                self.state = 'Constrained move'

        
        #  'Decelerate to stop at red'
        elif self.state == 'Decelerate to stop at red':
            #  'Decelerate to stop at red' -> 'Stop at red'
            if self.expectedStopTime <= 0:
                self.state = 'Stop at red'
                self.newState = True
            #  'Decelerate to stop at red' -> 'Move and stop at station'
            elif isinstance(self.headFutureRoute[1],Stop) and \
                self.relatedSignal.aspect == 'g'and \
                    self.currentHeadLocation.length - self.currentHeadLocationDistance <=200 and \
                        self.headFutureRoute[1].id not in self.route.skips: 
                self.state = 'Move and stop at station'
                self.expectedStopTime = 0
                self.newState = True
            #  'Decelerate to stop at red' -> 'Free move'
            elif self.relatedSignal.aspect == 'g':
                self.state = 'Free move'
                self.expectedStopTime = 0
                self.newState = True
            #  'Decelerate to stop at red' -> 'Constrained move'    
            elif self.relatedSignal.aspect == 'y':
                self.state = 'Constrained move'
                self.expectedStopTime = 0
                self.newState = True
            #  'Decelerate to stop at red' -> 'Decelerate to stop at red'
            else:
                self.state = 'Decelerate to stop at red'


        # 'Stop at red' case
        elif self.state == 'Stop at red':
            #  'Stop at red' -> 'Move and stop at station'
            if isinstance(self.headFutureRoute[1],Stop) and self.relatedSignal.aspect == 'g':
                self.state = 'Move and stop at station'
                self.newState = True
            #  'Stop at red' -> 'Free move'
            elif self.relatedSignal.aspect == 'g':
                self.state = 'Free move'
                self.newState = True
            #  'Stop at red' -> 'Constrained move'    
            elif self.relatedSignal.aspect == 'y':
                self.state = 'Constrained move'
                self.newState = True
            #  'Stop at red' -> 'Stop at red'
            else:
                self.state = 'Stop at red'
        

        # 'Move and stop at station' case
        elif self.state == 'Move and stop at station':
            #  'Move and stop at station' -> 'Dwell at station'
            if self.expectedStopTime <= 0:
                self.state = 'Dwell at station'
                self.newState = True
            #  'Move and stop at station' -> 'Move and stop at station'
            if self.expectedStopTime > 0:
                self.state = 'Move and stop at station'


        # 'Turn around' case
        elif self.state == 'Turn around':
            #  'Turn around' -> 'Dwell at station'
            if self.expectedTurnAroundTime <= 0 and self.route.components[0].occupied == False:
                self.state = 'Dwell at station'
                self.newState = True
                self.currentHeadLocation = self.route.components[0]
                self.currentTailLocation = self.route.components[0]
                self.nextHeadLocation = self.route.components[0]
                self.nextTailLocation = self.route.components[0]
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
                if self.currentSpeed + self.maxAcc * timestep >= self.goalSpeed:
                    self.nextAcceleration = (self.goalSpeed - self.currentSpeed)/timestep
                else:
                    self.nextAcceleration = self.maxAcc
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
                if self.currentSpeed + self.maxAcc * timestep >= self.constrainedSpeed:
                    self.nextAcceleration = (self.constrainedSpeed - self.currentSpeed)/timestep
                else:
                    self.nextAcceleration = self.maxAcc
            if self.currentSpeed > self.constrainedSpeed:
                if self.currentSpeed + self.normalDec * timestep <= self.constrainedSpeed:
                    self.nextAcceleration = (self.constrainedSpeed - self.currentSpeed)/timestep
                else:
                    self.nextAcceleration = self.normalDec
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
                # print('self.expectedStopTime: ' + str(self.expectedStopTime)) #
                # print('self.expectedDecTime: ' + str(self.expectedDecTime))
                # print('self.decTime: ' + str(self.decTime))
                self.nextAcceleration = 0
                self.expectedDecTime -= timestep #time until starting to decelerate
                self.expectedStopTime -= timestep #time until finished decelerating 
                self.newState = False
            else:
                if self.expectedDecTime > 0:
                    self.nextAcceleration = 0
                elif self.expectedDecTime <= 0:
                    if self.currentSpeed + self.normalDec < 0:
                        self.nextAcceleration = -self.currentSpeed
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
                self.stopSlotId, distance = self.headFutureRoute[1].setVehicleStopSlot(self)
                self.expectedStopTime = \
                    ((self.currentHeadLocation.length - self.currentHeadLocationDistance + distance)\
                        /self.stationSpeed)//timestep*timestep
                self.currentSpeed =  (self.currentHeadLocation.length - self.currentHeadLocationDistance + distance)\
                        /self.expectedStopTime
                self.nextAcceleration = 0
                self.expectedStopTime -= timestep
                self.newState = False
            else:
                self.expectedStopTime -= timestep
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
                # self.trackSection.remove()

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
        self.currentHeadLocation = self.nextHeadLocation
        self.currentHeadLocationDistance = self.nextHeadLocationDistance
        self.currentTailLocation = self.nextTailLocation
        self.currentTailLocationDistance = self.nextTailLocationDistance
        self.currentTrack = self.currentHeadLocation.track
                        

    def deactivate(self,simulation):
        simulation.activeVehicles.remove(self)
        print('deactivating vehicle ' + str(self.id))


    def move(self,timestep):
        '''
        calculate the vehicle's speed, location in next timestep with given current speed and acceleration next time step
        '''
        if isinstance(self.currentHeadLocation,Section): #DT
            self.goalSpeed = self.currentHeadLocation.maxSpeed #DT
        elif isinstance(self.currentHeadLocation, Stop): #DT
            self.goalSpeed = 15 #DT
        self.nextSpeed = self.currentSpeed + self.nextAcceleration * timestep
        self.movement = self.currentSpeed * timestep + 0.5 * self.nextAcceleration * timestep * timestep
        # update the total distance along the trip #DT
        self.totalDistance += self.movement
        if self.currentHeadLocationDistance + self.movement > self.currentHeadLocation.length: #if advanced to next block
            self.headFutureRoute = self.headFutureRoute[1:]
            self.nextHeadLocation = self.headFutureRoute[0]
            self.nextHeadLocationDistance = self.currentHeadLocationDistance + self.movement - self.currentHeadLocation.length
        else: #if on the same block
            self.nextHeadLocation = self.currentHeadLocation
            self.nextHeadLocationDistance = self.currentHeadLocationDistance + self.movement
        # update the tail location in the next timestep
        if self.currentTailLocationDistance + self.movement > self.currentTailLocation.length:
            self.tailFutureRoute = self.tailFutureRoute[1:]
            self.nextTailLocation = self.tailFutureRoute[0]
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement - self.currentTailLocation.length
        else:
            self.nextTailLocation = self.currentTailLocation
            self.nextTailLocationDistance = self.currentTailLocationDistance + self.movement