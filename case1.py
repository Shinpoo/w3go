from pyomo.opt import SolverFactory
from pyomo.environ import *
infinity = float('inf')

model = ConcreteModel()
# => Pass to AbstractModel() if you want to parametrize the inputs.
Npc = 1 # Nb personnes max/voiture

############
### SETS ###
############

model.D = Set(initialize=['D1'], doc='Destinations')
model.P = Set(initialize=['P1','P2','P3'], doc='People')
model.N = model.D | model.P # union


##################
### PARAMETERS ###
##################

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
# Mettre Np et Npc en param ?

#################
### VARIABLES ###
#################

model.b = Var(model.N, model.N, within=Binary, doc='Arrow activation')
model.a = Var(model.P, within=Binary, doc='Car activation')
model.x = Var(model.D, within=Binary, doc='Destination activation')
model.u = Var(model.P, within=NonNegativeIntegers, doc="Acyclic variables")
model.f = Var(within=Binary, doc="Acyclic variables")
model.z1 = Var(model.P, model.D, within=Binary, doc="[Sum(i in P)] x_j*a_i (for linearization)")
model.z2 = Var(model.P, model.D, within=Binary, doc="[Sum(i in P)] a_i*b_ij (for linearization)")


##########################
### OBJECTIVE FUNCTION ###
##########################

def objective_rule(model):
    return sum(model.d[i,j]*model.b[i,j] for i in model.N for j in model.N)
model.objective = Objective(rule=objective_rule, sense=minimize, doc='Min total distance')


###################
### CONSTRAINTS ###
###################

## C1) La somme des chemins arrivant en 1 point de P est 0 si ce point est un point de départ, sinon elle vaut 1 (2 voitures ne peuvent aller chez une même personne)
## Sum(i in P) b_ij = 1 - a_j  (for all j in P)
def C1(model, j):
    return sum(model.b[i,j] for i in model.P) <= 1 - model.a[j]

model.C1 = Constraint(model.P, rule=C1, doc='incomings arrows to P')

## C2) La somme des chemins arrivant à une destination est égale au nombre de voiture si c'est la destination choisie (i.e celle qui minimise la distance total). Cette somme vaut 0 sinon.
## Sum(i in P) b_ij = x_j*N_cars (for all j in D) <=> Sum(i in P) b_ij = x_j * sum(i in P) a_i  (for all j in D) 
## ==linear==> C2) Sum(i in P) b_ij = sum(i in P) z1_ij  (for all j in D)
##             C2a) z1_ij <= a_i (for all i in P, j in D)
##             C2b) z1_ij <= x_j (for all i in P, j in D)
##             C2c) z1_ij >= a_i + x_j - 1 (for all i in P, j in D)

def C2(model, j):
    return sum(model.b[i,j] for i in model.P) == sum(model.z1[i,j] for i in model.P)

def C2a(model, i, j):
    return model.z1[i,j] <= model.a[i]

def C2b(model, i, j):
    return model.z1[i,j] <= model.x[j]

def C2c(model, i, j):
    return model.z1[i,j] >= model.a[i] + model.x[j] - 1

model.C2 = Constraint(model.D, rule=C2, doc='incoming arrows to D')
model.C2a = Constraint(model.P, model.D, rule=C2a, doc='C2a')
model.C2b = Constraint(model.P, model.D, rule=C2b, doc='C2b')
model.C2c = Constraint(model.P, model.D, rule=C2c, doc='C2c')


## C3) Il ne peut exister qu'une seule destination
## Sum(i in D) x_i = 1

model.C3 = Constraint(expr = sum(model.x[i] for i in model.D) == 1, doc='One destination')


## C4) Le nombre de chemins allant des points de départ à la destination directement est inférieur au nombre de voitures, 
## sauf dans le cas où le nombre de points de départ (càd nombre de voitures) est égale au nombre de personne. Dans ce dernier cas, le nombre
## de chemins est égale au nombre de voitures (toutes les voitures se rendent directement à la destination).
## Sum(i in P) a_i*b_ij <= N_cars - f (for all j in D) <=> Sum(i in P) a_i*b_ij <= [Sum(i in P) a_i] - f (for all j in D)
## ==linear==>  C4) Sum(i in P) z2_ij <= [Sum(i in P) a_i] - f (for all j in D)
##              C4a) z2_ij <= a_i (for all i in P, j in D)
##              C4b) z2_ij <= b_ij (for all i in P, j in D)
##              C4c) z2_ij >= a_i + b_ij - 1 (for all i in P, j in D)
##              C4d) f <= N_p - N_cars <=> f <= N_p - sum(i in P) a_i   [f = 0 si N_p = N_cars // f = 1 si N_p > N_cars]
##              C4e) N_p*f >= N_p - N_cars <=> N_p*f >= N_p - sum(i in P) a_i

