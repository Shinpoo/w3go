from pyomo.environ import*
from math import sqrt, ceil
import matplotlib.pyplot as plt
from datetime import datetime
from shutil import copyfile
import os
import time
import json


class Optimizer:
    
    def __init__(self, data_path, case):
        self.data_path = data_path
        self.data = self._load_data(self.data_path)
        self.u_level_range = 20
        self._pre_process_data(self.data)
        self.model = None
        self.case = case
        self.Big_M = 200
        self.TOL_IS_ZERO = 1e-4
        self._create_model()
        

    def _load_data(self, path):
        with open(path) as json_file:
            return json.loads(json_file.read())

    def _pre_process_data(self, data):

        def distance(A, B):
            # Calculate the distance from A to B
            # This will be changed when using maps
            return sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)

        self.solver = data["solver"]
        self.solver_manager = data["solver_manager"]
        self.people_list = list(data["people"].keys())
        self.destination_list = list(data["destinations"].keys())
        self.dist_dict = {(i,k): distance(j["loc"], l["loc"]) for i,j in {**data["people"], **data["destinations"]}.items() for k,l in {**data["people"], **data["destinations"]}.items()}
        self.alpha = data["alpha"]
        self.d_max = data["d_max"] * len(data["people"])
        self.d_min = data["d_min"] * len(data["people"])
        self.car_available = {i:j["car"] for (i,j) in data["people"].items()}
        self.PIC_max = {i:j["PIC_max"] for (i,j) in data["people"].items()}
        self.global_PIC_max = data["global_PIC_max"] 
        self.score = {i:j["score"] for (i,j) in data["destinations"].items()}
        self.u_level = {j:(i+1) * self.u_level_range for (i,j) in enumerate(data["people"].keys())}

    def _create_model(self):
        t0_building = time.time()
        self.model = ConcreteModel()
        self._create_sets()
        self._create_parameters()
        self._create_variables()
        self._create_constraints()
        self._create_objective()
        self.building_duration = time.time() - t0_building

    def _create_sets(self):
        self.model.D = Set(initialize=self.destination_list, doc='Destinations')
        self.model.P = Set(initialize=self.people_list, doc='People')
        self.model.N = self.model.D | self.model.P # union

    def _create_parameters(self):
        self.model.d = Param(self.model.N, self.model.N, initialize=self.dist_dict, doc='Distances')
        self.model.a_max = Param(self.model.P, initialize=self.car_available, doc='Can use a car')
        self.model.score = Param(self.model.D, initialize=self.score, doc='Destination scores')
        self.model.alpha = Param(initialize=self.alpha, doc='Importance of distance score compared to the fun score')
        self.model.d_max = Param(initialize=self.d_max, doc='The distance that gives a 0/10 distance score')
        self.model.d_min = Param(initialize=self.d_min, doc='The distance that gives a 10/10 distance score')
        self.model.n_people = Param(initialize=len(self.model.P), doc='Number of people')
        if self.case == "global_PIC":
            self.model.PIC_max = Param(initialize=self.global_PIC_max, doc='Max people in car')
        elif self.case == "local_PIC":
            self.model.PIC_max = Param(self.model.P, initialize=self.PIC_max, doc='Max people in car')
            self.model.u_max = Param(self.model.P, initialize=self.u_level, doc='u level')

    def _create_variables(self):
        self.model.b = Var(self.model.N, self.model.N, within=Binary, doc='Arrow activation')
        self.model.a = Var(self.model.P, within=Binary, doc='Car activation')
        self.model.x = Var(self.model.D, within=Binary, doc='Destination activation')
        self.model.u = Var(self.model.P, within=NonNegativeIntegers, doc="Acyclic variables")
        self.model.f = Var(within=Binary, doc="Aux variable - 0 if the number of car is the number of people, 1 otherwise")
        self.model.z1 = Var(self.model.P, self.model.D, within=Binary, doc="Aux variable - [Sum(i in P)] x_j*a_i (for linearization)")
        self.model.z2 = Var(self.model.P, self.model.D, within=Binary, doc="Aux variable - [Sum(i in P)] a_i*b_ij (for linearization)")
        self.model.fun_score = Var(doc="fun score", within=NonNegativeReals)
        self.model.d_tot = Var(doc="total distance", within=NonNegativeReals)
        self.model.d_score = Var(doc="distance score", within=NonNegativeReals)
        self.model.total_score = Var(doc="final score", within=NonNegativeReals)

        if self.case == "local_PIC":
            self.model.v = Var(self.model.P, self.model.P, within=Binary, doc="1 if Person i passed to j")
            self.model.delta1 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
            self.model.delta2 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
            self.model.z3 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
            self.model.PIC = Var(self.model.P, within=NonNegativeIntegers, doc="People in car")

    def _create_constraints(self):
        self._create_simplegraph_constraints()
        self._create_acyclicgraph_constraints()
        self._create_car_constraints()
        self._create_score_constraints()

    def _create_simplegraph_constraints(self):
        def C1(model, j):
            return sum(model.b[i,j] for i in model.P) <= 1 - model.a[j]
        def C2(model, j):
            return sum(model.b[i,j] for i in model.P) == sum(model.z1[i,j] for i in model.P)
        def C2a(model, i, j):
            return model.z1[i,j] <= model.a[i]
        def C2b(model, i, j):
            return model.z1[i,j] <= model.x[j]
        def C2c(model, i, j):
            return model.z1[i,j] >= model.a[i] + model.x[j] - 1
        def C4(model, j):
            return sum(model.z2[i,j] for i in model.P) <= sum(model.a[i] for i in model.P) - model.f
        def C4a(model, i, j):
            return model.z2[i,j] <= model.a[i]
        def C4b(model, i, j):
            return model.z2[i,j] <= model.b[i,j]
        def C4c(model, i, j):
            return model.z2[i,j] >= model.a[i] + model.b[i,j] - 1
        def C6(model, i):
            return sum(model.b[i,j] for j in model.N) == 1
        def C7(model, i, j):
            return model.b[i,j] == 0

        self.model.C1 = Constraint(self.model.P, rule=C1, doc='incomings arrows to P')
        self.model.C2 = Constraint(self.model.D, rule=C2, doc='incoming arrows to D')
        self.model.C2a = Constraint(self.model.P, self.model.D, rule=C2a, doc='C2a')
        self.model.C2b = Constraint(self.model.P, self.model.D, rule=C2b, doc='C2b')
        self.model.C2c = Constraint(self.model.P, self.model.D, rule=C2c, doc='C2c')
        self.model.C3 = Constraint(expr = sum(self.model.x[i] for i in self.model.D) == 1, doc='One destination')
        self.model.C4 = Constraint(self.model.D, rule=C4, doc='incoming arrows from starts to D')
        self.model.C4a = Constraint(self.model.P, self.model.D, rule=C4a, doc='C4a')
        self.model.C4b = Constraint(self.model.P, self.model.D, rule=C4b, doc='C4b')
        self.model.C4c = Constraint(self.model.P, self.model.D, rule=C4c, doc='C4c')
        self.model.C4d = Constraint(expr = self.model.f <= self.model.n_people - sum(self.model.a[i] for i in self.model.P), doc='C4d')
        self.model.C4e = Constraint(expr = self.model.n_people * self.model.f >= self.model.n_people  - sum(self.model.a[i] for i in self.model.P), doc='C4e')
        self.model.C6 = Constraint(self.model.P, rule=C6, doc='outgoing arrows from P')
        self.model.C7 = Constraint(self.model.D, self.model.N, rule=C7, doc='outgoing arrows from D')


    def _create_acyclicgraph_constraints(self):
        if self.case == "global_PIC":
            def C8(model, i, j):
                return model.n_people * (1 - model.b[i,j]) + model.u[j] >= model.u[i] + 1
            def C8a(model, i):
                return model.u[i] >= 1
            def C8b(model, i):
                return model.u[i] <= model.n_people

            self.model.C8 = Constraint(self.model.P, self.model.P, rule=C8, doc='Acyclic')
            self.model.C8a = Constraint(self.model.P, rule=C8a, doc='C8a')
            self.model.C8b = Constraint(self.model.P, rule=C8b, doc='C8b')

        elif self.case == "local_PIC":
            def C8(model, i, j):
                return self.Big_M * (1 - model.b[i,j]) + model.u[j] >= model.u[i] + 1
            def C8prime(model, i, j):
                return model.u[j] <= model.u[i] + 1 + self.Big_M * (1 - model.b[i,j])
            def C8d(model, i):
                return model.u[i] >= (1 + model.u_max[i]) * model.a[i]
            def C8e(model, i):
                return model.u[i] <= model.a[i] + self.Big_M*(1 - model.a[i]) + model.u_max[i]

            self.model.C8 = Constraint(self.model.P, self.model.P, rule=C8, doc='Acyclic')
            self.model.C8prime = Constraint(self.model.P, self.model.P, rule=C8prime, doc='Acyclic')
            self.model.C8d = Constraint(self.model.P, rule=C8d, doc='C8d')
            self.model.C8e = Constraint(self.model.P, rule=C8e, doc='C8e')

    def _create_car_constraints(self):

        def C10(model, i):
            return model.a[i] <= model.a_max[i]

        self.model.C10 = Constraint(self.model.P, rule=C10, doc='use car only if has a car')

        if self.case == "global_PIC":
            def C9(model, i):
                return model.u[i] <= model.PIC_max

            self.model.C9 = Constraint(self.model.P, rule=C9, doc='Max person/car')

        elif self.case == "local_PIC":
            def C11(model, i, j):
                return -1 >= model.u[j] - model.u[i] - self.Big_M* (1 - model.delta1[i,j])
            def C12(model, i, j):
                return 0 <= model.u[j] - model.u[i] + self.Big_M * model.delta1[i,j]
            def C13(model, i, j):
                return model.u[j] - model.u[i] >= ceil(self.u_level_range/2) - self.Big_M * (1 - model.delta2[i,j])
            def C14(model, i, j):
                return model.u[j] - model.u[i] <= ceil(self.u_level_range/2) - 1 + self.Big_M * model.delta2[i,j]
            def C15(model, i, j):
                return model.v[i,j] ==  1 - (model.delta1[i,j] + model.delta2[i,j])
            def C16(model, i, j):
                return model.z3[i,j] <=  model.v[i,j]
            def C17(model, i, j):
                return model.z3[i,j] <=  model.a[i]
            def C18(model, i, j):
                return model.z3[i,j] >=  model.v[i,j] + model.a[i] - 1
            def C19(model, i):
                return sum(model.z3[i,j] for j in model.P) ==  model.PIC[i]
            def C20(model, i):
                return model.PIC[i] <= model.PIC_max[i]

            self.model.C11 = Constraint(self.model.P, self.model.P, rule=C11, doc='Car count')
            self.model.C12 = Constraint(self.model.P, self.model.P, rule=C12, doc='Car count')
            self.model.C13 = Constraint(self.model.P, self.model.P, rule=C13, doc='Car count')
            self.model.C14 = Constraint(self.model.P, self.model.P, rule=C14, doc='Car count')
            self.model.C15 = Constraint(self.model.P, self.model.P, rule=C15, doc='Car count')
            self.model.C16 = Constraint(self.model.P, self.model.P, rule=C16, doc='Car count')
            self.model.C17 = Constraint(self.model.P, self.model.P, rule=C17, doc='Car count')
            self.model.C18 = Constraint(self.model.P, self.model.P, rule=C18, doc='Car count')
            self.model.C19 = Constraint(self.model.P, rule=C19, doc='Car count')
            self.model.C20 = Constraint(self.model.P, rule=C20, doc='Max PIC constraint')

    def _create_score_constraints(self):
        self.model.C21 = Constraint(expr = sum(self.model.x[i] * self.model.score[i] for i in self.model.D) == self.model.fun_score, doc='Fun level')
        self.model.C22 = Constraint(expr = self.model.d_tot == sum(self.model.d[i,j]*self.model.b[i,j] for i in self.model.N for j in self.model.N), doc="total distance")
        self.model.C23 = Constraint(expr = self.model.d_score == 10 * (self.model.d_tot - self.model.d_max) / (self.model.d_min - self.model.d_max), doc="distance score")
        self.model.C24 = Constraint(expr = self.model.total_score == self.model.alpha * self.model.d_score + (1 - self.model.alpha) * self.model.fun_score, doc="distance score")

    def _create_objective(self):
        def objective_rule(model):
            return model.total_score
        self.model.objective = Objective(rule=objective_rule, sense=maximize, doc='Maximize the score')

    
    def solve_model(self):
        t0_solve = time.time()
        if self.solver_manager == "local":
            solver=SolverFactory(self.solver)
            self.results = solver.solve(self.model)
        elif self.solver_manager == "neos":
            solver_manager = SolverManagerFactory('neos')
            self.results = solver_manager.solve(self.model, opt=self.solver)
        self.solving_duration = time.time() - t0_solve

    def show_results(self):
        if self.results.solver.termination_condition != TerminationCondition.infeasible:
            self.model.x.display()
            self.model.u.display()
            if self.case == "local_PIC":
                self.model.PIC.display()
            print("Building duration = %gs"% self.building_duration)
            print("Solving duration = %gs"% self.solving_duration)
            print("Total distance = %f" % value(self.model.d_tot))
            print("Fun score = %f" % value(self.model.fun_score))
            print("Distance score = %f" % value(self.model.d_score))
            print("Final score = %f" % value(self.model.objective))
            self._plot_results()
        print("Status = %s" % self.results.solver.termination_condition)


    def _plot_results(self):
        fig1 = plt.figure(figsize=(12, 6.75), dpi=120)
        plt.axis('equal')
        plt.grid()

        for k,i in self.data["people"].items(): 
            plt.plot(i["loc"][0],i["loc"][1], 'o', label=k)
        for k,i in self.data["destinations"].items(): 
            plt.plot(i["loc"][0],i["loc"][1], 'x', label=k)
    
        for i in self.model.N:
            for j in self.model.N:
                if 1 - self.TOL_IS_ZERO <= value(self.model.b[i,j]) <= 1 + self.TOL_IS_ZERO :
                    A_0 = {**self.data["people"], **self.data["destinations"]}[i]["loc"][0]
                    A_1 = {**self.data["people"], **self.data["destinations"]}[i]["loc"][1]
                    B_0 = {**self.data["people"], **self.data["destinations"]}[j]["loc"][0] 
                    B_1 = {**self.data["people"], **self.data["destinations"]}[j]["loc"][1]
                    plt.arrow(A_0,A_1,B_0-A_0,B_1-A_1, length_includes_head=True, head_width=0.1, head_length=0.2, fc='k', ec='k')
        plt.legend()
        results_folder = "results/results__%s" % (datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        os.makedirs(results_folder)

        fig1.savefig(results_folder + '/Itinerary.pdf')
        copyfile(self.data_path, results_folder + "/inputs.json")