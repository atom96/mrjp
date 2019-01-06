from typing import List

from compiler import BaseBase, UndefinedVariableException, RegisterLocation, MemoryLocation, ABCMeta, abstractmethod, \
    Counter, InvalidCastException, CompilerException
from type import INT_TYPE, BOOL_TYPE, STRING_TYPE, get_size, can_be_casted, NULL_TYPE


def get_default_value(_type):
    try:
        return {
        INT_TYPE: ExpLitInt(0),
        BOOL_TYPE: ExpLitFalse(),
        STRING_TYPE: ExpLitString('""')
         }[_type]
    except KeyError:
        return ExpCast(ExpLitNull.instance(), _type)



class ExpBase(BaseBase):
    __metaclass__ = ABCMeta

    @abstractmethod
    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        raise NotImplementedError()

    def is_reference(self):
        return False

    def get_reference(self, location: RegisterLocation):
        raise AttributeError("Cannot give reference")

    def get_real_value(self):
        raise AttributeError("Cannot give real value")


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
            raise UndefinedVariableException('Variable {} is undefined'.format(self.name), self)

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return self.location.mov_to_register(location)

    def boolean_jmp(self, if_true, if_false):
        return [
            'cmp {}, 0'.format(self.location),
            'je {}'.format(if_false),
            'jmp {}'.format(if_true)
        ]

    def is_reference(self):
        return True

    def get_reference(self, location: RegisterLocation):
        return ['lea {}, [{}]'.format(location.full_name, self.location.abs_location)]

class ExpLitInt(ExpBase):
    def __init__(self, value):
        self.value = value

    def get_type(self, env):
        if not (-2**32 < self.value < 2**31 - 1):
            raise CompilerException('Constant does not fit in int type {}'.format(self.value), self)

        return INT_TYPE

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, {}'.format(location, self.value)]

    def get_real_value(self):
        return self.value


