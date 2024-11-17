class Section(object):
    def __init__(self,ID, track_segment, length,start_location, end_location, max_speed,track, curvature, curve_direction, cant):
        self.id = ID
        self.trackSegment = track_segment
        self.length = length
        self.startLocation = start_location
        self.endLocation = end_location
        self.maxSpeed = max_speed
        self.track = track
        self.curvature = curvature
        self.curve_direction = curve_direction
        self.cant = cant
        self.vehicles = []
        self.occupied = False

    def updateOccupancy(self):
        if len(self.vehicles) == 0:
            self.occupied = False
        else:
            self.occupied = True

    def calculateSectionSpeed(self, vehicle):
        tg = 4.7 #track gauge
        g = 32.3 #gravitational constant
        if self.maxSpeed > 0:
            track_speed = self.maxSpeed
        elif self.curve_direction == 1 or self.curve_direction == 0 or self.curve_direction == '1' or self.curve_direction == '0': #speed formula on curves
            r = 5729.58/self.curvature #curve radius derived from degree of curvature
            curve_speed =  ((((1+((g**2)*(r**2))))/(tg/((self.cant + vehicle.maxCantDeficiency)/12))**2)**0.25)/1.467
            track_speed = curve_speed*0.44
        else: #speed on straight sections
            if vehicle.maxSpeed > 50:
                track_speed = 88
            else:
                track_speed = 42 ## TBD: All nan values get 42
        return(min(track_speed,vehicle.maxSpeed))

class Track(object):
    #Composed of track sections in order by start position of section
    def __init__(self,ID,components):
        self.id = ID
        self.components = components