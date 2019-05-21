from pyomo.opt import SolverFactory
from pyomo.environ import*
import json
from math import sqrt
import matplotlib.pyplot as plt
from datetime import datetime
from shutil import copyfile
import os

print("...")
TOL_IS_ZERO = 1e-4
Big_M = 99999 # Pb avec Big M >= 100 000
model = ConcreteModel()

########################
### PRE-PROCESS DATA ###
########################


with open("input_data.json") as json_file:
    data = json.loads(json_file.read())

Npc = data["People/car"] 
people_list = list(data["People"].keys())
destination_list = list(data["Destinations"].keys())


def distance(A, B):
    # Calculate the distance from A to B
    # This will be changed when using maps
    return sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)

dist_dict = {}
# TODO Trouvez un moyen + simple avec dict comprehension
for i,j in data["People"].items():
    for k,l in data["People"].items():
        dist_dict.update({(i,k): distance(j["loc"], l["loc"])}) 

for i,j in data["People"].items():
    for k,l in data["Destinations"].items():
        dist_dict.update({(i,k): distance(j["loc"], l["loc"])}) 

for i,j in data["Destinations"].items():
    for k,l in data["People"].items():
        dist_dict.update({(i,k): distance(j["loc"], l["loc"])}) 

for i,j in data["Destinations"].items():
    for k,l in data["Destinations"].items():
        dist_dict.update({(i,k): distance(j["loc"], l["loc"])}) 

car_dispo = {i:j["car"] for (i,j) in data["People"].items()}


############
### SETS ###
############

model.D = Set(initialize=destination_list, doc='Destinations')
model.P = Set(initialize=people_list, doc='People')
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

# dtab = {
#     ('P1','P1') : 0,
#     ('P1','P2') : 1,
#     ('P1','P3') : 2,
#     ('P1','D1') : 3,
#     ('P2','P1') : 1,
#     ('P2','P2') : 0,
#     ('P2','P3') : 1,
#     ('P2','D1') : 2,
#     ('P3','P1') : 2,
#     ('P3','P2') : 1,
#     ('P3','P3') : 0,
#     ('P3','D1') : 1,
#     ('D1','P1') : 3,
#     ('D1','P2') : 2,
#     ('D1','P3') : 1,
#     ('D1','D1') : 0
#     }

u_level = {}
level = 0
for i in data["People"].keys():
    level += 100
    u_level.update({i: level})     
model.d = Param(model.N, model.N, initialize=dist_dict, doc='Distances')
model.a_bar = Param(model.P, initialize=car_dispo, doc='Can use a car')
model.u_bar = Param(model.P, initialize=u_level, doc='u level')
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
model.v = Var(model.P, model.P, within=Binary, doc="Person i passed to j")
model.delta1 = Var(model.P, model.P, within=Binary, doc="Aux variable")
model.delta2 = Var(model.P, model.P, within=Binary, doc="Aux variable")
model.z3 = Var(model.P, model.P, within=Binary, doc="Aux variable")
model.PIC = Var(model.P, within=NonNegativeIntegers, doc="People in car")

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
    return Big_M * (1 - model.b[i,j]) + model.u[j] >= model.u[i] + 1

def C8prime(model, i, j):
    return model.u[j] <= model.u[i] + 1 + Big_M * (1 - model.b[i,j])

def C8a(model, i):
    return model.u[i] >= 1

def C8b(model, i):
    return model.u[i] <= Big_M

def C8d(model, i):
    return model.u[i] >= (1 + model.u_bar[i]) * model.a[i]

def C8e(model, i):
    return model.u[i] <= model.a[i] + Big_M*(1 - model.a[i]) + model.u_bar[i]

model.C8 = Constraint(model.P, model.P, rule=C8, doc='Acyclic')
model.C8a = Constraint(model.P, rule=C8a, doc='C8a')
model.C8b = Constraint(model.P, rule=C8b, doc='C8b')

