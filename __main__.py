from optimizer import Optimizer


if __name__ == "__main__":
    Ofun = Optimizer(data_path="input_data.json", case="variable_PPC")
    Ofun.solve_model()
    Ofun.show_results()
