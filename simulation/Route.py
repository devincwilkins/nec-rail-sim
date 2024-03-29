class Route(object):
    def __init__(self,ID,name, components,direction_id, start_block):
        self.id = ID
        self.name = name
        self.components = components
        self.direction_id = direction_id
        self.start_block = start_block