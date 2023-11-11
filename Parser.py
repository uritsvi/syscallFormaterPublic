from ply import lex
from ply import yacc

import Program

tokens = (
    'name_keyword',
    'id_keyword',

    'format_keyword',
    'field_keyword',
    'offset_keyword',
    'size_keyword',
    'signed_keyword',

    'colon',
    'semicolon',

    'number',
    'name',

    'new_line',

    'unsigned_keyword',
    'const_keyword',

    'short_keyword',
    'char_keyword',
    'int_keyword',
    'size_t_keyword',
    "pid_t_keyword",

    'struct_keyword',

    'asterisk',

)


def t_number(t):
    r"""\d+"""
    return t


def t_name_keyword(t):
    r"""name"""
    return t


def t_id_keyword(t):
    r"""ID"""
    return t


def t_format_keyword(t):
    r"""format"""
    return t


def t_field_keyword(t):
    r"""field"""
    return t


def t_offset_keyword(t):
    r"""offset"""
    return t


def t_signed_keyword(t):
    r"""signed"""
    return t


def t_new_line(t):
    r"""\n+"""


def t_unsigned_keyword(t):
    r"""unsigned"""
    return t


def t_const_keyword(t):
    r"""const"""
    return t


def t_short_keyword(t):
    r"""short"""
    return t


def t_char_keyword(t):
    r"""char"""
    return t


def t_int_keyword(t):
    r"""int"""
    return t


def t_size_t_keyword(t):
    r"""size_t"""
    return t


def t_pid_t_keyword(t):
    r"""pid_t"""
    return t


def t_struct_keyword(t):
    r"""struct"""
    return t


def t_size_keyword(t):
    r"""size"""
    return t


def t_test(t):
    r"""\t"""


t_name = r'\w+'
t_colon = r':'
t_semicolon = r';'
t_asterisk = r'\*'

t_ignore = " "


def t_error(t):
    print("error token t: " + str(t))


def p_program(p):
    """program : syscall_name \
                 syscall_id \
                 format_dec \
                 parameters """

    program_name = p[1]
    parameters = p[4]

    program_obj = Program.Program()
    program_obj.set_name(program_name)
    program_obj.set_parameters(parameters)
    p[0] = program_obj


def p_format_dec(p):
    """format_dec : format_keyword colon"""


def p_syscall_name(p):
    """syscall_name : name_keyword colon name """
    p[0] = p[3]


def p_syscall_id(p):
    """syscall_id : id_keyword colon number"""


def p_parameters(p):
    """parameters : parameter
                    | parameters parameter"""

    if len(p) == 2:
        parameters_list = []
        parameters_list.append(p[1])
        p[0] = parameters_list
    elif len(p) == 3:
        parameters_list = p[1]
        parameters_list.append(p[2])
        p[0] = parameters_list


def p_parameter(p):
    """parameter : field_keyword colon data_type name semicolon \
    offset_keyword colon number semicolon \
    size_keyword colon number semicolon \
    signed_keyword colon number semicolon"""

    parameters = Program.Parameter(p[3], p[4])
    p[0] = parameters


def p_data_type(p):
    """data_type : int_keyword
                   | short_keyword
                   | char_keyword
                   | size_t_keyword
                   | pid_t_keyword
                   | unsigned_keyword data_type
                   | const_keyword data_type
                   | data_type asterisk
                   | struct_keyword name"""

    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[1] + " " + p[2]


def p_error(p):
    print("error parsing tokens p: " + str(p))


def remove_last_line_from_string(s):
    return s[:s.rfind('\n')]


def pars(code):
    lexer = lex.lex()
    parser = yacc.yacc()

    lexer.input(code)
    program = parser.parse(code)

    if program is None:
        print("error generating program")
        exit(-1)

    return program
