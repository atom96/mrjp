from abc import ABCMeta, abstractmethod

from compiler import BaseBase, TypeException, RegisterLocation, Counter
from type import INT_TYPE, BOOL_TYPE, STRING_TYPE, is_type_matching
from expr import ExpApp


class OperatorBase(BaseBase):
    __metaclass__ = ABCMeta

    def calc_to_register(self, location: RegisterLocation):
        raise NotImplementedError()

    def get_real_value(self):
        raise AttributeError("Cannot give real value")


class TwoParamsOperatorBase(OperatorBase):
    regsiter1 = RegisterLocation('eax', 'rax')
    regsiter2 = RegisterLocation('ebx', 'rbx')

    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def get_type(self, env):
        t1 = self.param1.get_type(env)

        if self.ALLOWED_TYPES != 'Any' and t1 not in self.ALLOWED_TYPES:
            raise TypeException(
                '{} is not allowed type. Operator {} only accepts {}'.format(t1, self.NAME, self.ALLOWED_TYPES), self)

        t2 = self.param2.get_type(env)

        if self.ALLOWED_TYPES == 'Any':
            if not (is_type_matching(t1, t2, env) or is_type_matching(t2, t1, env)):
                raise TypeException('{} and {} types mismatch'.format(t1, t2), self)
        elif t1 != t2:
            raise TypeException('{} and {} types mismatch'.format(t1, t2), self)
        return self.RESULT_TYPE


class OneParamOperatorBase(OperatorBase):
    def __init__(self, param):
        self.param = param

    def get_type(self, env):
        t = self.param.get_type(env)
        if t not in self.ALLOWED_TYPES:
            raise TypeException(
                '{} is not allowed type. Operator {} only accepts {}'.format(t, self.NAME, self.ALLOWED_TYPES), self)
        return self.RESULT_TYPE


class IntOperator():
    ALLOWED_TYPES = [INT_TYPE]
    RESULT_TYPE = INT_TYPE


class BoolResultOperator():
    __metaclass__ = ABCMeta

    @abstractmethod
    def boolean_jmp(self, if_true, if_false):
        raise NotImplementedError()

    def calc_to_register(self, location: RegisterLocation):
        l_true = 'L{}'.format(Counter.get())
        l_false = 'L{}'.format(Counter.get())
        l_end = 'L{}'.format(Counter.get())

        return self.boolean_jmp(l_true, l_false) + [
            l_true + ':',
            'mov {}, 1'.format(location),
            'jmp {}'.format(l_end),
            l_false + ':',
            'mov {}, 0'.format(location),
            l_end + ':'
        ]


class IntBoolOperator(BoolResultOperator):
    __metaclass__ = ABCMeta

    ALLOWED_TYPES = [INT_TYPE]
    RESULT_TYPE = BOOL_TYPE

    @abstractmethod
    def boolean_jmp(self, if_true, if_false):
        raise NotImplementedError()


class BoolOperator(BoolResultOperator):
    __metaclass__ = ABCMeta

    ALLOWED_TYPES = [BOOL_TYPE]
    RESULT_TYPE = BOOL_TYPE

    @abstractmethod
    def boolean_jmp(self, if_true, if_false):
        raise NotImplementedError()


class TwoParamsIntOperator(TwoParamsOperatorBase, IntOperator):
    MNEMONIC = None

    def calc_to_register(self, location: RegisterLocation):
        if self.regsiter1 == location:
            temp_register = self.regsiter2
        else:
            temp_register = self.regsiter1

        return ['push {}'.format(temp_register.full_name)] + \
               self.param1.mov_to_register(location) + \
               self.param2.mov_to_register(temp_register) + \
               [
                   '{} {}, {}'.format(self.MNEMONIC, location, temp_register),
                   'pop {}'.format(temp_register.full_name)
               ]


