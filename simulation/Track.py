class Section(object):
    def __init__(self,ID,length,location, max_speed,track, curvature, curve_direction, cant):
        self.id = ID
        self.length = length
        self.location = location
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

class Track(object):
    #Composed of track sections in order by start position of section
    def __init__(self,ID,components):
        self.id = ID
        self.components = components