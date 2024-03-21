
def flight_level_to_feet(flight_level):
    '''Converts a flight level in the format 'FXXX' to feet, where XXX is a number between 0 and 999.'''
    # Check if the flight level starts with 'F' and has a numeric value after
    if flight_level.startswith('F') and flight_level[1:].isdigit():
        # Convert the numeric part of the flight level to an integer, then multiply by 100
        return int(flight_level[1:]) * 100
    else:
        # Return a message or raise an error if the format is incorrect
        return "Invalid flight level format"

def speed_to_knots(speed):
    '''Converts a speed in the format 'NXXX' to knots, where XXX is a number between 0 and 999.'''
    # Check if the speed starts with 'N' and has a numeric value after
    if speed.startswith('N') and speed[1:].isdigit():
        # Convert the numeric part of the speed to an integer
        return int(speed[1:])
    else:
        # Return a message or raise an error if the format is incorrect
        return "Invalid speed format"
    
