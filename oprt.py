from compiler import BaseBase, TypeException
from type import INT_TYPE, BOOL_TYPE, STRING_TYPE


class OperatorBase(BaseBase):
    pass


class TwoParamsOperatorBase(OperatorBase):
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def get_type(self, env):
        t1 = self.param1.get_type(env)

        if t1 not in self.ALLOWED_TYPES:
            raise TypeException(
                '{} is not allowed type. Operator {} only accepts {}'.format(t1, self.NAME, self.ALLOWED_TYPES))
        t2 = self.param2.get_type(env)

        if t1 != t2:
            raise TypeException('{} and {} types mismatch'.format(t1, t2))
        return self.RESULT_TYPE

    def get_value(self):
        l_value, l_code = self.param1.get_value()
        r_value, r_code = self.param2.get_value()

        print(l_code, l_value)
        code = l_code + ['push eax'] + r_code
        code += [
            'pop eax',
            '{} eax, {}'.format(self.MNEMONIC, r_value)
        ]
        return 'eax', code


class OneParamOperatorBase(OperatorBase):
    def __init__(self, param):
        self.param = param

    def get_type(self, env):
        t = self.param.get_type(env)
        if t not in self.ALLOWED_TYPES:
            raise TypeException(
                '{} is not allowed type. Operator {} only accepts {}'.format(t, self.NAME, self.ALLOWED_TYPES))
        return self.RESULT_TYPE




class IntOperator():
    ALLOWED_TYPES = [INT_TYPE]
    RESULT_TYPE = INT_TYPE


class IntBoolOperator():
    ALLOWED_TYPES = [INT_TYPE]
    RESULT_TYPE = BOOL_TYPE


class BoolOperator():
    ALLOWED_TYPES = [BOOL_TYPE]
    RESULT_TYPE = BOOL_TYPE


class PlusOperator(TwoParamsOperatorBase):
    MNEMONIC = 'add'
    ALLOWED_TYPES = [INT_TYPE, STRING_TYPE]
    RESULT_TYPE = None
    NAME = '+'

    def get_type(self, env):
        super().get_type(env)
        return self.param1.get_type(env)



class MinusOperator(TwoParamsOperatorBase, IntOperator):
    MNEMONIC = 'sub'
    NAME = '-'


class TimesOperator(TwoParamsOperatorBase, IntOperator):
    MNEMONIC = 'imul'
    NAME = '*'


class DivisionOperator(TwoParamsOperatorBase, IntOperator):
    MNEMONIC = 'div'
    NAME = '/'


class ModOperator(TwoParamsOperatorBase, IntOperator):
    MNEMONIC = 'div'
    NAME = '%'


class LTOperator(TwoParamsOperatorBase, IntBoolOperator):
    NAME = '<'


class LEOperator(TwoParamsOperatorBase, IntBoolOperator):
    NAME = '<='


class GTOperator(TwoParamsOperatorBase, IntBoolOperator):
    NAME = '>'


class GEOperator(TwoParamsOperatorBase, IntBoolOperator):
    NAME = '>='


class EQOperator(TwoParamsOperatorBase, BoolOperator):
    ALLOWED_TYPES = [INT_TYPE, STRING_TYPE, BOOL_TYPE]
    NAME = '=='


class NEOperator(TwoParamsOperatorBase, IntBoolOperator):
    ALLOWED_TYPES = [INT_TYPE, STRING_TYPE, BOOL_TYPE]
    NAME = '!='


class NegOperator(OneParamOperatorBase, IntOperator):
    NAME = '-'

    def get_value(self):
        value, code = self.param.get_type()
        code += ['mov eax, -1',
                 'imul eax, {}'.format(value)]
        return 'eax', code


class NotOperator(OneParamOperatorBase, BoolOperator):
    NAME = '!'


class AndOperator(TwoParamsOperatorBase, BoolOperator):
    NAME = '&&'


class OrOperator(TwoParamsOperatorBase, BoolOperator):
    NAME = '||'
