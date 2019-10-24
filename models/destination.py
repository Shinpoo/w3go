class Destination:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])
        self.interval_score = 10
    def decrease_score(self):
        pass