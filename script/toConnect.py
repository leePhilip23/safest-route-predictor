from data import DataAPI
from map import MapAPI
from here_location_services.config.matrix_routing_config import AvoidBoundingBox
from math import dist
import pandas as pd
import pickle

from util import *


class toConnect():
    def __init__(self):
        self.avoidance = []
        self.field_names = ['Weekday_1', 'Weekday_2', 'Weekday_3', 'Weekday_4', 'Weekday_5', 'Weekday_6',
             'Duration', 'Rain', 'Rd', 'St', 'Dr', 'Ave', 'Route',"Pike", 'Fwy', 'Start_Lat', 'Start_Lng',
                            'End_Lat', 'End_Lng', 'Distance(mi)','Humidity(%)']
        self.df = pd.DataFrame(columns=self.field_names)
        self.flow_dict = {}
        self.coors = []
        self.origin = [32.9857, -96.7502]  # toyota NA HQ
        self.dest = [33.0811809, -96.841015]  # UTD
        self.val = None
        self.heatMap = {}
    def set_origin_end(self, begin, end):

        results = MapAPI().address_to_wgs84(begin)
        lat = results['geometry']['location']['lat']
        lng = results['geometry']['location']['lng']
        self.origin = [lat,lng]

        results = MapAPI().address_to_wgs84(end)
        lat = results['geometry']['location']['lat']
        lng = results['geometry']['location']['lng']
        self.dest = [lat, lng]



    def create_csv_from_flow(self):
        # driver ranking: 1 worst, 4 best

        from datetime import datetime
        import calendar
        day = datetime.now().weekday()
        day_name = calendar.day_name[day]
        Tuesday = day_name == "Tuesday"
        Wednesday = day_name == "Wednesday"
        Thursday = day_name == "Thursday"
        Friday = day_name == "Friday"
        Saturday = day_name == "Saturday"
        Sunday = day_name == "Sunday"

        data = DataAPI().getFlow(self.origin, self.dest)
        abs_distance = wsg84_distance(self.origin, self.dest)
        weather = DataAPI().getWeatherAt([data[0]["location"]["shape"]["links"][0]["points"][0]["lat"],
                                          data[0]["location"]["shape"]["links"][0]["points"][0]["lng"]])
        for result in data:
            location = result["location"]
            if "description" in location:
                name = location["description"]
            else:
                name = "Rd"

            Rd = "Rd" in name
            St = "St" in name
            Dr = "Dr" in name or "Ln" in name
            Ave = "Ave" in name or "Blvd" in name
            Route = "Route" in name
            Pike = "PKE" in name or "pke" in name or "Booth" in name
            Fwy = "Wy" in name or "wy" in name or "pky" in name or "Pky" in name or "TOLLWAY" in name or "Way" in name
            flow = result["currentFlow"]
            # print(flow)

            if "speedUncapped" in flow:
                su = flow["speedUncapped"]
                ff = flow["freeFlow"]

                flow_coeff = su / ff
                # print(name,Rd,St,Dr,Ave,Route,Pike,Fwy)
                rain = False
                humidity = 0
                if "Rain" in weather["current"]["weather"]:
                    rain = True
                humidity = float(weather["current"]["humidity"] )
                for i in location["shape"]["links"]:
                    paths = i
                    start = [paths["points"][0]["lat"], paths["points"][0]["lng"]]
                    end = [paths["points"][-1]["lat"], paths["points"][-1]["lng"]]
                    if tuple(start) not in self.flow_dict or tuple(end) not in self.flow_dict:
                        self.flow_dict[tuple(start)] = flow_coeff
                        self.flow_dict[tuple(end)] = flow_coeff
                    distance = paths["length"] * 0.000621371
                    duration = distance / ff * su * 100
                    self.df.loc[len(self.df.index)] = [int(Tuesday), int(Wednesday), int(Thursday), int(Friday),
                                                       int(Saturday), int(Sunday),
                                                       duration, int(rain), int(Rd), int(St), int(Dr), int(Ave),
                                                       int(Route), int(Pike), int(Fwy),
                                                       start[0], start[1], end[0], end[1], distance, humidity]
                    self.coors.append([start, end])
                    self.df = self.df.fillna(0)

                    # print(len(self.df.index))
        if os.path.exists("street_data.csv"):
            os.remove("street_data.csv")
        self.df.to_csv("street_data.csv", index=False)


    def inference_data(self):
        f = pd.read_csv("street_data.csv")
        model = pickle.load(open("PredictModelFile.pkl", "rb"))

        self.val = model.predict(f)
        print(self.val)

    def determine_avoid_bbox(self, driver_ranking=2):

        # some functions = determind the risk
        # score = func()
        from operator import itemgetter
        for index, score in enumerate(self.val):
            start = self.coors[index][0]
            end = self.coors[index][1]
            flow_coeff = (self.flow_dict[tuple(start)] + self.flow_dict[tuple(end)]) / 2
            score *= ((1 / flow_coeff) if flow_coeff <= 1.05 else flow_coeff)
            score *= 0.75
            mid_point = [(start[0]+end[0])/2,(start[1]+end[1])/2]
            self.heatMap[tuple(mid_point)] = score
            score *= 25

            # print(score, driver_ranking)
            # print(distance, abs_distance)
            abs_distance = wsg84_distance(self.origin, self.dest)
            local_distance = wsg84_distance(self.origin, mid_point) + wsg84_distance(self.dest, mid_point)
            if local_distance < abs_distance * 1.2:
                if score >= driver_ranking :
                    temp_bbox = AvoidBoundingBox(max(start[0], end[0]), min(start[0], end[0]), max(start[1], end[1]),
                                                 min(start[1], end[1]))
                    self.avoidance.append( (temp_bbox,score))
                    # print(len(self.avoidance))
        if len(self.avoidance) >= 80:
            self.avoidance = sorted(self.avoidance, key=itemgetter(1), reverse=True)
            temp = []
            spacing = int(len(self.avoidance)/80)
            print(spacing)
            for i in range(0, len(self.avoidance), spacing):
                temp.append(self.avoidance[i][0])
                if len(temp) >= 80:
                    break
            self.avoidance = temp
            # print(start, end, score)
        else:
            temp = []
            for i in range(0, len(self.avoidance)):
                temp.append(self.avoidance[i][0])

            self.avoidance = temp
        print(len(self.avoidance))
        return self.avoidance


    def get_route(self):
        from datetime import datetime
        map,route,zoom = MapAPI().run( start = self.origin, end = self.dest, mode = "car", departure_time = datetime.now(),  avoidance= self.avoidance)
        return map,route,zoom, self.avoidance, self.heatMap

# to = toConnect()
# to.set_origin_end("UTD", "SMU")
# to.create_csv_from_flow()
# to.inference_data()
# to.determine_avoid_bbox(2)
# map,route, box, hmap = to.get_route()
# print(route)
