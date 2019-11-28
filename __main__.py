# from case1optimizer import Case1optimizer
# from case2optimizer import Case2optimizer
import json
from models.activity import Activity

if __name__ == "__main__":
    with open("input_data.json") as json_file:
        data = json.loads(json_file.read())
    act = Activity(data)
    act.run()
    # act.compute_interval_score()

