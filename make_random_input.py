import names
from random import randrange
import random
from random_word import RandomWords
import json

def make_random_json():
    r = RandomWords()

    # Return a single random word
    activities = ["Eat", "Cinema", "Boulet Patins", "Restaurant", "Glace", "Ptit Dej", "Snack", "Work Meeting"]
    map_size = 100
    nb_people = 1 + randrange(12)
    nb_dest = 4 + randrange(10)
    planning_range = 1 + randrange(200)
    people_names = [names.get_full_name() for i in range(nb_people)]
    dest_names = r.get_random_words(limit=nb_dest)
    locs_p = [[random.uniform(-map_size/2, map_size/2), random.uniform(-map_size/2, map_size/2)] for i in range(nb_people)]
    locs_d = [[random.uniform(-map_size/2, map_size/2), random.uniform(-map_size/2, map_size/2)] for i in range(nb_dest)]
    cars = [bool(randrange(2)) for i in range(nb_people)]
    PPC_max = [1 + randrange(4) for i in range(nb_people)]
    availabilities_p = [[randrange(2) for i in range(planning_range)] for j in range(nb_people)]
    availabilities_d = [[randrange(2) for i in range(planning_range)] for j in range(nb_dest)]

    scores = [random.uniform(0,10) for i in range(nb_dest)]
    duration = 1 + randrange(5)
    activity = random.choice(activities)

    people_list = [
        {
            "name": people_names[i],
            "loc": locs_p[i],
            "car": cars[i],
            "PPC_max": PPC_max[i],
            "availabilities": availabilities_p[i]
            } for i in range(nb_people)
            ]

    dest_list = [
        {
            "name": dest_names[i],
            "loc": locs_d[i],
            "score": scores[i],
            "availabilities": availabilities_d[i]
            } for i in range(nb_dest)
            ]


    opt_dict = {
            "name": random.choice(["case1optimizer","case2optimizer"]),
            #"name": "case2optimizer",
            "solver_manager": "neos",
            "solver": "cplex",
            "alpha": 0.50,
            "constant_PPC_max": 2 + randrange(3)
        }

    act_dict = {
            "name": activity,
            "duration": duration,
            "start_date": "2019-01-01T00:00:00"
        }

    data = {
        "people": people_list,
        "destinations": dest_list,
        "optimizer": opt_dict,
        "activity": act_dict
    }
    path = "random_data.json"
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)

        