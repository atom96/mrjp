from abc import ABCMeta, abstractmethod
from typing import List

from compiler import BaseBase, RedefinitionException, TypeException, RegisterLocation, \
    Counter, not_so_deep_copy
from type import INT_TYPE, VOID_TYPE, BOOL_TYPE, is_type_matching, get_size
import compiler


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
        env = not_so_deep_copy(env)

        env['was_return'] = env['was_return'] or block_env['was_return']
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
            if var.name in env['var']:
                if env['var'][var.name]['level'] == env['level']:
                    raise RedefinitionException('Variable {} redefined'.format(var.name), self)
            try:
                env = var.check_correctness(env)
            except compiler.CompilerException as e:
                raise compiler.CompilerException(e.rlmsg, self)
        return env

    def compile(self):
        result = []
        for var in self.vars:
            result += var.compile()
        return result


class AsgStmt(StmtBase):
    def __init__(self, expr, value):
        self.expr = expr
        self.value = value
        self.type = None

    def check_correctness(self, env):
        var_type = self.expr.get_type(env)
        val_type = self.value.get_type(env)
        self.type = var_type
        if not self.expr.is_reference() or not is_type_matching(var_type, val_type, env):
            raise TypeException(
                'Right side has type {} but tried to assign value of type {}'.format(var_type, val_type), self)
        return env

    def compile(self) -> List[str]:
        r1 = RegisterLocation('eax', 'rax')
        r2 = RegisterLocation('ebx', 'rbx')
        result = ['push rax', 'push rbx']
        result += self.expr.get_reference(r1)

        if get_size(self.type) == 4:
            register = 'ebx'
        else:
            register = 'rbx'

        result += self.value.mov_to_register(r2) + \
                  ['mov [{}], {}'.format(r1.full_name, register),
                   'pop rbx',
                   'pop rax']
        return result


class PPStmt(StmtBase):
    def __init__(self, expr):
        self.expr = expr
        self.location = None

    def check_correctness(self, env):
        if self.expr.get_type(env) != INT_TYPE:
            raise TypeException('Right side has inproper type. Only int variables can be ++', self)

        return env

    def compile(self):
        r = RegisterLocation('eax', 'rax')

        result = ['push rax']
        result += self.expr.get_reference(r)

        return result + ['inc DWORD [rax]', 'pop rax']


class MMStrmt(StmtBase):
    def __init__(self, expr):
        self.expr = expr
        self.location = None

    def check_correctness(self, env):
        if self.expr.get_type(env) != INT_TYPE:
            raise TypeException('Right side has inproper type. Only int variables can be --', self)

        return env

    def compile(self):
        r = RegisterLocation('eax', 'rax')

        result = ['push rax']
        result += self.expr.get_reference(r)

        return result + ['dec DWORD [rax]', 'pop rax']


class RetVoidStmt(StmtBase):
    def check_correctness(self, env):
        if env['current_fun'][1] != VOID_TYPE:
            raise TypeException(
                'Tried to return without value from non-void function {} {}'.format(*env['current_fun']), self)

        env = not_so_deep_copy(env)
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
        t = self.value.get_type(env)

        if t == VOID_TYPE:
            raise TypeException("Cannot return void value", self)

        if not is_type_matching(env['current_fun'][1], t, env):
            raise TypeException('Tried to return wrong type {} from {} instead of {}'.format(t, *env['current_fun']),
                                self)

        env = not_so_deep_copy(env)
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
            raise TypeException('If condition should be bool', self)

        if self.stmt.__class__.__name__ == 'DeclStmt':
            raise TypeException('Declaration as only statement in "if" is not supported', self)
        env = not_so_deep_copy(env)
        new_env = self.stmt.check_correctness(env)

        try:
            if self.cond.get_real_value():
                env['was_return'] = env['was_return'] or new_env['was_return']
        except AttributeError:
            pass
        env['strings'].update(new_env['strings'].items())
        env['stack_counter'] = new_env['stack_counter']

        return env

    def compile(self):
        l_true = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return self.cond.boolean_jmp(l_true, l_end) + \
               [l_true + ':'] + \
               self.stmt.compile() + \
               [l_end + ':']


class EmptyStmt(StmtBase):
    def compile(self):
        return []

    def check_correctness(self, env):
        return env


class IfElseStmt(StmtBase):
    def __init__(self, cond, stmt1, stmt2):
        self.cond = cond
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('If condition should be bool', self)

        if self.stmt1.__class__.__name__ == 'DeclStmt' or self.stmt2.__class__.__name__ == 'DeclStmt':
            raise TypeException('Declaration as only statement in "if" is not supported', self)

        env = not_so_deep_copy(env)

        env1 = self.stmt1.check_correctness(env)
        env['stack_counter'] = env1['stack_counter']
        env2 = self.stmt2.check_correctness(env)
        env2['stack_counter'] = env2['stack_counter']

        env['strings'].update(env1['strings'])
        env['strings'].update(env2['strings'])

        try:
            if self.cond.get_real_value():
                env['was_return'] = env['was_return'] or env1['was_return']
            else:
                env['was_return'] = env['was_return'] or env2['was_return']
        except AttributeError:
            env['was_return'] = env['was_return'] or (env1['was_return'] and env2['was_return'])

        return env

    def compile(self):
        l_true = 'L{}'.format(Counter.get())
        l_false = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return self.cond.boolean_jmp(l_true, l_false) + \
               [l_true + ':'] + \
               self.stmt1.compile() + \
               ['jmp {}'.format(l_end),
                l_false + ':'] + \
               self.stmt2.compile() + \
               [l_end + ':']


class WhileStmt(StmtBase):
    def __init__(self, cond, stmt):
        self.cond = cond
        self.stmt = stmt

    def check_correctness(self, env):
        if self.cond.get_type(env) != BOOL_TYPE:
            raise TypeException('While condition should be bool', self)
        if self.stmt.__class__.__name__ == 'DeclStmt':
            raise TypeException('Declaration as only statement in "while" is not supported', self)

        env = not_so_deep_copy(env)

        new_env = self.stmt.check_correctness(env)
        try:
            if self.cond.get_real_value():
                env['was_return'] = True
        except AttributeError:
            pass
        env['strings'].update(new_env['strings'])
        env['stack_counter'] = new_env['stack_counter']

        return env

    def compile(self):
        l_start = 'L{}'.format(Counter.get())
        l_cond = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())
        return ['jmp {}'.format(l_cond),
                l_start + ':'] + \
               self.stmt.compile() + \
               [l_cond + ':'] + \
               self.cond.boolean_jmp(l_start, l_end) + \
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


compiler.RETURN_VOID = RetVoidStmt()
