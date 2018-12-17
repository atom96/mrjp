from compiler import BaseBase, UndefinedVariableException
from type import INT_TYPE, BOOL_TYPE, STRING_TYPE


def get_default_value(type):
    return {
        INT_TYPE: ExpLitInt(0),
        BOOL_TYPE: ExpLitFalse(),
        STRING_TYPE: ExpLitString("")
     }[type]


class ExpBase(BaseBase):
    pass


class ExpVariable(ExpBase):
    def __init__(self, name):
        self.name = name

    def get_type(self, env):
        try:
            print(env)
            return env['var'][self.name]['type']
        except:
            raise UndefinedVariableException('Variable {} is undefined'.format(self.name))


    def get_value(self):
        return 'eax', ['mov eax, {}'.format(self.name)]

class ExpLitInt(ExpBase):
    def __init__(self, value):
        self.value = value

    def get_type(self, env):
        return INT_TYPE

    def get_value(self):
        return str(self.value), []


class ExpLitTrue(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '1', []


class ExpLitFalse(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '0', []


class ExpLitString(ExpBase):
    def __init__(self, value):
        self.value = value

    def get_type(self, env):
        return STRING_TYPE


class ExpApp(ExpBase):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def get_type(self, env):
        types = [x.get_type(env) for x in self.args]
        try:
            env['fun'][self.name]['args'].check_types(types)
            return env['fun'][self.name]['type']
        except KeyError:
            raise UndefinedVariableException('Function {} is undefined'.format(self.name))

    def get_value(self):
        return 'rax', ['; push params', 'call {}'.format(self.name)]


class ExpOperator(ExpBase):
    def __init__(self, operator):
        self.operator = operator

    def get_type(self, env):
        return self.operator.get_type(env)

    def get_value(self):
        return self.operator.get_value()
