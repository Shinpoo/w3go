class Person:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])


    def increase_availabilties(self):
        pass