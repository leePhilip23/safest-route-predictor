import json
import os
from datetime import datetime

from here_location_services import LS
from here_location_services.config.routing_config import ROUTING_RETURN, ROUTING_SPANS
from here_location_services.config.matrix_routing_config import AvoidBoundingBox
from here_map_widget import Map, Marker, GeoJSON
from here_location_services.config.isoline_routing_config import RANGE_TYPE, ISOLINE_ROUTING_TRANSPORT_MODE
from util import *
from pyproj import Transformer


class MapAPI:
    def __init__(self):
        # load credentials
        self.creds = read_api_key()
        self.LS_API_KEY = self.creds["here.api_key"]
        self.GMAP_API_KEY = self.creds["gmap.api_key"]
        self.ls = LS(api_key=self.LS_API_KEY)
        self.route_map = None
        self.origin = [32.9857, -96.7502] #toyota NA HQ
        self.dest = [33.0811809, -96.841015] #UTD
        self.zoom = 14
    def address_to_wgs84(self, address_or_zipcode):
        """
        convert given address code into WGS84 format: longtitude and latitude
        :param address_or_zipcode: string
            address of the location to be converted
        :return geo: JSON object of the address which contains information including WGS
        """
        import requests
        # lat,lng = None, None
        results = None
        api_key = self.GMAP_API_KEY
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        endpoint = f"{base_url}?address={address_or_zipcode}&key={api_key}"
        # see how our endpoint includes our API key? Yes this is yet another reason to restrict the key
        r = requests.get(endpoint)
        if r.status_code not in range(200, 299):
            return None
        try:
            '''
            This try block incase any of our inputs are invalid. This is done instead
            of actually writing out handlers for all kinds of responses.
            '''
            results = r.json()['results'][0]
            # lat = results['geometry']['location']['lat']
            # lng = results['geometry']['location']['lng']
        except:
            pass
        # print(results)
        return results

    # def adjust_map(self):
    #     self.route_map.
    def calculate_zoom(self, start, dest):
        """
        calculate the appropriate zoom to set our map to
        :param start:[float, float] wsg84 coordinate of the start of the route
        :param dest:[float, float] wsg84 coordinate of the end of the route
        :return:
        """
        """
        Formula used to calculate zoom: 
        Convert latitude, longitude to spherical mercator x, y. Get distance between your two points in spherical 
        mercator. The equator is about 40m meters long projected and tiles are 256 pixels wide, so the pixel length 
        of that map at a given zoom level is about 256 * distance/40000000 * 2^zoom.
         """
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        mercator_start = transformer.transform(start[0], start[1])
        mercator_dest = transformer.transform(dest[0], dest[1])
        # print(mercator_dest,mercator_start)
        from math import dist, log2
        distance = dist(mercator_start,mercator_dest)
        # print(distance)
        zoom = log2(1/distance * 40000000)
        return zoom



    def calculate_route(self, mode="car", departure_time=datetime.now(), avoidance=None):
        """
        using HERE Location Service API to calculate a route
        :param start: [float, float] wsg84 coordinate of the start of the route
        :param destination: [float, float] wsg84 coordinate of the end of the route
        :param mode: string - the method of traveling
        :param departure_time: datetime - when the user intend to leave
        :param avoidance: [[flat, flat]] - area(s) to avoid
        :return:
        """

        self.calculate_zoom(self.origin,self.dest)
        # via = waypoint - stupid naming

        if mode == "car":
            result = self.ls.car_route(
                origin=self.origin,
                destination=self.dest,

                via=None,
                alternatives=2,
                departure_time=departure_time,
                spans= [ROUTING_SPANS.streetAttributes, ROUTING_SPANS.carAttributes],
                return_results=[
                    ROUTING_RETURN.polyline,
                    ROUTING_RETURN.elevation,
                    ROUTING_RETURN.instructions,
                    ROUTING_RETURN.actions,
                ],
                avoid_areas=avoidance
            )
            geo_json = result.to_geojson()
            return geo_json
        else:
            return "Not implemented yet"
    def setOrigin(self, start):
        self.origin = start
    def setDest(self, end):
        self.dest = end
    def run(self, start = None, end = None, mode = "car", departure_time = datetime.now(),  avoidance= None):

        if start is not None:
            if isinstance(start, str):
                temp = self.address_to_wgs84(start)
                self.setOrigin(temp)
            else:
                self.setOrigin(start)

        if end is not None:
            if isinstance(end, str):
                temp = self.address_to_wgs84(end)
                self.setOrigin(temp)
            else:
                self.setDest(end)

        route = self.calculate_route(mode=mode, departure_time= departure_time, avoidance= avoidance)

        geo_layer = GeoJSON(data=route, style={"lineWidth": 5})

        self.zoom = self.calculate_zoom(self.origin,self.dest)
        center = midpoint(self.origin, self.dest)
        self.route_map = Map(api_key=self.LS_API_KEY, center=center, zoom=self.zoom)

        origin_marker = Marker(lat=self.origin[0],lng=self.origin[1])
        dest_marker = Marker(lat=self.dest[0],lng=self.dest[1])
        self.route_map.add_layer(geo_layer)
        self.route_map.add_object(origin_marker)
        self.route_map.add_object(dest_marker)
        return center, route, self.zoom
"""
Testing
"""
# maps = MapAPI()

import os

# maps.calculate_zoom(maps.origin,maps.dest)
# print(maps.zoom)
# print(maps.calculate_route())
# results = maps.address_to_wgs84("Toyota North America")
# lat = results['geometry']['location']['lat']
# lng = results['geometry']['location']['lng']
# name = []
# for i in range(0,len(results['address_components'][0])):
#     name.append(results['address_components'][i]['long_name'])
# print(lat,lng,name)
