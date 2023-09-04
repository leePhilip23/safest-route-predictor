import json

import requests
from requests.auth import HTTPBasicAuth
# import dill
from bs4 import BeautifulSoup
# from datetime import datetime
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XML, fromstring, tostring
from util import *

class DataAPI():
    def __init__(self):
        self.creds = read_api_key()
        self.LS_API_KEY = self.creds["here.api_key"]
        self.GMAP_API_KEY = self.creds["gmap.api_key"]
        self.WEATHER_API_KEY = self.creds["weather.api_key"]

    def getFlow(self,origin, end):

        auth = HTTPBasicAuth('apiKey', self.LS_API_KEY)
        flow_url = f"https://data.traffic.hereapi.com/v7/flow"
        if end == None:
            destination = [33.0811809, -96.841015]
        else:
            destination = end
        if origin == None:
            start = [32.9857, -96.7502]
        else:
            start = origin
        page = requests.get(f'https://data.traffic.hereapi.com/v7/flow?apiKey={self.LS_API_KEY}'
                            f'&in=bbox:{min(start[1],destination[1]) - 0.01},{min(start[0],destination[0])- 0.01},'
                            f'{max(start[1],destination[1]) + 0.01},{max(start[0],destination[0]) + 0.01}&locationReferencing=shape')

        # print(f'https://data.traffic.hereapi.com/v7/flow?apiKey={LS_API_KEY}'
        #                     f'&in=bbox:{min(start[1],destination[1])},{min(start[0],destination[0])},'
        #                     f'{max(start[1],destination[1])},{max(start[0],destination[0])}&locationReferencing=olr')
        return(page.json()["results"])

    def getWeatherAt(self, location):
        # print(self.WEATHER_API_KEY)
        page = requests.get(f"https://api.openweathermap.org/data/2.5/onecall?lat={location[0]}"
                            f"&lon={location[1]}&exclude=minutely,hourly,daily,alerts&appid={self.WEATHER_API_KEY}")
        # print(page.json())
        return page.json()
# file_name = "temp_traffic.json"
# with open(file_name, 'w') as file_object:  #open the file in write mode
#  json.dump(page.json(), file_object)
# d = DataAPI()
# print(d.getWeatherAt([32,96])["current"]["weather"])

