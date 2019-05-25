from optimizer import Optimizer
from pyomo.environ import*


class Case1optimizer(Optimizer):
    
    def __init__(self, data_path):
        super().__init__(data_path)

    def _create_parameters(self):
        super()._create_parameters()
        self.model.PPC_max = Param(initialize=self.constant_PPC_max, doc='Max people in car')

    def _create_acyclicgraph_constraints(self):
        super()._create_acyclicgraph_constraints()
        def C8(model, i, j):
            return model.n_people * (1 - model.b[i,j]) + model.u[j] >= model.u[i] + 1
        def C8a(model, i):
            return model.u[i] >= 1
        def C8b(model, i):
            return model.u[i] <= model.n_people

        self.model.C8 = Constraint(self.model.P, self.model.P, rule=C8, doc='Acyclic')
        self.model.C8a = Constraint(self.model.P, rule=C8a, doc='C8a')
        self.model.C8b = Constraint(self.model.P, rule=C8b, doc='C8b')
    
    def _create_car_constraints(self):
        super()._create_car_constraints()
        def C9(model, i):
            return model.u[i] <= model.PPC_max

        self.model.C9 = Constraint(self.model.P, rule=C9, doc='Max person/car')

