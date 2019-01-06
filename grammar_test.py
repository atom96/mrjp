import sys

from lark import Tree, Token

from expr import *
from oprt import *
from type import *
from stmt import *
from compiler import *

import lark

grammar = r"""

    program: top_def+                         -> program

    ?top_def: fun_def 
             | "class" id "{" cls_def* "}"               -> cls_def 
             | "class" id "extends" id "{" cls_def* "}"  -> cls_extends_def
    
    ?cls_def: fun_def | field 
    
    fun_def: type_ id "(" arg? ")" block      -> fun_def

    arg: type_ id ( "," type_ id )*           -> arg

    field: type_ id ";"                       -> field

    block: "{" stmt* "}"                      -> block

    ?stmt: ";"                                -> s_empty
        | "return" _expr ";"                  -> s_ret_val
        | "return" ";"                        -> s_ret_void
        | block                               -> s_block
        | _expr "=" _expr ";"                 -> s_asg
        | _expr "++" ";"                      -> s_pp
        | _expr "--" ";"                      -> s_mm
        | "if" "(" _expr ")" stmt             -> s_if
        | "if" "(" _expr ")" stmt "else" stmt -> s_if_else
        | "while" "(" _expr ")" stmt          -> s_while
        | stmt2
        
    ?stmt2: type_ item ( "," item )* ";"        -> s_decl
        | _expr ";"                           -> s_expr

    type_: "int"     -> t_int
        | "string"   -> t_string
        | "boolean"  -> t_bool
        | "void"     -> t_void
        | id         -> t_class

    item: id                                  -> decl
        | id "=" _expr                        -> decl

    _expr : expr0
    ?expr0: expr1 "||" _expr   -> e_or         | expr1
    ?expr1: expr2 "&&" expr1   -> e_and        | expr2
    ?expr2: expr2 rel_op expr3 -> e_op         | expr3
    ?expr3: expr3 add_op expr4 -> e_op         | expr4
    ?expr4: expr4 mul_op expr5 -> e_op         | expr5
    ?expr5: "(" id ")" expr5   -> e_cast       | expr6    
    ?expr6: "new" id           -> e_new        | expr7
    
    ?expr7: "-"  expr7         -> e_neg
        |  "!"  expr7          -> e_not
        | expr8
    
    ?expr8: id                                  -> p_var
        | INT                                   -> p_int
        | "true"                                -> p_true
        | "false"                               -> p_false
        | "null"                                -> p_null
        | ESCAPED_STRING                        -> p_string
        | expr8 "." id                          -> e_cls_attr
        | id "(" ( _expr ( "," _expr )* )? ")"  -> call
        | expr8 "." id "(" ( _expr ( "," _expr )* )? ")"  -> e_cls_call
        
        |"(" _expr ")"

    add_op: "+" -> op_plus
        | "-"   -> op_minus

    mul_op: "*" -> op_times
        | "/"   -> op_div
        | "%"   -> op_mod

    rel_op: "<" -> op_lt
        | "<="  -> op_le
        | ">"   -> op_gt
        | ">="  -> op_ge
        | "=="  -> op_eq
        | "!="  -> op_ne

    ?id: CNAME -> string_value

    COMMENT     :  "/*" /(.|\n|\r)+/ "*/" |  "//" /[^\n]/* | "#" /[^\n]/*
    %import common.NEWLINE
    %import common.WS
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.INT

    %ignore COMMENT
    %ignore WS
    """


