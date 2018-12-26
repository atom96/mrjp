from typing import List

from compiler import BaseBase, UndefinedVariableException, RegisterLocation, MemoryLocation, ABCMeta, abstractmethod, \
    Counter
from type import INT_TYPE, BOOL_TYPE, STRING_TYPE, get_size


def get_default_value(type):
    return {
        INT_TYPE: ExpLitInt(0),
        BOOL_TYPE: ExpLitFalse(),
        STRING_TYPE: ExpLitString('""')
    }[type]


class ExpBase(BaseBase):
    __metaclass__ = ABCMeta

    @abstractmethod
    def mov_to_register(self, location: RegisterLocation) -> str:
        raise NotImplementedError()


class ExpVariable(ExpBase):
    def __init__(self, name):
        self.name = name
        self.location = None

    def set_location(self, location: MemoryLocation):
        self.location = location

    def get_type(self, env):
        try:
            var = env['var'][self.name]
            self.location = var['location']
            return var['type']
        except:
            raise UndefinedVariableException('Variable {} is undefined'.format(self.name))

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return self.location.mov_to_register(location)

    def boolean_jmp(self, if_true, if_false):
        return [
            'cmp {}, 0'.format(self.location),
            'je {}'.format(if_false),
            'jmp {}'.format(if_true)
        ]

class ExpLitInt(ExpBase):
    def __init__(self, value):
        self.value = value

    def get_type(self, env):
        return INT_TYPE

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, {}'.format(location, self.value)]

class ExpLitTrue(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '1', []

    def boolean_jmp(self, if_true, if_false):
        return ['jmp {}'.format(if_true)]

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, 1'.format(location)]


class ExpLitFalse(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '0', []

    def boolean_jmp(self, if_true, if_false):
        return ['jmp {}'.format(if_false)]

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, 0'.format(location)]


class ExpLitString(ExpBase):
    def __init__(self, value):
        self.value = value
        self.ptr = None

    def get_type(self, env):
        if self.value not in env['strings']:
            env['strings'][self.value] = 'L{}'.format(Counter.get())
        self.ptr = env['strings'][self.value]
        return STRING_TYPE

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, {}'.format(location.full_name, self.ptr)]


class ExpApp(ExpBase):
    RESULT_REGISTER = RegisterLocation('eax', 'rax')

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

    def mov_to_register(self, location: RegisterLocation):
        result = [
            'push rcx',
            'mov rcx, rsp',
            'and rsp, 0xFFFFFFFFFFFF0000',
        ]

        if len(self.args) % 2 == 0:
            result.append('add rsp, 8')

        for e in reversed(self.args):
            result += e.mov_to_register(self.RESULT_REGISTER)
            result += ['push {}'.format(self.RESULT_REGISTER.full_name)]

        result += [
            'call {}'.format(self.name),
            'mov rsp, rcx',
            'pop rcx',
        ]

        if location != self.RESULT_REGISTER:
            result = ['push {}'.format(self.RESULT_REGISTER.full_name)] + result + [
                'mov {}, {}'.format(location, self.RESULT_REGISTER),
                'pop {}'.format(self.RESULT_REGISTER.full_name)
            ]

        return result


class ExpOperator(ExpBase):
    def __init__(self, operator):
        self.operator = operator

    def get_type(self, env):
        return self.operator.get_type(env)

    def mov_to_register(self, location: RegisterLocation):
        return self.operator.calc_to_register(location)

    def boolean_jmp(self, if_true, if_false):
        return self.operator.boolean_jmp(if_true, if_false)
