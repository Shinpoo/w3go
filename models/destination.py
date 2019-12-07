class Destination:
    def __init__(self, params):
        for key in params:
            setattr(self, key, params[key])
        self.interval_score = 10
        self.activity_start_date = None
        self.activity_end_date = None
        self.intersection_list = []
        self.flag_interval = False
        if not any(self.availabilities):
            self.flag_interval = True
            self.interval_score = 0

        self.chosen_destination = None
