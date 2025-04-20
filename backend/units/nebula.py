class Nebula:
    def __init__(self, title, description, id):
        self.title = title
        self.description = description
        self.id = id
        self.stars = []
        self.constellation = []

    def __str__(self):
        return f"Nebula(id={self.id}, title={self.title}, description={self.description})"
    
    def __repr__(self):
        return self.__str__()
    
    def get_title(self):
        return self.title
    
    def get_description(self):
        return self.description
    
    def get_id(self):
        return self.id
    
    def add_star(self, star_id):
        self.stars.append(star_id)

    def remove_star(self, star_id):
        self.stars.remove(star_id)

    def get_stars(self):
        return self.stars

    def clear(self):
        self.stars = []

    def delete(self):
        pass

    def save(self):
        pass

    def load(self):
        pass
    
    