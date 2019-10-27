from models.destination import Destination
from models.person import Person
import importlib
from math import sqrt


class Activity:
    def __init__(self, data):
        self.people = [Person(p_data) for p_data in data["people"]]
        self.destinations = [Destination(d_data) for d_data in data["destinations"]]
        for key in data["activity"]:
            setattr(self, key, data["activity"][key])
        module = importlib.import_module("optimizers." + data["optimizer"]["name"])
        class_ = getattr(module, data["optimizer"]["name"].capitalize())
        self.optimizer = class_(data["optimizer"])
        
    def compute_distance_dict(self):
        def distance(A, B):
            # Calculate the distance from A to B
            return sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)

        return {(i.name,j.name): distance(i.loc, j.loc) for i in self.people + self.destinations for j in self.people + self.destinations}

    def compute_interval_score(self):
        while not all([d.flag_interval for d in self.destinations]):

            for d in self.destinations:
                if not d.flag_interval:
                    for hour in range(len(d.availabilities)):
                        product = d.availabilities[hour]
                        for p in self.people:
                            product *= p.increased_availabilities[hour]
                        d.intersection_list.append(product)

            for d in self.destinations:
                if not d.flag_interval:
                    if any(d.intersection_list):
                        d.flag_interval = True
                    else:
                        d.interval_score -= 1

            for p in self.people:
                p.increase_availabilities()
            # print(self.people[0].increased_availabilities)
            # for d in self.destinations:
            #     print(d.name + " : " + str(d.interval_score))


                
            

        

    def run(self):
        self.optimizer._create_model(self.people, self.destinations, self.compute_distance_dict())
        self.optimizer.solve_model()
        self.optimizer.show_results(self.people, self.destinations)
