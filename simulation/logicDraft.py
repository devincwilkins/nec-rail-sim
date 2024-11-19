
def determineRelevantEvents(self):
    #function identifies events whose related locations fall within braking distance
        #HOWEVER this does not always mean they will be speed-controlling, i.e. a control point switch with
            ##no speed limit 
    brake_distance = self.updateDecelDistance(0)
    n = 0
    relevant_distance = 0 
    store_track = self.track
    relevant_events_dict = {}
    while relevant_distance <= brake_distance:
        event = self.futureEvents[n]
        if isinstance(event, ControlPointManeuver):
            if n == 0:
                relevant_distance += event.controlPoint.controlTrackLocation - self.trackDistance
            else: 
                relevant_distance += event.controlPoint.controlTrackLocation - store_track.start_location
            store_track = event.controlPoint.aheadTrack
        elif isinstance(event, StationStop):
            if n == 0:
                relevant_distance += event.stop.eastBound - self.trackDistance
            else:
                relevant_distance += event.stop.eastBound - store_track.start_location
        if relevant_distance >= brake_distance:
            return(relevant_events_dict)
        else:
            relevant_events_dict[event] = relevant_distance #or append n?
        n += 1 


###################

def setGoalSpeed(self):
        def detectSpeedShifts(self):
            i = 1
            distance_to_i = 1
            new_deceleration_distance = np.inf
            need_to_decelerate = False
            final_speed = None
            new_speed = None
            new_distance = None
            priority_deceleration_distance = 0
            my_track = self.currentTrack
            my_segment = self.segment_index
            my_distance = self.trackDistance
            last_segment = None
            next_fullstop = None
            for event in self.futureEvents:
                if isinstance(event,ControlPointManeuver):
                    next_track = event.controlpoint.aheadTrack
                    last_segment = event.controlpoint.controlTrackSegment
                    next_track_segment = event.controlpoint.aheadTrackSegment
                    next_track_distance = event.controlpoint.aheadTrackLocation
                    break
                elif isinstance(event,StationStop):
                    next_fullstop = event.station.trackSegment
                else:
                    pass
            while distance_to_i < (self.updateDecelDistance(0) + 1000) and next_fullstop < (self.updateDecelDistance(0) + 1000):
                if self.route.direction_id == 0:
                    if last_segment > (my_segment + i + 1):
                        next_section = my_track.components[my_segment + i]
                        distance_to_i = next_section.start_location - my_distance
                    else:
                        my_track = next_track
                        my_segment = next_track_segment
                        my_distance = next_track_distance #no my distance is someting else....
                        next_section = my_track.components[my_segment]
                        distance_to_i = next_section.start_location - (self.currentTrack.endLocation - my_distance)
                elif self.route.direction_id == 1:
                    exit()
                    print("please write this section for reverse directon :-)")
                next_section_speed = self.calculateSectionSpeed(next_section)
                if next_section_speed < self.currentSpeed: 
                    new_speed = next_section_speed 
                    new_deceleration_distance = self.updateDecelDistance(new_speed)
                    new_distance = distance_to_i
                    if new_deceleration_distance + self.currentSpeed >= new_distance: #if distance needed to decelerate to speed of upcoming slow zone is more than the distance to the zone
                        if new_deceleration_distance > priority_deceleration_distance: #set as 'most urgent' or 'controlling' curve 
                            priority_deceleration_distance = new_deceleration_distance
                            final_speed = new_speed
                i += 1
            if priority_deceleration_distance > 0:
                need_to_decelerate = True
            else:
                need_to_decelerate = False
            return(need_to_decelerate, final_speed)
        
        decelerate_boolean,decelerate_to_speed = detectSpeedShifts() 
        if decelerate_boolean == True:
            self.nextAcceleration = self.getNextDeceleration()
            return(decelerate_to_speed)
        else:
            return(self.updateMaxSpeed())