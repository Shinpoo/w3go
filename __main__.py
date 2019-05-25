from case1optimizer import Case1optimizer
from case2optimizer import Case2optimizer


if __name__ == "__main__":
    Ofun = Case1optimizer(data_path="input_data.json")
    Ofun.solve_model()
    Ofun.show_results()