class ExpLitTrue(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '1', []

    def boolean_jmp(self, if_true, if_false):
        return ['jmp {}'.format(if_true)]

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, 1'.format(location)]

    def get_real_value(self):
        return True


class ExpLitFalse(ExpBase):
    def get_type(self, env):
        return BOOL_TYPE

    def generate_value(self):
        return '0', []

    def boolean_jmp(self, if_true, if_false):
        return ['jmp {}'.format(if_false)]

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['mov {}, 0'.format(location)]

    def get_real_value(self):
        return False


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


class ExpLitNull(ExpBase):
    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        return ['xor {}, {}'.format(location.full_name, location.full_name)]

    INSTANCE = None

    @staticmethod
    def instance():
        if ExpLitNull.INSTANCE is None:
            ExpLitNull.INSTANCE = ExpLitNull()
        return ExpLitNull.INSTANCE

    def get_type(self, env):
        return NULL_TYPE


class ExpApp(ExpBase):
    RESULT_REGISTER = RegisterLocation('eax', 'rax')

    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.type = None

    def get_type(self, env):
        types = [x.get_type(env) for x in self.args]
        try:
            try:
                env['fun'][self.name]['args'].check_types(types, env)
            except CompilerException as e:
                raise CompilerException(e.rlmsg, self)
            self.type = env['fun'][self.name]['type']
            return env['fun'][self.name]['type']
        except KeyError:
            raise UndefinedVariableException('Function {} is undefined'.format(self.name), self)

    @classmethod
    def mov_any_call_to_register(cls, location: RegisterLocation, name: str, args):
        result = [
            'push r12',
            'mov r12, rsp',
            'and rsp, 0xFFFFFFFFFFFFFFF0',
        ]

        if len(args) % 2 == 0:
            result.append('sub rsp, 8')

        for e in reversed(args):
            result += e.mov_to_register(cls.RESULT_REGISTER)
            result += ['push {}'.format(cls.RESULT_REGISTER.full_name)]

        result += [
            'call {}'.format(name),
            'mov rsp, r12',
            'pop r12',
            # 'add rsp, {}'.format(len(args) * 8)
        ]

        if location != cls.RESULT_REGISTER:
            result = ['push {}'.format(cls.RESULT_REGISTER.full_name)] + result + [
                'mov {}, {}'.format(location.full_name, cls.RESULT_REGISTER.full_name),
                'pop {}'.format(cls.RESULT_REGISTER.full_name)
            ]

        return result

    def mov_to_register(self, location: RegisterLocation):
        return self.mov_any_call_to_register(location, 'top_' + self.name, self.args)

    def boolean_jmp(self, if_true, if_false):
        r = RegisterLocation('eax', 'rax')
        result = ['push rax'] + self.mov_to_register(r)

        return result + [
                'cmp rax, 0',
                'pop rax',
                'je {}'.format(if_false),
                'jmp {}'.format(if_true)
            ]


class ExpOperator(ExpBase):
    def __init__(self, operator):
        self.operator = operator

    def get_type(self, env):
        try:
            return self.operator.get_type(env)
        except CompilerException as e:
            if e.obj.line is None or e.obj.column is None:
                raise CompilerException(e.rlmsg, self)
            else:
                raise e


    def mov_to_register(self, location: RegisterLocation):
        return self.operator.calc_to_register(location)

    def boolean_jmp(self, if_true, if_false):
        return self.operator.boolean_jmp(if_true, if_false)

    def get_real_value(self):
        self.operator.get_real_value()


class ExpNew(ExpBase):
    def __init__(self, type):
        self.type = type
        self.cls = None

    def get_type(self, env):
        try:
            self.cls = env['cls'][self.type.type_name]
        except KeyError:
            raise UndefinedVariableException('Class {} undefined'.format(self.type), self)
        return self.type

    def mov_to_register(self, location: RegisterLocation):
        result = [
            'push rdi',
            'mov rdi, {}'.format(self.cls.size),
            'call malloc',
            'mov QWORD [rax], {}'.format('vtable_' + self.cls.name)
        ]

        offset = 8
        for obj in self.cls.vt_table:
            for _ in obj['fields']:
                result.append('mov QWORD [rax + {}], 0'.format(offset))
                offset += 8

        result.append('pop rdi')

        if location.full_name != 'rax':
            result.insert(0, 'push rax')
            result.append('mov {}, rax'.format(location.full_name))
            result.append('pop rax')
        return result


class ExpAttribute(ExpBase):
    def __init__(self, expr, attr):
        self.expr = expr
        self.attr = attr
        self.cls = None
        self.type = None

    def get_type(self, env):
        cls = self.expr.get_type(env).type_name

        try:
            attr = env['cls'][cls].get_attribute(self.attr, env)
            self.cls = env['cls'][cls]
            self.type = attr.type
            return self.type
        except KeyError:
            raise UndefinedVariableException('Class {} is undefined'.format(cls), self)

    def mov_to_register(self, location: RegisterLocation) -> List[str]:
        result = self.expr.mov_to_register(location)
        offset = self.cls.get_attr_offset(self.attr)

        if get_size(self.type) == 4:
            register = location
            type = 'DWORD'
        else:
            register = location.full_name
            type = 'QWORD'

        result.append('mov {}, {} [{}+{}]'.format(register, type, location.full_name, offset))
        return result

    def is_reference(self):
        return True

    def get_reference(self, location: RegisterLocation):
        result = self.mov_to_register(location)
        result[-1] = result[-1].replace('mov', 'lea').replace(location.location, location.full_name).replace('DWORD', '').replace('QWORD', '')
        return result


class ExpMethodCall(ExpBase):
    def __init__(self, expr, method, args):
        self.expr = expr
        self.method = method
        self.args = args
        self.cls = None

    def get_type(self, env):
        types = [x.get_type(env) for x in self.args]
        cls = self.expr.get_type(env).type_name

        try:
            method = env['cls'][cls].get_method(self.method, env)
            try:
                method.args.check_types(types, env)
            except CompilerException as e:
                raise CompilerException(e.rlmsg, self)
            self.cls = env['cls'][cls]
            return method.type
        except KeyError:
            raise UndefinedVariableException('Class {} is undefined'.format(cls), self)

    def mov_to_register(self, location: RegisterLocation):
        r = RegisterLocation('r14d', 'r14')
        offset = self.cls.get_method_offset(self.method)

        result = ['push r14', 'push r13']
        result += self.expr.mov_to_register(r)

        result += ExpApp.mov_any_call_to_register(location, '[r14 + {}]'.format(offset), [r] + self.args)

        idx = result.index('call [r14 + {}]'.format(offset))

        result = result[:idx] + ['mov r13, r14', 'mov r14, QWORD [r14]'] + result[idx:]

        return result + ['pop r13', 'pop r14']

    def boolean_jmp(self, if_true, if_false):
        r = RegisterLocation('eax', 'rax')
        result = ['push rax'] + self.mov_to_register(r)

        return result + [
            'cmp rax, 0',
            'pop rax',
            'je {}'.format(if_false),
            'jmp {}'.format(if_true)
        ]

class ExpCast(ExpBase):
    def __init__(self, expr, type):
        self.expr = expr
        self.type = type

    def get_type(self, env):
        t = self.expr.get_type(env)
        if not can_be_casted(t, self.type, env):
            raise InvalidCastException("Type {} cannot be casted to {}".format(t, self.type), self)
        return self.type

    def mov_to_register(self, location: RegisterLocation):
        return self.expr.mov_to_register(location)