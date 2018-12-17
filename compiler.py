from copy import deepcopy

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

    def check_correctness(self):
        """
        void printInt(int)
        void printString(string)
        void error()
        int readInt()
        string readString()
        :return:
        """
        env = {'fun': {
            'printInt' : {'type': type.VOID_TYPE, 'args': Args([(type.INT_TYPE, 's')])},
            'printString': {'type': type.VOID_TYPE, 'args': Args([(type.STRING_TYPE, 's')])},
            'error': {'type': type.VOID_TYPE, 'args': Args([])},
            'readInt': {'type': type.INT_TYPE, 'args': Args([])},
            'readString': {'type': type.STRING_TYPE, 'args': Args([])}

        }, 'var': {}, 'level': 0, 'was_return': False}


        for def_ in self.defs:
            if def_.name in env['fun']:
                raise RedefinitionException('Redefinition of function {}'.format(def_.name))
            env['fun'][def_.name] = {'type': def_.type, 'args': def_.args}

        for def_ in self.defs:
            def_.check_correctness(env)

    def compile(self):
        for def_ in self.defs:
            if def_.name == 'main':
                print(def_.block.compile())


class TopDef(BaseBase):
    def __init__(self, type, name, args, block):
        self.type = type
        self.name = name
        self.args = args
        self.block = block

    def check_correctness(self, env):
        env = deepcopy(env)

        env['current_fun'] = (self.name, self.type)
        for arg in self.args.args:
            env['var'][arg[1]] = {'type': arg[0], 'level': 1 }
        block_env = self.block.check_correctness(env)

        print('\n', self.name, '\n', block_env)

        if not block_env['was_return']:
            raise NoReturnException('Function {} not ended with "return" statemnt'.format(self.name))

        del env['current_fun']


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
        for stmt in self.stmts:

            if stmt.__class__.__name__ ==  'ExprStmt':
                print('\n'.join(stmt.expr.get_value()[1]))


class Args(BaseBase):
    def __init__(self, args):
        self.args = args


    def check_types(self, another):
        print(self.args)
        for type_, other_type in zip(self.args, another):
            if type_[0] != other_type:
                raise TypeException('Argument of wrong type {} instead of {}'.format(other_type, type_[0]))

class VarDef(BaseBase):
    def __init__(self, type, name, value):
        self.type = type
        self.name = name
        self.value = value

    def check_correctness(self, env):
        value_type = self.value.get_type(env)
        print(value_type)
        if self.type != value_type:
            raise TypeException("Cannot assign {} to variable {} of type {}".format(value_type, self.name, self.type))
        env = deepcopy(env)

        env['var'][self.name] = {'level': env['level'], 'type': self.type}
        return env