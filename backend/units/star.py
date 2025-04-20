class Star:
    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description
        self.parents = []
        self.children = []
        #self.constellation = [] MAYBE ?
        #self.nebula = [] MAYBE ?
        self.importance = None

    def __str__(self):
        return f"Star(id={self.id}, title={self.title}, description={self.description})"
    
    def __repr__(self):
        return self.__str__()

    def edit_title(self, title):
        self.title = title

    def edit_description(self, description):
        self.description = description

    def edit_constellation(self, constellation):
        self.constellation = constellation

    def edit_importance(self, importance):
        self.importance = importance

    def add_parent(self, parent_id):
        if self.parents is None:
            self.parents = []
        self.parents.append(parent_id)

    def add_child(self, child_id):
        if self.children is None:
            self.children = []
        self.children.append(child_id)

    def delete_parent(self, parent_id):
        if self.parents is not None:
            self.parents.remove(parent_id)

    def delete_child(self, child_id):
        if self.children is not None:
            self.children.remove(child_id)

    

    

    
    
    