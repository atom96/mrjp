from copy import deepcopy
from abc import ABCMeta, abstractmethod
from typing import List

import type

# from type import INT_TYPE, STRING_TYPE, VOID_TYPE

RETURN_VOID = None


class CompilerException(Exception):
    def __init__(self, msg, obj):
        super().__init__('At line {}, column {}: '.format(obj.line, obj.column) + msg)
        self.rlmsg = msg
        self.obj = obj


class RedefinitionException(CompilerException):
    pass


class TypeException(CompilerException):
    pass


class UndefinedVariableException(CompilerException):
    pass


class NoReturnException(CompilerException):
    pass


class NoAttributeException(CompilerException):
    pass


class CycleException(CompilerException):
    pass


class InvalidCastException(CompilerException):
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

    def __init__(self, location: int, size: int, register='rbp'):
        asm_type = {4: 'DWORD', 8: 'QWORD'}[size]
        super().__init__('{} [{}{}{}]'.format(asm_type, register, self.sign(location), abs(location)))
        self.size = size
        self.abs_location = '{}{}{}'.format(register, self.sign(location), abs(location))

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

    def mov_to_register(self, dest: 'RegisterLocation') -> List[str]:
        return ['mov {}, {}'.format(dest.full_name, self.full_name)]


class BaseBase:
    line = None
    column = None

    def __repr__(self):
        params = ''
        for attr, val in sorted(self.__dict__.items()):
            params += '{}={}, '.format(attr, val if not isinstance(val, str) else {'"{}"'.format(val)})

        params = '(' + params[:-2] + ')' if params else '()'
        return self.__class__.__name__ + params

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__


def not_so_deep_copy(env):
    new_env = {}
    for key, value in env.items():
        if key == 'cls':
            continue
        new_env[key] = deepcopy(value)

    new_env['cls'] = env['cls']
    return new_env


class Program(BaseBase):
    def __init__(self, functions, classes):
        self.functions = functions
        self.classes = classes
        self.strings = None

    def check_for_cycles_in_inheritance(self, env):

        for cls in self.classes:
            curr_cls = cls
            inh = set()

            while (curr_cls.parent is not None):
                if curr_cls.name in inh:
                    raise CycleException("found cycle in inheritance line of class {}".format(curr_cls.name), self)
                inh.add(curr_cls.name)

                try:
                    curr_cls = env['cls'][curr_cls.parent]
                except KeyError:
                    raise UndefinedVariableException('Class {} is not defined'.format((curr_cls.parent)), self)

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
                'printInt': {'type': type.VOID_TYPE, 'args': Args([(type.INT_TYPE, 's')])},
                'printString': {'type': type.VOID_TYPE, 'args': Args([(type.STRING_TYPE, 's')])},
                'error': {'type': type.VOID_TYPE, 'args': Args([])},
                'readInt': {'type': type.INT_TYPE, 'args': Args([])},
                'readString': {'type': type.STRING_TYPE, 'args': Args([])}
            },
            'cls': {},
            'var': {},
            'level': 0,
            'was_return': False,
            'strings': {},
            'in_class': False,
            'this': None
        }

        was_main = False
        for def_ in self.functions:
            if def_.name in env['fun']:
                raise RedefinitionException('Redefinition of function {}'.format(def_.name), def_)
            env['fun'][def_.name] = {'type': def_.type, 'args': def_.args}
            if def_.name == 'main':
                was_main = True
                if len(def_.args.args) != 0:
                    raise TypeException("Main function cannot have any arguments", def_)

        if not was_main:
            raise CompilerException("Main function not found", self)

        for cls in self.classes:
            if cls.name in env['cls']:
                raise RedefinitionException('Redefinition of class {}'.format(cls.name), self)
            env['cls'][cls.name] = cls

        self.check_for_cycles_in_inheritance(env)

        for def_ in self.functions:
            new_env = def_.check_correctness(env)
            env['strings'].update(new_env['strings'].items())

        for cls in self.classes:
            new_env = cls.check_correctness(env)
            env['strings'].update(new_env['strings'].items())

        self.strings = env['strings']

    def compile(self):
        res = []
        res.append('global ' + 'top_main')

        res.append('extern top_printString')
        res.append('extern top_printInt')
        res.append('extern top_strConcat')
        res.append('extern top_error')
        res.append('extern top_readInt')
        res.append('extern top_readString')
        res.append('extern malloc')

        res.append('section .data')
        res.append('')
        for string, label in self.strings.items():
            res.append('{} db '.format(label) +
                       ','.join([hex(ord(c)) for c in string[1:-1].encode('utf-8').decode("unicode_escape")] + ['0']))

        for cls in self.classes:
            res.append('vtable_' + cls.name + ' dq ' + cls.get_virtual_methods())

            res.append('section .text')

        res.append('')
        for def_ in self.functions:
            res += def_.compile()
            res.append('')

        for cls in self.classes:
            res += cls.compile()
            res.append('')

        return '\n'.join(res)


