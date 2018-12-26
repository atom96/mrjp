from abc import ABCMeta, abstractmethod
from copy import deepcopy
from typing import List

from compiler import BaseBase, RedefinitionException, TypeException, UndefinedVariableException, RegisterLocation, \
    Counter
from type import INT_TYPE, VOID_TYPE, BOOL_TYPE


class StmtBase(BaseBase):
    __metaclass__ = ABCMeta

    @abstractmethod
    def compile(self) -> List[str]:
        raise NotImplementedError()


class BlockStmt(StmtBase):
    def __init__(self, block):
        self.block = block

    def check_correctness(self, env):
        block_env = self.block.check_correctness(env)

        if env['was_return'] != block_env['was_return']:
            env = deepcopy(env)
            env['was_return'] = block_env['was_return']
        env['stack_counter'] = block_env['stack_counter']
        env['strings'].update(block_env['strings'].items())
        return env

    def compile(self):
        return self.block.compile()



class DeclStmt(StmtBase):
    def __init__(self, type, vars):
        self.type = type
        self.vars = vars

    def check_correctness(self, env):
        for var in self.vars:
            # print(var)
            if var.name in env['var']:
                if env['var'][var.name]['level'] == env['level']:
                    raise RedefinitionException('Variable {} redefined'.format(var))
            env = var.check_correctness(env)
        return env

    def compile(self):
        result = []
        for var in self.vars:
            result += var.compile()
        return result


class AsgStmt(StmtBase):
    def __init__(self, variable, value):
        self.variable = variable
        self.value = value
        self.location = None

    def check_correctness(self, env):
        try:
            var_type = env['var'][self.variable]['type']
            self.location = env['var'][self.variable]['location']
        except KeyError:
            # print(env)
            raise
        val_type = self.value.get_type(env)
        if var_type != val_type:
            raise TypeException(
                'Variable {} has type {} but tried to assign value of type {}'.format(self.variable, var_type,
                                                                                      val_type))
        return env

    def compile(self) -> List[str]:
        r = RegisterLocation('eax', 'rax')
        if self.location.size == 4:
            register = 'eax'
        else:
            register = 'rax'
        return ['push rax'] +  \
                self.value.mov_to_register(r) + \
               ['mov {}, {}'.format(self.location, register),
                 'pop rax']


class PPStmt(StmtBase):
    def __init__(self, variable):
        self.variable = variable
        self.location = None

    def check_correctness(self, env):
        try:
            var_type = env['var'][self.variable]['type']
            self.location = env['var'][self.variable]['location']

            if var_type != INT_TYPE:
                raise TypeException('Variable {} has inproper type. Only int variables can be ++'.format(self.variable))

        except KeyError:
            print(env)
            raise UndefinedVariableException('Variable {} is undefined')
        return env

    def compile(self):
        return ['inc {}'.format(self.location)]

class MMStrmt(StmtBase):
    def __init__(self, variable):
        self.variable = variable
        self.location = None

    def check_correctness(self, env):
        try:
            var_type = env['var'][self.variable]['type']
            self.location = env['var'][self.variable]['location']

            if var_type != INT_TYPE:
                raise TypeException('Variable {} has inproper type. Only int variables can be --'.format(self.variable))

        except KeyError:
            raise UndefinedVariableException('Variable {} is undefined')
        return env

    def compile(self):
        return ['dec {}'.format(self.location)]


class RetVoidStmt(StmtBase):
    def check_correctness(self, env):
        if env['current_fun'][1] != VOID_TYPE:
            raise TypeException('Tried to return without value from non-void function {} {}'.format(*env['current_fun']))

        env = deepcopy(env)
        env['was_return'] = True
        return env

    def compile(self):
        return ['mov rsp, rbp',
                'pop rbp',
                'ret']


class RetValueStmt(StmtBase):
    RESULT_REGISTER = RegisterLocation('eax', 'rax')
    def __init__(self, value):
        self.value = value

    def check_correctness(self, env):
        # print(self.value)
        t = self.value.get_type(env)
        if env['current_fun'][1] != t:
            raise TypeException('Tried to return wrong type {} from {} instead of {}'.format(t, *env['current_fun']))

        env = deepcopy(env)
        env['was_return'] = True
        return env

    def compile(self):

        return self.value.mov_to_register(self.RESULT_REGISTER) + [
            'mov rsp, rbp',
            'pop rbp',
            'ret'
        ]


class IfStmt(StmtBase):
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('If condition should be bool')
        return self.stmt.check_correctness(env)

    def compile(self):
        l_true = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return self.cond.boolean_jmp(l_true, l_end) + \
               [l_true + ':'] + \
               self.stmt.compile() +\
               [l_end + ':']



class IfElseStmt(StmtBase):
    def __init__(self, cond, stmt1, stmt2):
        self.cond = cond
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('If condition should be bool')
        env1 = self.stmt1.check_correctness(env)
        return self.stmt2.check_correctness(env1)

    def compile(self):
        l_true = 'L{}'.format(Counter.get())
        l_false = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return self.cond.boolean_jmp(l_true, l_false) + \
               [l_true + ':'] + \
               self.stmt1.compile() + \
               [l_false + ':'] + \
               self.stmt2.compile() + \
               [l_end + ':']


class WhileStmt(StmtBase):
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('While condition should be bool')
        return self.stmt.check_correctness(env)


    def compile(self):
        l_start = 'L{}'.format(Counter.get())
        l_cond = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return ['jmp {}'.format(l_cond),
                l_start + ':'] + \
               self.stmt.compile() + \
                [l_cond + ':'] + \
                self.cond.boolean_jmp(l_start, l_end) +\
                [l_end + ':']

class ExprStmt(StmtBase):
    def __init__(self, expr):
        self.expr = expr

    def check_correctness(self, env):
        self.expr.get_type(env)
        return env

    def compile(self):
        r = RegisterLocation('eax', 'rax')
        return ['push rax'] + self.expr.mov_to_register(r) + ['pop rax']