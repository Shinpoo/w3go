from case1optimizer import Case1optimizer
from case2optimizer import Case2optimizer


if __name__ == "__main__":
    with open("input_data.json") as json_file:
        data = json.loads(json_file.read())
    Ofun = Case1optimizer(data_dict=data)
    Ofun.solve_model()
    Ofun.show_results()