def C4(model, j):
    return sum(model.z2[i,j] for i in model.P) <= sum(model.a[i] for i in model.P) - model.f

def C4a(model, i, j):
    return model.z2[i,j] <= model.a[i]

def C4b(model, i, j):
    return model.z2[i,j] <= model.b[i,j]

def C4c(model, i, j):
    return model.z2[i,j] >= model.a[i] + model.b[i,j] - 1

model.C4 = Constraint(model.D, rule=C4, doc='incoming arrows from starts to D')
model.C4a = Constraint(model.P, model.D, rule=C4a, doc='C4a')
model.C4b = Constraint(model.P, model.D, rule=C4b, doc='C4b')
model.C4c = Constraint(model.P, model.D, rule=C4c, doc='C4c')
model.C4d = Constraint(expr = model.f <= len(model.P) - sum(model.a[i] for i in model.P), doc='C4d')
model.C4e = Constraint(expr = len(model.P) * model.f >= len(model.P) - sum(model.a[i] for i in model.P), doc='C4e')


## C5) Il doit y avoir au moins une voiture. Sinon la distance totale trouvée sera toujours 0 en n'activant aucune voiture. 
## N_cars >= 1 <=> sum(i in P) a_i >= 1

model.C5 = Constraint(expr = sum(model.a[i] for i in model.P) >= 1, doc='One car')


## C6) La somme des chemins sortant d'un point P vaut toujours 1 (Que ce soit un point de départ ou non).
## sum(j in N) b_ij = 1 (for all i in P)

def C6(model, i):
    return sum(model.b[i,j] for j in model.N) == 1

model.C6 = Constraint(model.P, rule=C6, doc='outgoing arrows from P')


## C7) Tous les chemins sortant d'une destination valent 0.
## b_ij = 0 (for all i in D, j in N)

def C7(model, i, j):
    return model.b[i,j] == 0

model.C7 = Constraint(model.D, model.N, rule=C7, doc='outgoing arrows from D')


## C8) Empêcher les cycles de 1, 2, ..., N_p points.
##     N_p * (1 - b_ij) + u_j >= u_i + 1 (for all i,j in P) [S' il y a un chemin de i vers j alors u_j > u_i] (contrainte de Miller-Tucker-Zemlin remaniée.)
## C8a)u_i >= 1 (for all i in P)
## C8b)u_i <= N_p (for all i in P)

def C8(model, i, j):
    return len(model.P) * (1 - model.b[i,j]) + model.u[j] >= model.u[i] + 1

def C8a(model, i):
    return model.u[i] >= 1

def C8b(model, i):
    return model.u[i] <= len(model.P)

model.C8 = Constraint(model.P, model.P, rule=C8, doc='Acyclic')
model.C8a = Constraint(model.P, rule=C8a, doc='C8a')
model.C8b = Constraint(model.P, rule=C8b, doc='C8b')

## C9) Maximum Npc personnes par voiture
##     u_i <= N_pc (for all i in P)

def C9(model, i):
    return model.u[i] <= Npc

model.C9 = Constraint(model.P, rule=C9, doc='Max person/car')

#########################
### SOLVING & RESULTS ###
#########################

solver = SolverFactory("cplex")
results = solver.solve(model)
#results.write()
print("\nDisplaying Solution\n" + '-'*60)
# Print the value of the variables at the optimum
# for i in model.P:
#     print("%s = %f" % (model.a[i], value(model.a[i])))
    
# for i in model.N:
#     for j in model.N:
#         print("%s = %f" % (model.b[i,j], value(model.b[i,j])))

# # Print the value of the objective
# print("Objective = %f" % value(model.objective))

def pyomo_postprocess(options=None, instance=None, results=None):
    model.x.display()
    model.b.display()
    model.a.display()
    model.u.display()
    #model.display()

pyomo_postprocess(None, model, results)
print("Objective = %f" % value(model.objective))
print("Status = %s" % results.solver.termination_condition)