class TwoParamsIntToBoolOperator(TwoParamsOperatorBase, IntBoolOperator):
    COMPARISON = None

    def boolean_jmp(self, if_true, if_false):
        return ['push {}'.format(self.regsiter1.full_name),
                'push {}'.format(self.regsiter2.full_name)] + \
               self.param1.mov_to_register(self.regsiter1) + \
               self.param2.mov_to_register(self.regsiter2) + \
               [
                   'cmp {}, {}'.format(self.regsiter1, self.regsiter2),
                   'pop {}'.format(self.regsiter2.full_name),
                   'pop {}'.format(self.regsiter1.full_name),
                   '{} {}'.format(self.COMPARISON, if_true),
                   'jmp {}'.format(if_false),
               ]

    def calc_to_register(self, location: RegisterLocation):
        return BoolResultOperator.calc_to_register(self, location)


class PlusOperator(TwoParamsIntOperator):
    MNEMONIC = 'add'
    ALLOWED_TYPES = [INT_TYPE, STRING_TYPE]
    RESULT_TYPE = None
    NAME = '+'

    def get_type(self, env):
        super().get_type(env)
        self.type = self.param1.get_type(env)
        return self.type

    def calc_to_register(self, location: RegisterLocation):
        if self.type == INT_TYPE:
            return super().calc_to_register(location)
        else:
            return ExpApp('strConcat', [self.param1, self.param2]).mov_to_register(location)

    def get_real_value(self):
        return self.param1.get_real_value() + self.param2.get_real_value()


class MinusOperator(TwoParamsIntOperator):
    MNEMONIC = 'sub'
    NAME = '-'

    def get_real_value(self):
        return self.param1.get_real_value() - self.param2.get_real_value()


class TimesOperator(TwoParamsIntOperator):
    MNEMONIC = 'imul'
    NAME = '*'

    def get_real_value(self):
        return self.param1.get_real_value() * self.param2.get_real_value()


class DivisionOperator(TwoParamsIntOperator):
    MNEMONIC = 'div'
    NAME = '/'
    STANDARD_LOCATION = RegisterLocation('eax', 'rax')
    DIVISOR_LOCATION = RegisterLocation('ebx', 'rbx')

    def calc_to_register(self, location: RegisterLocation):
        result = []

        result += self.param1.mov_to_register(self.STANDARD_LOCATION)
        result += self.param2.mov_to_register(self.DIVISOR_LOCATION)
        result += [
            'push rdx',
            'cdq',
            'idiv {}'.format(self.DIVISOR_LOCATION),
            'pop rdx'
        ]

        if location == self.STANDARD_LOCATION:
            result.insert(0, 'push {}'.format(self.DIVISOR_LOCATION.full_name))
            result.append('pop {}'.format(self.DIVISOR_LOCATION.full_name))
        elif location == self.DIVISOR_LOCATION:
            result.insert(0, 'push {}'.format(self.STANDARD_LOCATION.full_name))
            result.append('mov {}, {}'.format(location, self.STANDARD_LOCATION))
            result.append('pop {}'.format(self.STANDARD_LOCATION.full_name))
        else:
            result.insert(0, 'push {}'.format(self.DIVISOR_LOCATION.full_name))
            result.insert(1, 'push {}'.format(self.STANDARD_LOCATION.full_name))
            result.append('mov {}, {}'.format(location, self.STANDARD_LOCATION))
            result.append('pop {}'.format(self.STANDARD_LOCATION.full_name))
            result.append('pop {}'.format(self.DIVISOR_LOCATION.full_name))

        return result

    def get_real_value(self):
        return self.param1.get_real_value() // self.param2.get_real_value()


class ModOperator(DivisionOperator):
    MNEMONIC = 'div'
    NAME = '%'

    def calc_to_register(self, location: RegisterLocation):
        result = super().calc_to_register(location)
        idx = result.index('idiv {}'.format(self.DIVISOR_LOCATION))
        result.insert(idx + 1, 'mov eax, edx')
        return result

    def get_real_value(self):
        return self.param1.get_real_value() % self.param2.get_real_value()


