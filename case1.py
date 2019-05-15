from pyomo.opt import SolverFactory
from pyomo.environ import *
infinity = float('inf')

model = ConcreteModel()

# # Foods
model.D = Set(initialize=['D1'], doc='Destinations')
# Nutrients
model.P = Set(initialize=['P1','P2','P3'], doc='People')
model.N = model.D | model.P # union

#  Table d(i,j)  distance in thousands of miles
#                        P1            P2           P3           D1
#      P1                 0             1            2            3
#      P2                 1             0            1            2
#      P3                 2             1            0            1
#      D1                 3             2            1            0               
dtab = {
    ('P1','P1') : 0,
    ('P1','P2') : 1,
    ('P1','P3') : 2,
    ('P1','D1') : 3,
    ('P2','P1') : 1,
    ('P2','P2') : 0,
    ('P2','P3') : 1,
    ('P2','D1') : 2,
    ('P3','P1') : 2,
    ('P3','P2') : 1,
    ('P3','P3') : 0,
    ('P3','D1') : 1,
    ('D1','P1') : 3,
    ('D1','P2') : 2,
    ('D1','P3') : 1,
    ('D1','D1') : 0
    }
model.d = Param(model.N, model.N, initialize=dtab, doc='Distances')

model.b = Var(model.N, model.N, within=Binary, doc='Arrow activation')
model.a = Var(model.P, within=Binary, doc='Car activation')


# ## Define constraints ##
# ## Sum(i in P) b_ij = 1 - a_j  (j in P)
def incomings_to_P(model, j):
    return sum(model.b[i,j] for i in model.P) <= 1 - model.a[j]

model.C1 = Constraint(model.P, rule=incomings_to_P, doc='incomings arrows to P')

def objective_rule(model):
    return sum(model.d[i,j]*model.b[i,j] for i in model.N for j in model.N)
model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')

# # This is an optional code path that allows the script to be run outside of
# # pyomo command-line.  For example:  python transport.py

# # This emulates what the pyomo command-line tools does

solver = SolverFactory("cplex")
print(...)
results = solver.solve(model)
print("Status = %s" % results.solver.termination_condition)

print(...)
#sends results to stdout
#results.write()
# print(...)
print("\nDisplaying Solution\n" + '-'*60)
#pyomo_postprocess(None, model, results)
# Print the value of the variables at the optimum
for i in model.P:
    print("%s = %f" % (model.a[i], value(model.a[i])))
    
for i in model.P:
    for j in model.P:
        print("%s = %f" % (model.b[i,j], value(model.b[i,j])))

# Print the value of the objective
print("Objective = %f" % value(model.objective))