class ControlPoint(object):
    def __init__(self, ID, name,control_track,control_track_location,ahead_track,ahead_track_location,ahead_track_segment,direction,speed):
        self.id = ID
        self.name = name
        self.controlTrack = control_track
        self.controlTrackLocation = control_track_location
        self.aheadTrack = ahead_track
        self.aheadTrackLocation = ahead_track_location
        self.aheadTrackSegment = ahead_track_segment
        self.direction = direction
        self.speed = speed
        self.aspect = 'g'

    def updateAspect(self):
        if self.aheadBlock.occupied:
            self.aspect = 'r'
        elif self.twoAheadBlock != None:
            if self.twoAheadBlock.occupied:
                self.aspect = 'y'
            else:
                self.aspect = 'g'
        else:
            self.aspect = 'g'
