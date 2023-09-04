import os

def midpoint(p1, p2):
    return [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2]
def read_api_key():
    """
    reads and parse and store the credential information from local sources
    :return:
    credd : dict
        a dictionary storing different keys and api keys
    """
    here_path = os.path.join(os.getcwd(), "..")
    here_path = os.path.join(here_path, "credentials")
    cred_path = os.path.join(here_path, "credentials.properties")
    # print(cred_path)
    cred = {}
    with open(cred_path, "r") as f:
        for temp in f:
            temp = (temp.strip()).split("=")
            # print(temp)
            if len(temp)>=2:
                cred[temp[0].strip()] = temp[1].strip()

    return cred


from math import radians, cos, sin, asin, sqrt


def wsg84_distance(location1, location2):
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = location1[1]
    lon2 = location2[1]
    lat1 = location1[0]
    lat2 = location2[0]
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return (c * r) / 1.6

