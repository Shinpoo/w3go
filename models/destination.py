class Destination:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])

    def decrease_score(self):
        pass