class ClassDef(BaseBase):
    def __init__(self, name, fields, methods, parent=None):
        self.name = name
        self.fields = fields
        self.methods = methods
        self.parent = parent
        self.inheritance_chain = None
        self.size = None
        self.vt_table = None

    def get_method_offset(self, method_name):
        offset = 0
        for obj in self.vt_table:
            for method in sorted(obj['methods']):
                if method == method_name:
                    return offset
                offset += 8

        raise Exception("Method not found????")

    def get_attr_offset(self, attr_name):

        offset = 8
        for obj in self.vt_table:
            for attr in obj['fields']:
                if attr.name == attr_name:
                    return offset
                offset += 8

        raise Exception("Attribute not found???? {} {}".format(attr, self.vt_table))

    def get_method(self, name, env):
        for method in self.methods:
            if method.name == name:
                return method

        if self.parent is None:
            raise NoAttributeException('Class {} does not contain method {}'.format(self.name, name), self)
        else:
            return env['cls'][self.parent].get_method(name, env)

    def get_attribute(self, name, env):
        for attr in self.fields:
            if attr.name == name:
                return attr

        if self.parent is None:
            raise NoAttributeException('Class {} does not contain attribute {}'.format(self.name, name), self)
        else:
            return env['cls'][self.parent].get_attribute(name, env)

    def check_correctness(self, env):

        curr_class = self
        inheritance_chain = []
        while True:
            inheritance_chain.append(curr_class)
            if curr_class.parent is None:
                break
            curr_class = env['cls'][curr_class.parent]

        all_attrs = []
        all_methods = []

        vt_table = []

        self.inheritance_chain = list(reversed(inheritance_chain))

        for curr_class in self.inheritance_chain:
            cur_obj = {}

            for attr in curr_class.fields:
                for known_attr in all_attrs:
                    if attr.name == known_attr.name:
                        raise RedefinitionException(
                            'Redefinition of attribute {} in class {}'.format(attr.name, curr_class.name), self)
                all_attrs.append(attr)

            cur_obj['fields'] = curr_class.fields
            cur_obj['methods'] = {}
            for method in curr_class.methods:
                found = False
                for known_method in all_methods:
                    if method.name == known_method.name:
                        if known_method.type != method.type:
                            raise RedefinitionException(
                                "Wrong type of result in method {} in class {}".format(method.name, curr_class.name),
                                self)
                        if [a[0] for a in known_method.args.args] != [a[0] for a in method.args.args]:
                            raise RedefinitionException(
                                "Wrong types of arguments in method {} in class {}".format(method.name,
                                                                                           curr_class.name), self)

                        for obj in vt_table:
                            if method.name in obj['methods']:
                                obj['methods'][method.name] = curr_class.name
                        found = True
                        break
                if not found:
                    cur_obj['methods'][method.name] = curr_class.name

                all_methods.append(method)
            vt_table.append(cur_obj)

        self.vt_table = vt_table

        env = not_so_deep_copy(env)
        env['in_class'] = self.name

        env['var']['self'] = {'type': type.Type(self.name), 'level': 1, 'location': MemoryLocation(16, 8)}

        for attr in all_attrs:
            location = self.get_attr_offset(attr.name)
            env['var'][attr.name] = {'type': attr.type, 'level': 1,
                                     'location': MemoryLocation(location, type.get_size(attr.type), 'r13')}

        # for method in all_methods:
        #     env['fun'][method.name] = { 'type': method.type, 'args': method.args }

        for method in self.methods:
            new_env = method.check_correctness(env)
            env['strings'].update(new_env['strings'].items())
        self.size = 8 + 8 * len(all_attrs)
        return env

    def get_virtual_methods(self):
        methods = []
        offset = 0
        for obj in self.vt_table:
            for method in sorted(obj['methods']):
                name = 'cls_' + obj['methods'][method] + '_' + method
                methods.append(name)
                offset += 8
        return ','.join(methods + ['0'])

    def compile(self):
        result = []

        for method in self.methods:
            result += method.compile()
        return result


