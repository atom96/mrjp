from copy import deepcopy
from abc import ABCMeta, abstractmethod
from typing import List

import type
# from type import INT_TYPE, STRING_TYPE, VOID_TYPE



class RedefinitionException(Exception):
    pass


class TypeException(Exception):
    pass


class UndefinedVariableException(Exception):
    pass


class NoReturnException(Exception):
    pass


class Counter:
    INSTANCE = None

    def __init__(self):
        self.counter = 0

    @staticmethod
    def get():
        if Counter.INSTANCE is None:
            Counter.INSTANCE = Counter()
        Counter.INSTANCE.counter += 1
        return Counter.INSTANCE.counter


class AssemblyLocation:
    __metaclass__ = ABCMeta

    def __init__(self, location: str):
        self.location = location

    @abstractmethod
    def mov_to_memory(self, dest: 'MemoryLocation') -> List[str]:
        raise NotImplemented

    def mov_to_register(self, dest: 'RegisterLocation') -> List[str]:
        return ['mov {}, {}'.format(dest, self)]

    def __repr__(self):
        return self.location

class MemoryLocation(AssemblyLocation):

    @staticmethod
    def sign(x):
        return ('+', '-')[x < 0]

    def __init__(self, location: str, size: int):
        asm_type = {4: 'DWORD', 8: 'QWORD'}[size]
        super().__init__('{} [rbp{}{}]'.format(asm_type, self.sign(location), abs(location)))
        self.size = size


    def mov_to_register(self, dest: 'RegisterLocation') -> List[str]:
        if self.size == 8:
            register = dest.full_name
        else:
            register = dest
        return ['mov {}, {}'.format(register, self)]


    def mov_to_memory(self, dest: 'MemoryLocation'):
        temp_register = 'rax' if self.size == 8 else 'eax'

        return [
            'push rax',
            'mov {}, {}'.format(temp_register, self),
            'mov {}, {}'.format(dest, temp_register),
            'pop rax'
        ]


class PointerLocation(AssemblyLocation):
    def mov_to_memory(self, dest: 'MemoryLocation') -> List[str]:
        return MemoryLocation.mov_to_memory(self, dest)


class RegisterLocation(AssemblyLocation):
    def __init__(self, location, full_name):
        super().__init__(location)
        self.full_name = full_name

    def mov_to_memory(self, dest: 'MemoryLocation'):
        return ['mov {}, {}'.format(dest, self)]

    def __eq__(self, other):
        # print(other.__dict__)
        return self.location == other.location


class BaseBase:
    def __repr__(self):
        params = ''
        for attr, val in sorted(self.__dict__.items()):
            params += '{}={}, '.format(attr, val if not isinstance(val, str) else {'"{}"'.format(val)})

        params = '(' + params[:-2] + ')' if params else '()'
        return self.__class__.__name__ + params

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__


class Program(BaseBase):
    def __init__(self, defs):
        self.defs = defs
        self.strings = None

    def check_correctness(self):
        """
        void printInt(int)
        void printString(string)
        void error()
        int readInt()
        string readString()
        :return:
        """
        env = {
            'fun': {
                'printInt' : {'type': type.VOID_TYPE, 'args': Args([(type.INT_TYPE, 's')])},
                'printString': {'type': type.VOID_TYPE, 'args': Args([(type.STRING_TYPE, 's')])},
                'error': {'type': type.VOID_TYPE, 'args': Args([])},
                'readInt': {'type': type.INT_TYPE, 'args': Args([])},
                'readString': {'type': type.STRING_TYPE, 'args': Args([])}
            },
            'var': {},
            'level': 0,
            'was_return': False,
            'strings': {}
        }


        for def_ in self.defs:
            if def_.name in env['fun']:
                raise RedefinitionException('Redefinition of function {}'.format(def_.name))
            env['fun'][def_.name] = {'type': def_.type, 'args': def_.args}

        for def_ in self.defs:
            new_env = def_.check_correctness(env)
            env['strings'].update(new_env['strings'].items())

        self.strings = env['strings']

    def compile(self):
        for def_ in self.defs:
            if def_.name == 'main':
                def_.name = 'program'
            print('global', def_.name)
        print('extern printString')
        print('extern strConcat')



        print('section .data')
        print()
        for string, label in self.strings.items():
            print('{} db '.format(label),
                  '\'',
                  string[1:-1],
                  '\', 0',
                  sep='')


        print('section .text')

        for def_ in self.defs:
            print('\n'.join(def_.compile()))




class TopDef(BaseBase):
    def __init__(self, type, name, args, block):
        self.type = type
        self.name = name
        self.args = args
        self.block = block
        self.stack_counter = None

    def check_correctness(self, env):
        env = deepcopy(env)

        env['current_fun'] = (self.name, self.type)
        env['stack_counter'] = 0

        stack_location = 16
        for arg in self.args.args:
            size = type.get_size(arg[0])
            env['var'][arg[1]] = {'type': arg[0], 'level': 1, 'location': MemoryLocation(stack_location, size) }
            stack_location += 8

        block_env = self.block.check_correctness(env)

        if not block_env['was_return']:
            raise NoReturnException('Function {} not ended with "return" statemnt'.format(self.name))

        self.stack_counter = block_env['stack_counter']
        return block_env

    def compile(self):
        return [
                self.name + ':',
                'push rbp',
                'mov rbp, rsp',
                'add rsp, {}'.format(self.stack_counter)
                ] + self.block.compile()


class Block(BaseBase):
    def __init__(self, stmts):
        self.stmts = stmts

    def check_correctness(self, env):
        env = deepcopy(env)
        env['level'] += 1
        for stmt in self.stmts:
            env = stmt.check_correctness(env)
        return env

    def compile(self):
        result = []
        for stmt in self.stmts:
            try:
                result += stmt.compile()
            except NotImplementedError as e:
                print(e.msg)
                pass
        return result


class Args(BaseBase):
    def __init__(self, args):
        self.args = args


    def check_types(self, another):
        # print(self.args)
        for type_, other_type in zip(self.args, another):
            if type_[0] != other_type:
                raise TypeException('Argument of wrong type {} instead of {}'.format(other_type, type_[0]))

class VarDef(BaseBase):
    def __init__(self, type, name, value):
        self.type = type
        self.name = name
        self.value = value
        self.location = None


    def check_correctness(self, env):
        value_type = self.value.get_type(env)
        # print(value_type)
        if self.type != value_type:
            raise TypeException("Cannot assign {} to variable {} of type {}".format(value_type, self.name, self.type))
        env = deepcopy(env)

        env['stack_counter'] -= type.get_size(self.type)
        self.location = MemoryLocation(env['stack_counter'], type.get_size(self.type))
        env['var'][self.name] = {'level': env['level'], 'type': self.type, 'location': self.location}
        return env

    def compile(self):
        r = RegisterLocation('eax', 'rax')

        if self.location.size == 4:
            register = 'eax'
        else:
            register = 'rax'

        return ['push rax'] + \
                self.value.mov_to_register(r) + \
               ['mov {}, {}'.format(self.location, register),
                'pop rax']