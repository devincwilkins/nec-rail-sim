class ControlPoint(object):
    def __init__(self, ID, name,direction):
        self.id = ID
        self.name = name
        self.direction = direction
        self.aspect = 'g'

    def updateAspect(self,currentTime):
        if self.aheadBlock.occupied:
            self.aspect = 'r'
        elif self.twoAheadBlock != None:
            if self.twoAheadBlock.occupied:
                self.aspect = 'y'
            else:
                self.aspect = 'g'
        else:
            self.aspect = 'g'
