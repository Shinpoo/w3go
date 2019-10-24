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
        

    def run(self):
        self.optimizer._create_model(self.people, self.destinations, self.compute_distance_dict())
        self.optimizer.solve_model()
        self.optimizer.show_results(self.people, self.destinations)