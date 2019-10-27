class Person:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])
        self.increased_availabilities = self.availabilities.copy()


    def increase_availabilities(self):
        if not any(self.increased_availabilities):
            self.increased_availabilities[int(len(self.increase_availabilties/2))] = 1
        else:
            indices = [i for i, x in enumerate(self.increased_availabilities) if x == 1]
            for i in indices:
                if i == 0:
                    self.increased_availabilities[i + 1] = 1
                elif i == len(self.increased_availabilities) - 1:
                        self.increased_availabilities[i - 1] = 1
                else:
                    self.increased_availabilities[i - 1] = 1
                    self.increased_availabilities[i + 1] = 1