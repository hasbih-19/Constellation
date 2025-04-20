class Constellation:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.stars = []

    def __str__(self):
        return f"Constellation(id={self.id}, name={self.name}, stars={self.stars})"
    
    def add_star(self, star):
        self.stars.append(star)

    def get_stars(self):
        return self.stars
    
<<<<<<< HEAD
    def remove_star(self, star_id):
        self.stars.remove(star_id)
    
=======
>>>>>>> 36de006 (Added star, constellation and nebula units)
    