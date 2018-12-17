from copy import deepcopy

from compiler import BaseBase, RedefinitionException, TypeException, UndefinedVariableException
from type import INT_TYPE, VOID_TYPE, BOOL_TYPE


class StmtBase(BaseBase):
    pass


class BlockStmt(StmtBase):
    def __init__(self, block):
        self.block = block

    def check_correctness(self, env):
        block_env = self.block.check_correctness(env)

        if env['was_return'] != block_env['was_return']:
            env = deepcopy(env)
            env['was_return'] = block_env['was_return']
        return env


class DeclStmt(StmtBase):
    def __init__(self, type, vars):
        self.type = type
        self.vars = vars

    def check_correctness(self, env):
        for var in self.vars:
            print(var)
            if var.name in env['var']:
                if env['var'][var.name]['level'] == env['level']:
                    raise RedefinitionException('Variable {} redefined'.format(var))
            env = var.check_correctness(env)
        return env


class AsgStmt(StmtBase):
    def __init__(self, variable, value):
        self.variable = variable
        self.value = value

    def check_correctness(self, env):
        try:
            var_type = env['var'][self.variable]['type']
        except KeyError:
            print(env)
            raise
        val_type = self.value.get_type(env)
        if var_type != val_type:
            raise TypeException(
                'Variable {} has type {} but tried to assign value of type {}'.format(self.variable, var_type,
                                                                                      val_type))
        return env


class PPStmt(StmtBase):
    def __init__(self, variable):
        self.variable = variable

    def check_correctness(self, env):
        try:
            var_type = env[self.variable]['type']
            if var_type != INT_TYPE:
                raise TypeException('Variable {} has inproper type. Only int variables can be ++'.format(self.variable))

        except KeyError:
            raise UndefinedVariableException('Variable {} is undefined')
        return env


class MMStrmt(StmtBase):
    def __init__(self, variable):
        self.variable = variable

    def check_correctness(self, env):
        try:
            var_type = env[self.variable]['type']
            if var_type != INT_TYPE:
                raise TypeException('Variable {} has inproper type. Only int variables can be --'.format(self.variable))

        except KeyError:
            raise UndefinedVariableException('Variable {} is undefined')
        return env


class RetVoidStmt(StmtBase):
    def check_correctness(self, env):
        if env['current_fun'][1] != VOID_TYPE:
            raise TypeException('Tried to return without value from non-void function {} {}'.format(*env['current_fun']))

        env = deepcopy(env)
        env['was_return'] = True
        return env


class RetValueStmt(StmtBase):
    def __init__(self, value):
        self.value = value

    def check_correctness(self, env):
        print(self.value)
        t = self.value.get_type(env)
        if env['current_fun'][1] != t:
            raise TypeException('Tried to return wrong type {} from {} instead of {}'.format(t, *env['current_fun']))

        env = deepcopy(env)
        env['was_return'] = True
        return env


class IfStmt(StmtBase):
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('If condition should be bool')
        return self.stmt.check_correctness(env)


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


class WhileStmt(StmtBase):
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('While condition should be bool')
        return self.stmt.check_correctness(env)

class ExprStmt(StmtBase):
    def __init__(self, expr):
        self.expr = expr

    def check_correctness(self, env):
        self.expr.get_type(env)
        return env