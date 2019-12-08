from optimizers.optimizer import Optimizer
from pyomo.environ import*


class Case2optimizer(Optimizer):
    def __init__(self, params, people, destinations):
        super().__init__(params, people, destinations)
        self.u_level_range = 20 # TODO Define it according to the number of ppl/dest

    def _create_parameters(self, dist_dict, d_mean):
        super()._create_parameters(dist_dict, d_mean)
        self.u_level = {name:(i+1) * self.u_level_range for (i,name) in enumerate([p.name for p in self.people])}
        self.PPC_max = {p.name:p.PPC_max for p in self.people}
        self.model.PPC_max = Param(self.model.P, initialize=self.PPC_max, doc='Max people in car')
        self.model.u_max = Param(self.model.P, initialize=self.u_level, doc='u level')

    def _create_variables(self):
        super()._create_variables()
        self.model.v = Var(self.model.P, self.model.P, within=Binary, doc="1 if Person i passed to j")
        self.model.delta1 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
        self.model.delta2 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
        self.model.z3 = Var(self.model.P, self.model.P, within=Binary, doc="Aux variable")
        self.model.PPC = Var(self.model.P, within=NonNegativeIntegers, doc="People in car")

    def _create_acyclicgraph_constraints(self):
        super()._create_acyclicgraph_constraints()
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
        super()._create_car_constraints()
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
            return sum(model.z3[i,j] for j in model.P) ==  model.PPC[i]
        def C20(model, i):
            return model.PPC[i] <= model.PPC_max[i]

        self.model.C11 = Constraint(self.model.P, self.model.P, rule=C11, doc='Car count')
        self.model.C12 = Constraint(self.model.P, self.model.P, rule=C12, doc='Car count')
        self.model.C13 = Constraint(self.model.P, self.model.P, rule=C13, doc='Car count')
        self.model.C14 = Constraint(self.model.P, self.model.P, rule=C14, doc='Car count')
        self.model.C15 = Constraint(self.model.P, self.model.P, rule=C15, doc='Car count')
        self.model.C16 = Constraint(self.model.P, self.model.P, rule=C16, doc='Car count')
        self.model.C17 = Constraint(self.model.P, self.model.P, rule=C17, doc='Car count')
        self.model.C18 = Constraint(self.model.P, self.model.P, rule=C18, doc='Car count')
        self.model.C19 = Constraint(self.model.P, rule=C19, doc='Car count')
        self.model.C20 = Constraint(self.model.P, rule=C20, doc='Max PPC constraint')