class Field(BaseBase):
    def __init__(self, name, type):
        self.name = name
        self.type = type


class FunDef(BaseBase):
    def __init__(self, type, name, args, block):
        self.type = type
        self.name = name
        self.args = args
        self.block = block
        self.stack_counter = None
        self.is_method = False

    def check_correctness(self, env):
        env = not_so_deep_copy(env)

        env['current_fun'] = (self.name, self.type)
        env['stack_counter'] = 0
        self.is_method = env['in_class']

        stack_location = 16

        if self.is_method:
            stack_location += 8

        for arg in self.args.args:
            if arg[0] == type.VOID_TYPE:
                raise TypeException('Parameter {} cannot be void'.format(arg[1]), self)
            size = type.get_size(arg[0])
            if arg[1] in env['var']:
                raise RedefinitionException('Redefinition of argument {}'.format(arg[1]), self)
            env['var'][arg[1]] = {'type': arg[0], 'level': 1, 'location': MemoryLocation(stack_location, size)}
            stack_location += 8

        block_env = self.block.check_correctness(env)

        if not block_env['was_return']:
            if self.type != type.VOID_TYPE:
                raise NoReturnException('Function {} not ended with "return" statemnt'.format(self.name), self)
            else:
                self.block.stmts.append(RETURN_VOID)

        self.stack_counter = block_env['stack_counter']
        return block_env

    def compile(self):

        if self.is_method:
            name = 'cls_' + self.is_method + '_' + self.name
        else:
            name = 'top_' + self.name

        return [
                   name + ':',
                   'push rbp',
                   'mov rbp, rsp',
                   'add rsp, {}'.format(self.stack_counter)
               ] + self.block.compile()


class Block(BaseBase):
    def __init__(self, stmts):
        self.stmts = stmts

    def check_correctness(self, env):
        env = not_so_deep_copy(env)
        env['level'] += 1
        for stmt in self.stmts:
            env = stmt.check_correctness(env)
        return env

    def compile(self):
        result = []
        for stmt in self.stmts:
            result += stmt.compile()

        return result


class Args(BaseBase):
    def __init__(self, args):
        self.args = args

    def check_types(self, another, env):
        if len(self.args) != len(another):
            raise TypeException('Number of arguments to function is improper', self)

        for type_, other_type in zip(self.args, another):
            if not type.is_type_matching(type_[0], other_type, env):
                raise TypeException('Argument of wrong type {} instead of {}'.format(other_type, type_[0]), self)


class VarDef(BaseBase):
    def __init__(self, type, name, value):
        self.type = type
        self.name = name
        self.value = value
        self.location = None

    def check_correctness(self, env):
        if self.type == type.VOID_TYPE:
            raise TypeException('Variable {} type cannot be void'.format(self.name), self)
        value_type = self.value.get_type(env)

        if not type.is_type_matching(self.type, value_type, env):
            raise TypeException("Cannot assign {} to variable {} of type {}".format(value_type, self.name, self.type),
                                self)
        env = not_so_deep_copy(env)

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
