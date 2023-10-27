class Route(object):
    def __init__(self,ID,name, components,direction_id):
        self.id = ID
        self.name = name
        self.components = components
        self.direction_id = direction_id