import ipso_phen.ipapi.class_pipelines as class_pipelines
from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import get_module_classes


def ipo_factory(
    file_path,
    options=None,
    force_abstract: bool = False,
    data_base=None,
    scale_factor=1,
):
    if force_abstract:
        return BaseImageProcessor(
            file_path,
            options,
            database=data_base,
            scale_factor=scale_factor,
        )
    else:
        # Build unique class list
        ipt_classes_list = get_module_classes(
            package=class_pipelines,
            class_inherits_from=BaseImageProcessor,
            remove_abstract=True,
        )

        # Create temporary image wrapper to detect experiment
        fh = file_handler_factory(file_path, data_base)

        # Select able class
        ipt_classes_list = list(set(ipt_classes_list))
        for cls in ipt_classes_list:
            if callable(getattr(cls, "can_process", None)) and cls.can_process(
                dict(experiment=fh.experiment, robot=fh.__class__.__name__)
            ):
                return cls(
                    file_path,
                    options,
                    database=data_base,
                    scale_factor=scale_factor,
                )

        return BaseImageProcessor(
            file_path,
            options,
            database=data_base,
            scale_factor=scale_factor,
        )
