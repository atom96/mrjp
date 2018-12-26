class Type:
    def __init__(self, type_name):
        self.type_name = type_name

    def __repr__(self):
        return self.type_name

    def __eq__(self, other):
        return self.type_name == other.type_name

    def __hash__(self):
        return hash(self.type_name)

INT_TYPE = Type('int')
BOOL_TYPE = Type('bool')
STRING_TYPE = Type('string')
VOID_TYPE = Type('void')

def get_size(type):
    return {INT_TYPE: 4,
     BOOL_TYPE: 4,
     STRING_TYPE: 8}[type]