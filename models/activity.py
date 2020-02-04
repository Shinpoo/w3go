from models.destination import Destination
from models.person import Person
import importlib
from math import sqrt
from itertools import groupby
import numpy as np
from dateutil.parser import isoparse
from datetime import timedelta
import matplotlib.pyplot as plt
from datetime import datetime
from shutil import copyfile
import os 

class Activity:
    def __init__(self, data):
        self.people = [Person(p_data) for p_data in data["people"]]
        self.destinations = [Destination(d_data) for d_data in data["destinations"]]
        for key in data["activity"]:
            setattr(self, key, data["activity"][key])
        self.start_date = isoparse(self.start_date)
        module = importlib.import_module("optimizers." + data["optimizer"]["name"])
        class_ = getattr(module, data["optimizer"]["name"].capitalize())
        self.optimizer = class_(data["optimizer"], self.people, self.destinations)
        self.d_mean = len(self.people) * np.mean([self.distance(i.loc, j.loc) for i in self.people for j in self.destinations])
        self.chosen_destination = None
        self.total_distance = None
        self.assessment_score = None
        self.interval_score = None
        self.distance_score = None
        self.score = None
        
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
        print("[INFO]: Calculating interval scores...")
        self.compute_interval_score()
        print("[INFO]: Done.")
        print("[INFO]: Creating mathematical optimization problem...")
        self.optimizer._create_model(self.compute_distance_dict(), self.d_mean)
        print("[INFO]: Done.")
        print("[INFO]: Solving mathematical optimization problem...")
        self.optimizer.solve_model()
        if self.optimizer.is_optimal() or self.optimizer.is_feasible():
            print("[INFO]: Solved to optimality or feasible.")
            self.optimizer.update_objects()
            self.total_distance, self.assessment_score, self.interval_score, self.distance_score, self.score = self.optimizer.get_optimized_results()
            for d in self.destinations:
                if d.chosen_flag:
                    self.chosen_destination = d
            self.print_time_score()
            self.plot_activity()
        else:
            print("[WARNING] Something went wrong!")


    def print_time_score(self):
        print("Building duration = %gs"% self.optimizer.building_duration)
        print("Solving duration = %gs"% self.optimizer.solving_duration)
        print("Total distance = %f" % self.total_distance)
        print("total avg dist = %f" % self.d_mean)
        print("Fun score = %f" % self.assessment_score)
        print("Interval score = %f" % self.interval_score)
        print("Distance score = %f" % self.distance_score)
        print("Final score = %f" % self.score)
        print("Chosen destination: %s"% self.chosen_destination.name)
        print("Start at: %s - End at: %s"%(self.chosen_destination.activity_start_date, self.chosen_destination.activity_end_date))

    def plot_activity(self):
        fig1 = plt.figure(figsize=(12, 6.75), dpi=120)
        plt.axis('equal')
        #plt.grid()
        plt.title("Activity: %s - Where: %s - When: %s"%(self.name, self.chosen_destination.name, self.chosen_destination.activity_start_date))
        for p in self.people: 
            plt.plot(p.loc[0],p.loc[1], 'o', label=p.name)
        for d in self.destinations: 
            plt.plot(d.loc[0],d.loc[1], 'x', label=d.name)

        for p in self.people:
            A_0 = p.loc[0]
            A_1 = p.loc[1]
            B_0 = p.going_to.loc[0]
            B_1 = p.going_to.loc[1]
            plt.arrow(A_0,A_1,B_0-A_0,B_1-A_1, length_includes_head=True, width=0.5, fc='k', ec='k')

        plt.legend()
        results_folder = "results/results__%s" % (datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        os.makedirs(results_folder)

        fig1.savefig(results_folder + '/Itinerary.pdf')
        copyfile("input_data.json", results_folder + "/inputs_out.json")