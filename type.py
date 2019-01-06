class Type:
    def __init__(self, type_name):
        if not isinstance(type_name, str):
            raise AttributeError('Only string should be type name')
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
NULL_TYPE = Type('null')


def get_size(type):
    try:
        return {INT_TYPE: 4,
                BOOL_TYPE: 4,
                STRING_TYPE: 8}[type]
    except KeyError:
        return 8


def is_type_matching(var_type, val_type, env):
    if var_type == val_type:
        return True

    if var_type in [INT_TYPE, STRING_TYPE, BOOL_TYPE] or val_type in [INT_TYPE, STRING_TYPE, BOOL_TYPE]:
        return False

    if val_type == NULL_TYPE:
        return True

    try:
        parent = env['cls'][val_type.type_name].parent
    except KeyError:
        raise Exception("Class {} not defined".format(val_type))
    if parent is None:
        return False
    else:
        # print('Warning, recursion')
        return is_type_matching(var_type, Type(parent), env)


def can_be_casted(type_from, type_to, env):
    if type_from == NULL_TYPE and type_to.type_name in env['cls']:
        return True

    return is_type_matching(type_to, type_from, env)
