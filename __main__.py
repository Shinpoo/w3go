# from case1optimizer import Case1optimizer
# from case2optimizer import Case2optimizer
import json
from models.activity import Activity
#from make_random_input import make_random_json


import os

if __name__ == "__main__":
    json_input = "input_data.json" # Examples: random_data.json (large) input_data.json (small)
    with open(json_input) as json_file:
        data = json.loads(json_file.read())
    os.environ['NEOS_EMAIL'] = data["optimizer"]["neos_email"]
    act = Activity(data)
    act.run()