class Score:
    def __init__(self, name, age, gender, yr_driven, previous_crash, year_of_car):
        # Save parameters
        self.name = name
        self.age = age
        self.gender = gender
        self.yr_driven = yr_driven
        self.previous_crash = previous_crash
        self.year_of_car = year_of_car

        # Points to be calculated
        self.age_points = 0
        self.gender_points = 0
        self.yr_driven_points = 0
        self.previous_crash_points = 0
        self.year_of_car_points = 0
        self.total_score = 0

        # Calculate points
        self.calc_age()
        self.calc_gender()
        self.calc_yr_driven()
        self.calc_previous_crash()
        self.calc_year_of_car()

    def calc_age(self):
        self.age_points = (1 - 4.11 * (self.age-10) ** -0.994) * 25
        # print(f"age_points: {self.age_points}")
        self.total_score += self.age_points

    def calc_gender(self):
        # noting for now
        pass

    def calc_yr_driven(self):
        self.yr_driven_points = (100 -(-0.0000258714655037193 * (self.yr_driven ** 3) + 0.00416691853684393 * (self.yr_driven ** 2) -0.221260904317065  * self.yr_driven + 4.81515176622346)*10)/4
        # print(f"yr_driven: {self.yr_driven_points}")
        self.total_score += self.yr_driven_points



    def calc_previous_crash(self):
        self.previous_crash_points = 25/(self.previous_crash + 1)
        self.total_score += self.previous_crash_points

    def calc_year_of_car(self):
        if self.year_of_car == 0:
            self.year_of_car_points= 25
        else:
            import math
            self.year_of_car_points = 25 - 3 * (1 / (1.4 - math.log10(self.year_of_car)))
            if self.year_of_car_points < 0:
                self.year_of_car_points = 0
        # print(f"year of car points: {self.yr_driven_points}")
        self.total_score += self.year_of_car_points