#EVENTS ARE GEOGRAPHICALLY TRIGGERED

class BeginService(object): #New stationstopEventObject for every stop a train makes along its route
    #begin to stop if within braking distance of stop
    def __init__(self, ID, track):
        self.id = ID
        self.track = track # Track number to be stopped at

class StationStop(object): #New stationstopEventObject for every stop a train makes along its route
    #begin to stop if within braking distance of stop
    def __init__(self, ID, stop):
        self.id = ID
        self.stop = stop # Stop Object to be Stopped at
    
class ControlPointManeuver(object): #New EventObject for every CP a train uses along its route
    def __init__(self, ID, stop):
        self.id = ID
        self.stop = stop # Stop Object to be Stopped at