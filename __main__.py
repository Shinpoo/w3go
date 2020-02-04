# from case1optimizer import Case1optimizer
# from case2optimizer import Case2optimizer
import json
from models.activity import Activity
from make_random_input import make_random_json




if __name__ == "__main__":
    print("[INFO]: Making data...")
    #make_random_json()
    print("[INFO]: Data created.")
    with open("input_data.json") as json_file:
        data = json.loads(json_file.read())
    act = Activity(data)
    act.run()