class MyTransformer(lark.Transformer):

    @lark.v_args(meta=True)
    def string_value(self, params, meta):
        return params[0].value

    @lark.v_args(meta=True)
    def program(self, params, meta):

        classes = []
        functions = []

        for param in params:
            if param.__class__.__name__ == 'FunDef':
                functions.append(param)
            else:
                classes.append(param)

        return Program(functions, classes)

    @lark.v_args(meta=True)
    def field(self, params, meta):
        result = Field(params[1], params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def arg(self, params, meta):
        args = []
        for i in range(0, len(params), 2):
            args.append((params[i], params[i + 1]))

        result = Args(args)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def block(self, params, meta):
        result = Block(params)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def decl(self, params, meta):
        return params

    # ==== Definitions ====
    @lark.v_args(meta=True)
    def fun_def(self, params, meta):
        if len(params) == 3:
            d_type, d_name, d_block = params
            d_args = Args([])
        else:
            d_type, d_name, d_args, d_block = params
        result = FunDef(d_type, d_name, d_args, d_block)
        result.line = meta.line
        result.column = meta.column
        return result

    def cls_def(self, params):
        name = params[0]
        fields = []
        methods = []

        for param in params[1:]:
            if param.__class__.__name__ == 'Field':
                fields.append(param)
            elif param.__class__.__name__ == 'FunDef':
                methods.append(param)
            else:
                print("Unknown param", param)
        result = ClassDef(name, fields, methods)
        return result

    @lark.v_args(meta=True)
    def cls_extends_def(self, params, meta):
        name = params[0]
        parent = params[1]

        cls = self.cls_def([name] + params[2:])
        cls.parent = parent
        result = cls
        result.line = meta.line
        result.column = meta.column
        return result

    # ==== Statements ====

    @lark.v_args(meta=True)
    def s_empty(self, params, meta):
        result = EmptyStmt()
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_ret_void(self, params, meta):
        result = RetVoidStmt()
        result.line = meta.line
        result.column = meta.column
        return result

    def s_block(self, params):
        result = BlockStmt(params[0])
        return result

    @lark.v_args(meta=True)
    def s_decl(self, params, meta):
        variables = []
        type = params[0]
        for param in params[1:]:
            if len(param) == 1:
                variables.append(VarDef(type, param[0], get_default_value(type)))
            else:
                variables.append(VarDef(type, param[0], param[1]))

        result = DeclStmt(params[0], variables)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_asg(self, params, meta):
        result = AsgStmt(params[0], params[1])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_pp(self, params, meta):
        result = PPStmt(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_mm(self, params, meta):
        result = MMStrmt(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_ret_val(self, params, meta):
        result = RetValueStmt(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_if(self, params, meta):
        result = IfStmt(params[0], params[1])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_if_else(self, params, meta):
        result = IfElseStmt(params[0], params[1], params[2])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_while(self, params, meta):
        result = WhileStmt(params[0], params[1])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def s_expr(self, params, meta):
        result = ExprStmt(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    # ==== TYPES ====

    @lark.v_args(meta=True)
    def t_int(self, params, meta):
        return INT_TYPE

    @lark.v_args(meta=True)
    def t_bool(self, params, meta):
        return BOOL_TYPE

    @lark.v_args(meta=True)
    def t_void(self, params, meta):
        return VOID_TYPE

    @lark.v_args(meta=True)
    def t_string(self, params, meta):
        return STRING_TYPE

    @lark.v_args(meta=True)
    def t_class(self, params, meta):
        return Type(params[0])

    # ==== Expressions ====

    @lark.v_args(meta=True)
    def e_or(self, params, meta):
        result = ExpOperator(OrOperator(params[0], params[1]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_and(self, params, meta):
        result = ExpOperator(AndOperator(params[0], params[1]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_op(self, params, meta):
        param1, operator, param2 = params
        operator.param1 = param1
        operator.param2 = param2
        result = ExpOperator(params[1])

        return result

    @lark.v_args(meta=True)
    def e_neg(self, params, meta):
        result = ExpOperator(NegOperator(params[0]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_not(self, params, meta):
        result = ExpOperator(NotOperator(params[0]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_var(self, params, meta):
        result = ExpVariable(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_true(self, params, meta):
        result = ExpLitTrue()
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_false(self, params, meta):
        result = ExpLitFalse()
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def call(self, params, meta):
        result = ExpApp(params[0], params[1:])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_string(self, params, meta):
        result = ExpLitString(params[0])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_int(self, params, meta):
        result = ExpLitInt(int(params[0]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def p_null(self, params, meta):
        result = ExpLitNull()
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_new(self, params, meta):
        result = ExpNew(Type(params[0]))
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_cls_call(self, params, meta):
        result = ExpMethodCall(params[0], params[1], params[2:])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_cls_attr(self, params, meta):
        result = ExpAttribute(params[0], params[1])
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def e_cast(self, params, meta):
        result = ExpCast(params[1], Type(params[0]))
        result.line = meta.line
        result.column = meta.column
        return result

    # ==== Operators ====
    @lark.v_args(meta=True)
    def op_plus(self, params, meta):
        result = PlusOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_minus(self, params, meta):
        result = MinusOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_times(self, params, meta):
        result = TimesOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_div(self, params, meta):
        result = DivisionOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_mod(self, params, meta):
        result = ModOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_lt(self, params, meta):
        result = LTOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_le(self, params, meta):
        result = LEOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_gt(self, params, meta):
        result = GTOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_ge(self, params, meta):
        result = GEOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_eq(self, params, meta):
        result = EQOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result

    @lark.v_args(meta=True)
    def op_ne(self, params, meta):
        result = NEOperator(None, None)
        result.line = meta.line
        result.column = meta.column
        return result


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG)

    path = sys.argv[1]

    with open(path) as f:
        try:
            program = lark.Lark(grammar, start="program", parser='lalr', propagate_positions=True, debug=True).parse(
                f.read())
        except FileNotFoundError as e:
            print(e)
            exit(1)
        except lark.exceptions.LarkError as e:
            line = getattr(e, 'line', 'undefined')
            column = getattr(e, 'column', 'undefined')

            print("Syntax error at line {} column {}".format(line, column))
            exit(1)
        program = MyTransformer().transform(program)
    try:
        program.check_correctness()
        asm = program.compile()
        with open(sys.argv[1][:-4] + '.s', 'w') as f:
            f.write(asm)

    except CompilerException as e:
        print(e)
        sys.exit(1)
