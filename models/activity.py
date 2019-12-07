from models.destination import Destination
from models.person import Person
import importlib
from math import sqrt
from itertools import groupby
import numpy as np
from dateutil.parser import isoparse
from datetime import timedelta


class Activity:
    def __init__(self, data):
        self.people = [Person(p_data) for p_data in data["people"]]
        self.destinations = [Destination(d_data) for d_data in data["destinations"]]
        for key in data["activity"]:
            setattr(self, key, data["activity"][key])
        self.start_date = isoparse(self.start_date)
        module = importlib.import_module("optimizers." + data["optimizer"]["name"])
        class_ = getattr(module, data["optimizer"]["name"].capitalize())
        self.optimizer = class_(data["optimizer"])
        
    def compute_distance_dict(self):
        return {(i.name,j.name): self.distance(i.loc, j.loc) for i in self.people + self.destinations for j in self.people + self.destinations}

    def distance(self, A, B):
            # Calculate the distance from A to B
            return sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)

    def compute_interval_score(self):
        while not all([d.flag_interval for d in self.destinations]):
            for d in self.destinations:
                if not d.flag_interval:
                    d.intersection_list = []
                    for hour in range(len(d.availabilities)):
                        product = d.availabilities[hour]
                        for p in self.people:
                            product *= p.increased_availabilities[hour]
                        d.intersection_list.append(product)
                #print(d.intersection_list)

            for d in self.destinations:
                if not d.flag_interval:
                    grouped_list = [(k, sum(1 for i in g)) for k,g in groupby(d.intersection_list)]
                    # print(d.intersection_list)
                    # print(grouped_list)
                    past_elem = []
                    for elem in grouped_list:
                        past_elem.append(elem)
                        if elem[0] == 1 and elem[1] >= self.duration:
                            d.flag_interval = True
                            nb_empty_hours = sum([y for (x,y) in past_elem[:-1]])
                            d.activity_start_date = self.start_date + timedelta(hours=nb_empty_hours + 1)
                            d.activity_end_date = d.activity_start_date + timedelta(hours=self.duration)
                            break

                    if not d.flag_interval:
                        d.interval_score -= 1
                        if d.interval_score == 0:
                            d.flag_interval = True

            for p in self.people:
                p.increase_availabilities()
            # print(self.people[0].increased_availabilities)
            # for d in self.destinations:
            #     print(d.name + " : " + str(d.interval_score))
            #     print(d.activity_start_date)
            #     print(d.activity_end_date)


                
            
    def run(self):
        self.compute_interval_score()
        d_mean = len(self.people) * self.compute_average_distance()
        self.optimizer._create_model(self.people, self.destinations, self.compute_distance_dict(), d_mean)
        self.optimizer.solve_model()
        self.optimizer.show_results(self.people, self.destinations)

    
    def compute_average_distance(self):
        return np.mean([self.distance(i.loc, j.loc) for i in self.people for j in self.destinations])

