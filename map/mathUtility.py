from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r


def convert_inhg_to_mb(inhg):
    """
    Convert pressure from inches of mercury (inHg) to millibars (mb)/hectopascals (hPa).

    Parameters:
    - inhg: The pressure value in inches of mercury.

    Returns:
    - The rounded pressure value in millibars/hPa to the nearest whole number.
    """
    return round(inhg * 33.8639,0) # 1 inHg = 33.8639 mb/hPa, round to nearest whole number, automatically converts to int