class LTOperator(TwoParamsIntToBoolOperator):
    NAME = '<'
    COMPARISON = 'jl'

    def get_real_value(self):
        return self.param1.get_real_value() < self.param2.get_real_value()


class LEOperator(TwoParamsIntToBoolOperator):
    NAME = '<='
    COMPARISON = 'jle'

    def get_real_value(self):
        return self.param1.get_real_value() <= self.param2.get_real_value()


class GTOperator(TwoParamsIntToBoolOperator):
    NAME = '>'
    COMPARISON = 'jg'

    def get_real_value(self):
        return self.param1.get_real_value() > self.param2.get_real_value()


class GEOperator(TwoParamsIntToBoolOperator):
    NAME = '>='
    COMPARISON = 'jge'

    def get_real_value(self):
        return self.param1.get_real_value() >= self.param2.get_real_value()


class EQOperator(TwoParamsIntToBoolOperator):
    ALLOWED_TYPES = 'Any'
    NAME = '=='
    COMPARISON = 'je'

    def get_real_value(self):
        return self.param1.get_real_value() == self.param2.get_real_value()

    def boolean_jmp(self, if_true, if_false):
        return ['push {}'.format(self.regsiter1.full_name),
                'push {}'.format(self.regsiter2.full_name)] + \
               self.param1.mov_to_register(self.regsiter1) + \
               self.param2.mov_to_register(self.regsiter2) + \
               [
                   'cmp {}, {}'.format(self.regsiter1.full_name, self.regsiter2.full_name),
                   'pop {}'.format(self.regsiter2.full_name),
                   'pop {}'.format(self.regsiter1.full_name),
                   '{} {}'.format(EQOperator.COMPARISON, if_true),
                   'jmp {}'.format(if_false),
               ]


class NEOperator(TwoParamsIntToBoolOperator):
    ALLOWED_TYPES = 'Any'
    NAME = '!='
    COMPARISON = 'jne'

    def get_real_value(self):
        return self.param1.get_real_value() != self.param2.get_real_value()

    def boolean_jmp(self, if_true, if_false):
        return EQOperator.boolean_jmp(self, if_false, if_true)


class NegOperator(OneParamOperatorBase, IntOperator):
    NAME = '-'

    def calc_to_register(self, location: RegisterLocation):
        return self.param.mov_to_register(location) + \
               ['neg {}'.format(location)]

    def get_real_value(self):
        return -self.param.get_real_value()


class NotOperator(OneParamOperatorBase, BoolOperator):
    NAME = '!'

    def boolean_jmp(self, if_true, if_false):
        return self.param.boolean_jmp(if_false, if_true)

    def calc_to_register(self, location: RegisterLocation):
        return BoolResultOperator.calc_to_register(self, location)

    def get_real_value(self):
        return not self.param.get_real_value()


class AndOperator(TwoParamsOperatorBase, BoolOperator):
    NAME = '&&'

    def boolean_jmp(self, if_true, if_false):
        label = 'L{}'.format(Counter.get())

        result = self.param1.boolean_jmp(label, if_false)
        result += [label + ':']
        result += self.param2.boolean_jmp(if_true, if_false)
        return result

    def calc_to_register(self, location: RegisterLocation):
        return BoolResultOperator.calc_to_register(self, location)

    def get_real_value(self):
        return self.param1.get_real_value() and self.param2.get_real_value()


class OrOperator(TwoParamsOperatorBase, BoolOperator):
    NAME = '||'

    def boolean_jmp(self, if_true, if_false):
        label = 'L{}'.format(Counter.get())

        result = self.param1.boolean_jmp(if_true, label)
        result += [label + ':']
        result += self.param2.boolean_jmp(if_true, if_false)
        return result

    def calc_to_register(self, location: RegisterLocation):
        return BoolResultOperator.calc_to_register(self, location)

    def get_real_value(self):
        return self.param1.get_real_value() or self.param2.get_real_value()
