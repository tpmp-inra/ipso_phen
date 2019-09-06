import inspect
import sys
from typing import Union

import ip_tools
from ip_base.ipt_abstract import IptBase
from tools.common_functions import get_module_classes


def _get_ipt_class(class_name: str) -> Union[type, None]:
    ipt_classes_list = get_module_classes(package=ip_tools, class_inherits_from=IptBase, remove_abstract=True)
    for cls_ in ipt_classes_list:
        if inspect.isclass(cls_) and (cls_.__name__ == class_name):
            return cls_
    else:
        return None


def call_ipt(ipt_id: str, source, **kwargs):
    """Processes an image/wrapper with an IPT using an function like syntax
    :param ipt_id: Class name of the IPT
    :param source: Wrapper or path to source image
    :param kwargs: Parameters for the IPT
    """
    item = _get_ipt_class(ipt_id)
    if item is not None:
        with item(source, **kwargs) as (res, ipt):
            if res:
                return ipt.result
    return None


def call_ipt_func(ipt_id: str, function_name: str, source, **kwargs):
    """Processes an image/wrapper with an IPT using an function like syntax
    :param ipt_id:
    :param function_name:
    :param source:
    :param kwargs:
    :return:
    """
    cls_ = _get_ipt_class(ipt_id)
    if cls_ is not None:
        item = cls_(**kwargs)
        func = getattr(item, function_name, None)
        if callable(func):
            return func(wrapper=source)
    return None


def call_ipt_code(
    ipt, file_name: str = '', generate_imports: bool = True, white_spaces: str = '', result_name: str = ''
):
    """Returns the code needed to run the IPT with given parameters
    :param generate_imports:
    :param white_spaces:
    :param file_name:
    :param result_name:
    :param ipt: IPT
    """

    if generate_imports:
        res = 'from ip_tools import call_ipt\n'
        res += '\n'
    else:
        res = ''
    ipt_id = ipt.__class__.__name__
    res_name = ipt.result_name

    if result_name:
        res_name = result_name + ' = '
    else:
        if not res_name or (res_name == 'none'):
            res_name = ''
        else:
            res_name += ' = '

    if file_name:
        source = f'"{file_name}"'
    else:
        source = f'wrapper'

    ws = white_spaces + '         ' + ''.join([' ' for _ in range(0, len(res_name))])
    res += f'{white_spaces}{res_name}call_ipt(ipt_id="{ipt_id}",\n'
    res += f'{ws}source={source},\n{ws}'
    res += f",\n{ws}".join([f"{p.name}={p.str_value}" for p in ipt.input_params(exclude_defaults=True)]
                          ) + ')\n'

    return res


def call_ipt_func_code(
    ipt,
    function_name: str,
    file_name: str = '',
    generate_imports: bool = True,
    white_spaces: str = '',
    result_name: str = ''
):
    """Returns the code needed to run a method from the IPT with given parameters
    :param function_name:
    :param generate_imports:
    :param white_spaces:
    :param file_name:
    :param result_name:
    :param ipt: IPT
    """

    if generate_imports:
        res = 'from ip_tools import call_ipt_func\n'
        if not file_name:
            res += f'{white_spaces}from ip_base.ip_abstract import AbstractImageProcessor\n'
        res += '\n'
    else:
        res = ''
    ipt_id = ipt.__class__.__name__
    res_name = ipt.result_name

    if result_name:
        res_name = result_name + ' = '
    else:
        if not res_name or (res_name == 'none'):
            res_name = ''
        else:
            res_name += ' = '

    if file_name:
        res += f'{white_spaces}wrapper = AbstractImageProcessor({file_name})\n'
        source = f'wrapper'
    else:
        source = f'wrapper'

    ws = white_spaces + \
         ''.join([' ' for _ in range(0, len('call_ipt_func '))]) + \
         ''.join([' ' for _ in range(0, len(res_name))])
    res += f'{white_spaces}{res_name}call_ipt_func(ipt_id="{ipt_id}",\n'
    res += f'{ws}source={source},\n{ws}function_name="{function_name}",\n{ws}'
    res += f",\n{ws}".join([f"{p.name}={p.str_value}" for p in ipt.input_params(exclude_defaults=True)]
                          ) + ')\n'

    return res
