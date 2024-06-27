class Route(object):
    def __init__(self,ID,name, components,direction_id, start_block, route_type, first_stop, last_stop):
        self.id = ID
        self.name = name
        self.components = components
        self.direction_id = direction_id
        self.start_block = start_block
        self.type = route_type
        self.first_stop = first_stop
        self.last_stop = last_stop