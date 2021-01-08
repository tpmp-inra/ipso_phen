import inspect
from typing import Union

import ipso_phen.ipapi.ipt as ipt
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.common_functions import get_module_classes


def get_ipt_class(class_name: str) -> Union[type, None]:
    ipt_classes_list = get_module_classes(
        package=ipt, class_inherits_from=IptBase, remove_abstract=True
    )
    for cls_ in ipt_classes_list:
        if inspect.isclass(cls_) and (cls_.__name__ == class_name):
            return cls_
    else:
        return None


def call_ipt(ipt_id: str, source, return_type: str = "result", **kwargs):
    """Processes an image/wrapper with an IPT using an function like syntax
    :param ipt_id: Class name of the IPT
    :param source: Wrapper or path to source image
    :param kwargs: Parameters for the IPT
    """
    item = get_ipt_class(ipt_id)
    if item is not None:
        with item(source, **kwargs) as (res, ipt):
            if res:
                if return_type == "data" and hasattr(ipt, "data_dict"):
                    return ipt.data_dict
                else:
                    return ipt.result
    return None


def chain_ipt(ipt_id: str, source, **kwargs):
    """Processes an image/wrapper with an IPT using an function like syntax
    :param ipt_id: Class name of the IPT
    :param source: Wrapper or path to source image
    :param kwargs: Parameters for the IPT
    """
    item = get_ipt_class(ipt_id)
    if item is not None:
        with item(source, **kwargs) as (res, ipt):
            if res:
                ipt.wrapper.current_image = ipt.result
                return ipt.wrapper
            else:
                return None
    return None


def call_ipt_func(ipt_id: str, function_name: str, source, **kwargs):
    """Processes an image/wrapper with an IPT using an function like syntax
    :param ipt_id:
    :param function_name:
    :param source:
    :param kwargs:
    :return:
    """
    cls_ = get_ipt_class(ipt_id)
    if cls_ is not None:
        item = cls_(**kwargs)
        func = getattr(item, function_name, None)
        if callable(func):
            return func(wrapper=source)
    return None


def call_ipt_code(
    ipt,
    file_name: str = "",
    generate_imports: bool = True,
    white_spaces: str = "",
    result_name: str = "",
    return_type: str = "result",
):
    """Returns the code needed to run the IPT with given parameters
    :param generate_imports:
    :param white_spaces:
    :param file_name:
    :param result_name:
    :param ipt: IPT
    """

    if generate_imports:
        res = "from ipso_phen.ipapi.base.ipt_functional import call_ipt\n"
        res += "\n"
    else:
        res = ""
    ipt_id = ipt.__class__.__name__
    res_name = ipt.result_name

    if result_name:
        res_name = result_name + " = "
    else:
        if not res_name or (res_name == "none"):
            res_name = ""
        else:
            res_name += " = "

    if file_name:
        source = f'"{file_name}"'
    else:
        source = f"wrapper"

    res += white_spaces + f"{res_name}call_ipt(\n"
    ws = white_spaces + "    "
    res += (
        f",\n{ws}".join(
            [
                f'{ws}ipt_id="{ipt_id}"',
                f"source={source}",
                f'return_type="{return_type}"',
            ]
            + [
                f"{p.name}={p.str_value}"
                for p in ipt.input_params(exclude_force_diredefaults=True)
            ]
        )
        + "\n"
    )
    res += white_spaces + ")\n"

    return res


def call_ipt_func_code(
    ipt,
    function_name: str,
    file_name: str = "",
    generate_imports: bool = True,
    white_spaces: str = "",
    result_name: str = "",
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
        res = "from ipso_phen.ipapi.ipt import call_ipt_func\n"
        if not file_name:
            res += f"{white_spaces}from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor\n"
        res += "\n"
    else:
        res = ""
    ipt_id = ipt.__class__.__name__
    res_name = ipt.result_name

    if result_name:
        res_name = result_name + " = "
    else:
        if not res_name or (res_name == "none"):
            res_name = ""
        else:
            res_name += " = "

    if file_name:
        res += f"{white_spaces}wrapper = BaseImageProcessor({file_name})\n"
        source = f"wrapper"
    else:
        source = f"wrapper"

    ws = white_spaces + "    "
    res += f"{white_spaces}{res_name}call_ipt_func(\n"
    res += f'{ws}ipt_id="{ipt_id}",\n{ws}source={source},\n{ws}function_name="{function_name}",\n{ws}'
    res += (
        f",\n{ws}".join(
            [f"{p.name}={p.str_value}" for p in ipt.input_params(exclude_defaults=True)]
        )
        + "\n"
    )
    res += f"{white_spaces})\n"

    return res