model.C8prime = Constraint(model.P, model.P, rule=C8prime, doc='Acyclic')
model.C8d = Constraint(model.P, rule=C8d, doc='C8d')
model.C8e = Constraint(model.P, rule=C8e, doc='C8e')


## C9) Maximum Npc personnes par voiture
##     u_i <= N_pc (for all i in P)

# def C9(model, i):
#     return model.u[i] <= Npc

# model.C9 = Constraint(model.P, rule=C9, doc='Max person/car')


## C10) Une personne ne peut prendre sa voiture uniquement si cette personne a mis sa voiture a disposition.
##     a_i <= a_bar_i (for all i in P)

def C10(model, i):
    return model.a[i] <= model.a_bar[i]

model.C10 = Constraint(model.P, rule=C10, doc='use car only if has a car')

def C11(model, i, j):
    return -1 >= model.u[j] - model.u[i] - Big_M* (1 - model.delta1[i,j]) # TODO Verify

def C12(model, i, j):
    return -1 <= model.u[j] - model.u[i] + Big_M * model.delta1[i,j] # TODO Verify

def C13(model, i, j):
    return model.u[j] - model.u[i] >= 40 - Big_M * (1 - model.delta2[i,j])

def C14(model, i, j):
    return model.u[j] - model.u[i] <= 40 + Big_M * model.delta2[i,j]

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

model.C11 = Constraint(model.P, model.P, rule=C11, doc='Car count')
model.C12 = Constraint(model.P, model.P, rule=C12, doc='Car count')
model.C13 = Constraint(model.P, model.P, rule=C13, doc='Car count')
model.C14 = Constraint(model.P, model.P, rule=C14, doc='Car count')
model.C15 = Constraint(model.P, model.P, rule=C15, doc='Car count')
model.C16 = Constraint(model.P, model.P, rule=C16, doc='Car count')
model.C17 = Constraint(model.P, model.P, rule=C17, doc='Car count')
model.C18 = Constraint(model.P, model.P, rule=C18, doc='Car count')
model.C19 = Constraint(model.P, rule=C19, doc='Car count')


#########################
### SOLVING & RESULTS ###
#########################

solver=SolverFactory(data["Solver"])
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
    model.v.display()
    model.PIC.display()
    #model.objective.display()
    #model.display()

if results.solver.termination_condition != TerminationCondition.infeasible:
    pyomo_postprocess(None, model, results)
    print("Objective = %f" % value(model.objective))

    #Plot
    fig1 = plt.figure(figsize=(12, 6.75), dpi=120)
    plt.axis('equal')
    plt.grid()

    #Plot points
    for k,i in data["People"].items(): 
        plt.plot(i["loc"][0],i["loc"][1], 'o', label=k)
    for k,i in data["Destinations"].items(): 
        plt.plot(i["loc"][0],i["loc"][1], 'x', label=k)
    
    #Plot arrows

    for i in model.N:
        for j in model.N:
            if 1 - TOL_IS_ZERO <= value(model.b[i,j]) <= 1 + TOL_IS_ZERO :
                A_0 = {**data["People"], **data["Destinations"]}[i]["loc"][0] #Look in people and destinations
                A_1 = {**data["People"], **data["Destinations"]}[i]["loc"][1]
                B_0 = {**data["People"], **data["Destinations"]}[j]["loc"][0] 
                B_1 = {**data["People"], **data["Destinations"]}[j]["loc"][1]
                plt.arrow(A_0,A_1,B_0-A_0,B_1-A_1, length_includes_head=True, head_width=0.05, head_length=0.1, fc='k', ec='k')
    plt.legend()
    results_folder = "results/results__%s" % (datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    os.makedirs(results_folder)

    fig1.savefig(results_folder + '/Itinerary.pdf')
    copyfile("input_data.json", results_folder + "/inputs.json")

print("Status = %s" % results.solver.termination_condition)
