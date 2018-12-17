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

    top_def: type_ id "(" arg? ")" block      -> top_def

    arg: type_ id ( "," type_ id )*           -> arg

    block: "{" stmt* "}"                      -> block

    ?stmt: ";"
        | block                               -> s_block
        | type_ item ( "," item )* ";"        -> s_decl
        | id "=" _expr ";"                    -> s_asg
        | id "++" ";"                         -> s_pp
        | id "--" ";"                         -> s_mm
        | "return" _expr ";"                  -> s_ret_val
        | "return" ";"                        -> s_ret_void
        | "if" "(" _expr ")" stmt             -> s_if
        | "if" "(" _expr ")" stmt "else" stmt -> s_if_else
        | "while" "(" _expr ")" stmt          -> s_while
        | _expr ";"                           -> s_expr

    type_: "int"     -> t_int
        | "string"   -> t_string
        | "boolean"  -> t_bool
        | "void"     -> t_void

    item: id                                  -> decl
        | id "=" _expr                        -> decl

    _expr : expr0
    ?expr0: expr1 "||" _expr   -> e_or         | expr1
    ?expr1: expr2 "&&" expr1   -> e_and        | expr2
    ?expr2: expr2 rel_op expr3 -> e_op         | expr3
    ?expr3: expr3 add_op expr4 -> e_op         | expr4
    ?expr4: expr4 mul_op expr5 -> e_op         | expr5
    ?expr5: "-"  expr6         -> e_neg
        |  "!"  expr6          -> e_not
        | expr6
    ?expr6: id                                  -> p_var
        | INT                                   -> p_int
        | "true"                                -> p_true
        | "false"                               -> p_false
        | id "(" ( _expr ( "," _expr )* )? ")"  -> call
        | ESCAPED_STRING                        -> p_string
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

    COMMENT     :  "/*" /(.|\\n|\\r)+/ "*/" |  "//" /(.)+/ NEWLINE | "#" /(.)+/ NEWLINE
    %import common.NEWLINE
    %import common.WS
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.INT

    %ignore COMMENT
    %ignore WS
    """

class MyTransformer(lark.Transformer):
    def string_value(selfself, params):
        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return params[0].value

    def program(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return Program(params)

    def top_def(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        if len(params) == 3:
            d_type, d_name, d_block = params
            d_args = Args([])
        else:
            d_type, d_name, d_args, d_block = params
        return TopDef(d_type, d_name, d_args, d_block)

    def arg(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        args = []
        for i in range(0, len(params), 2):
            args.append((params[i], params[i + 1]))

        return Args(args)

    def block(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return Block(params)

    def s_ret_void(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return RetVoidStmt()

    def s_block(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return BlockStmt(params[0])

    def s_decl(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        variables = []
        type = params[0]
        for param in params[1:]:
            print(params)
            if len(param) == 1:
                variables.append(VarDef(type, param[0], get_default_value(type)))
            else:
                variables.append(VarDef(type, param[0], param[1]))

        return DeclStmt(params[0], variables)

    def s_asg(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return AsgStmt(params[0], params[1])

    def s_pp(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return PPStmt(params[0])

    def s_mm(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return MMStrmt(params[0])

    def s_ret_val(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return RetValueStmt(params[0])

    def s_if(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return IfStmt(params[0], params[1])

    def s_if_else(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return IfElseStmt(params[0], params[1], params[2])

    def s_while(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return WhileStmt(params[0], params[1])

    def s_expr(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExprStmt(params[0])

    def t_int(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return INT_TYPE

    def t_bool(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return BOOL_TYPE

    def t_void(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return VOID_TYPE

    def t_string(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return STRING_TYPE


    def decl(self, params):
        return params


    def e_or(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpOperator(OrOperator(params[0], params[1]))

    def e_and(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpOperator(AndOperator(params[0], params[1]))

    def e_op(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        param1, operator, param2 = params
        operator.param1 = param1
        operator.param2 = param2
        return ExpOperator(params[1])

    def e_neg(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpOperator(NegOperator(params[0]))

    def e_not(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpOperator(NotOperator(params[0]))

    def p_var(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpVariable(params[0])

    def p_true(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpLitTrue()

    def p_false(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpLitFalse()

    def call(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpApp(params[0], params[1:])

    def p_string(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpLitString(params[0])

    def p_int(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ExpLitInt(int(params[0]))

    def op_plus(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return PlusOperator(None, None)

    def op_minus(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return MinusOperator(None, None)

    def op_times(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return TimesOperator(None, None)

    def op_div(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return DivisionOperator(None, None)

    def op_mod(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return ModOperator(None, None)

    def op_lt(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return LTOperator(None, None)

    def op_le(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return LEOperator(None, None)

    def op_gt(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return GTOperator(None, None)

    def op_ge(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return GEOperator(None, None)

    def op_eq(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return EQOperator(None, None)

    def op_ne(self, params):

        try:
            print(params[0].pos_in_stream)
           #)
            print(params[0].line)
            print(params[0].column)
        except:
            pass

        return NEOperator(None, None)


program = """
/* Test boolean operators. */

void xd(int x, string d) {
    return;
}

int main() {
  int x;
  int z;
  int y = z;
  
  5 + 3 / 8 * 9 - 7 % 1;
  
  printBool(test(-1) && test(0));
  printBool(test(-2) && test(1));
  printBool(test(3) && test(-5));
  printBool(test(234234) && test(21321));
  printString("||");
  printBool(test(-1) || test(0));
  printBool(test(-2) || test(1));
  printBool(test(3) || test(-5));
  printBool(test(234234) || test(21321));
  printString("!");
  printBool(true);
  printBool(false);
  return 0 ;

}

void printBool(boolean b) {
  if (!b) {
    printString("false");
  } else {
    printString("true");
 }
 return;
}

boolean test(int i) {
  printInt(i);
  return i > 0;
}
"""

program = MyTransformer().transform(lark.Lark(grammar, start="program").parse(program))
program.check_correctness()
program.compile()