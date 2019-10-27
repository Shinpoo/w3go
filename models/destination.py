class Destination:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])
        self.interval_score = 10
        self.intersection_list = []
        self.flag_interval = False
        if not any(self.availabilities):
            self.flag_interval = True
            self.interval_score = 0
