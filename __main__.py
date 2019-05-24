from optimizer import Optimizer

Ofun = Optimizer(data_path = "input_data.json", case ="global_PIC")
Ofun.solve_model()
Ofun.show_results()