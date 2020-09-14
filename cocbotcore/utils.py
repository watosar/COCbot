# -*- coding: utf-8 -*-
import re
import random


def dice_roll(count, size):
    return tuple(random.randint(1, int(size)) for _ in range(int(count)))


class ExInt:
    '''
    for resistance roll op 
    '''
    __slots__ = ('_value',)
    
    def __init__(self, value):
        self._value = value
        
    def __int__(self):
        return self._value
    
    def __str__(self):
        return str(self._value)
    
    def __rshift__(self, other):
        '->'
        return ExInt(50+(self._value-other._value)*5)
    
    def __lshift__(self, other):
        '<-'
        return ExInt(50+(other._value-self._value)*5)
    
    def __add__(self, other):
        return ExInt(self._value+other._value)
    
    def __sub__(self, other):
        return ExInt(self._value-other._value)
    
    def __mul__(self, other):
        return ExInt(self._value*other._value)
    
    def __mod__(self, other):
        return ExInt(self._value%other._value)
        
    def __truediv__(self, other):
        return ExInt(self._value/other._value)
    
    def __floordiv__(self, other):
        return ExInt(self._value//other._value)
    
    def __pow__(self, other):
        return ExInt(self._value**other._value)
        

ndn_pat = re.compile('([0-9]+)[dD]([0-9]+)')
formula_pat = re.compile(*(
    f'[+]?{single}({compare}{single})?' 
    for numeric, operator
    in ((f'-?({ndn_pat.pattern}|[0-9]+)','(->|<-|\*\*|//|[-+*/%])',),)
    for single, compare 
    in ((f'({numeric}({operator}{numeric})*)','(<=|>=|[<>=])',),)
    ))


def format_for_resist_op(formula):
    formula = formula.replace('->', '>>').replace('<-', '<<')
    formula = re.sub('[0-9]+', lambda m: f'ExInt({m.group()})', formula)
    return formula


def calc(formula: str): #-> float, str
    _formula = formula
    while re.search('[(][^()]+[)]', _formula):
        _formula = re.sub('[(][^()]+[)]',lambda s:s.group()[1:-1],_formula)
    if not formula_pat.fullmatch(_formula):
        raise ValueError((400, '式が不正です'))
    # ndnの置換
    formula = ndn_pat.sub(lambda m: f'({"+".join(str(i) for i in dice_roll(*m.groups()))})', formula)
    
    _formula = format_for_resist_op(formula)
    
    formula_spls = re.split('(<=|>=|(?<=[^-])[<>=](?=[^-]))', formula)
    if len(formula_spls)==3:
        formula_f, op, formula_b = formula_spls
        if formula_f.count('(') != formula_f.count(')'):
            raise ValueError()
        _formula_f = format_for_resist_op(formula_f)
        _formula_b = format_for_resist_op(formula_b)
        calc_result_f = eval(_formula_f, {'ExInt': ExInt}, {})
        calc_result_b = eval(_formula_b, {'ExInt': ExInt}, {})
        formula = f'{calc_result_f}{op}{calc_result_b} |\\| {formula}'
        calc_result = eval(f'{calc_result_f}{op}{calc_result_b}')
    else:
        calc_result = int(eval(_formula, {'ExInt': ExInt}, {}))
    return calc_result, formula
