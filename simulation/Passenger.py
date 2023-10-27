class Passenger(object):
    def __init__(self,ID,arrival_time,path):
        self.id = ID
        self.originArrivalTime = arrival_time   # time arriving in the origin stop
        self.arrivalTime = arrival_time         # time arriving in the current stop (origin/transfer)
        self.alightingTime = 0
        self.path = path                        # path 
        self.origin = path[0]
        self.futurePath = path[1:]              # stops in the path never arrived
        self.currentLocation = path[0]
        self.nextDestination = self.futurePath[0]
        self.boardingTime = 0
        self.waitingTime = 0
        self.destinationArrivalTime = 0
        self.denied = 0                         # how many times he's denied boarding
        self.active = 1                         # set to 0 when finish the journey

    def board(self,currentTime):
        self.currentLocation = 'in vehicle'
        self.boardingTime = currentTime
        self.waitingTime += (currentTime - self.arrivalTime)

    def deniedBoard(self):
        self.denied += 1

    def alightAndTransfer(self,currentTime):
        self.currentLocation = self.nextDestination
        self.alighingTime = currentTime
        if len(self.futurePath) == 1:                                           # arrive in the final destination
            self.destinationArrivalTime = currentTime
            self.nextDestination = None
            self.active = 0
        else:                                                                   # transfer
            self.futurePath = self.futurePath[1:]
            self.nextDestination = self.futurePath[0]
            if self.nextDestination.id == self.currentLocation.oppositeStopID:  # walk to opposite station
                self.currentLocation = self.nextDestination
                self.futurePath = self.futurePath[1:]
                self.nextDestination = self.futurePath[0]
                self.arrivalTime = currentTime + 30                             # hard code now !!!!
                self.currentLocation.passengers.append(self)                    # add to the transfer station
            else:                                                               # transfer in the same station (park st case)
                self.arrivalTime = currentTime + 10                             # hard code now !!!!
                self.currentLocation.passengers.append(self)