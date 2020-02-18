from uuid import uuid4
import json
from datetime import datetime as dt
from timeit import default_timer as timer

import numpy as np

from ip_base.ipt_abstract import (
    IptParam,
    IptBase,
    IptParamHolder,
    CLASS_NAME_KEY,
    MODULE_NAME_KEY,
    PARAMS_NAME_KEY,
)
from ip_base import ip_common as ipc
from ip_base.ipt_strict_pipeline import IptStrictPipeline
from ip_base.ip_abstract import AbstractImageProcessor
from tools.error_holder import ErrorHolder
from tools.common_functions import format_time

last_script_version = "0.2.0.0"

pp_last_error = ErrorHolder("Loose pipeline")


class MosaicData(object):
    def __init__(self, pipeline, enabled, images):
        super().__init__()
        self.enabled = enabled
        self.images = images
        if isinstance(self.images, str):
            self.images = [[i for i in line.split(",")] for line in self.images.split("\n")]
        self.pipeline = pipeline


class PipelineSettings(IptParamHolder):
    def __init__(self, pipeline, **kwargs):
        self.update_feedback_items = []
        super(PipelineSettings, self).__init__(**kwargs)
        self.mosaic = MosaicData(
            pipeline=pipeline,
            enabled=kwargs.get("mosaic_enabled", kwargs.get("build_mosaic", True) == 1),
            images=kwargs.get("mosaic_images", kwargs.get("mosaic_items", [["source", "mask"]])),
        )

    def build_params(self):
        self.add_text_output(
            is_single_line=True,
            name="image_output_path",
            desc="Images output folder",
            default_value="",
            hint="Path where images will be copied, if not absolute, will be relative to output CSV data file",
        )
        self.add_checkbox(
            name="debug_mode",
            desc="Display debug images",
            default_value=0,
            hint="Display module's intermediary images",
        )

    def params_to_dict(
        self,
        include_input: bool = True,
        include_output: bool = False,
        include_neutral: bool = False,
    ):
        dic = {}
        for p in self.gizmos:
            if (
                (include_input and p.is_input)
                or (include_output and p.is_output)
                or (include_neutral and p.is_neutral)
            ):
                dic[p.name] = p.value
        dic["mosaic_enabled"] = self.mosaic.enabled
        dic["mosaic_images"] = self.mosaic.images
        return dic

    def items(self):
        return self.gizmos + [self.mosaic]

    @property
    def node_count(self):
        return len(self.items())


class Node(object):
    def __init__(self, **kwargs):
        self.uuid = kwargs.get("uuid", str(uuid4()))
        if not self.uuid:
            self.uuid = str(uuid4())
        self.parent = kwargs.get("parent")
        self.last_result = {}

    def get_relevant_image(self):
        if self.output_type == ipc.IO_IMAGE:
            return self.last_result.get("image", np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8))
        elif self.output_type == ipc.IO_MASK:
            return self.last_result.get("mask", np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8))
        elif self.output_type in [ipc.IO_DATA, ipc.IO_ROI, ipc.IO_NONE]:
            return self.last_result.get(
                "image",
                self.last_result.get("mask", np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8)),
            )
        else:
            return np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8)

    def do_call_back(
        self, call_back, res, msg, data, is_progress=True, force_call_back=False, **kwargs
    ):
        call_back(
            res,
            msg,
            data
            if call_back is not None and (force_call_back or not self.root.parent.silent)
            else None,
            self.absolute_index + 1 if is_progress else -1,
            self.absolute_count if is_progress else -1,
        )
        md = np.array(self.root.parent.settings.mosaic.images)
        if isinstance(data, (GroupNode, ModuleNode)):
            dn = data.name
            if dn in md:
                self.root.parent.stored_mosaic_images[dn] = self.get_relevant_image()
        elif isinstance(data, AbstractImageProcessor):
            for d in data.image_list:
                if d["name"] in md:
                    self.root.parent.stored_mosaic_images[d["name"]] = d["image"]

    @property
    def root(self):
        root = self
        while root.parent is not None and not isinstance(root.parent, LoosePipeline):
            root = root.parent
        return root

    @property
    def absolute_index(self):
        if isinstance(self, GroupNode):
            if isinstance(self.parent, LoosePipeline):
                return self.absolute_count
            lst = self.root.as_pivot_list(index=self, types=("groups"))
        elif isinstance(self, ModuleNode):
            lst = self.root.as_pivot_list(index=self, types=("modules"))
        else:
            return -2
        return len(lst.get("before", ()))

    @property
    def absolute_count(self):
        if isinstance(self, GroupNode):
            return len(list(self.root.iter_items(types=("groups"))))
        elif isinstance(self, ModuleNode):
            return len(list(self.root.iter_items(types=("modules"))))
        else:
            return -2

    @property
    def target_reached(self):
        return self.root.parent._target_reached

    @target_reached.setter
    def target_reached(self, value):
        self.root.parent._target_reached = value


class ModuleNode(Node):
    def __init__(self, **kwargs):
        Node.__init__(self, **kwargs)
        self.enabled = kwargs.get("enabled", 1)
        self.tool = kwargs.get("tool")
        self.tool.owner = self

    def execute(self, wrapper: AbstractImageProcessor, **kwargs):
        call_back = kwargs.get("call_back", None)
        target_module = kwargs.get("target_module", "")
        if not self.last_result:
            before = timer()
            if self.tool.process_wrapper(wrapper=wrapper):
                # Get ROI
                if self.output_type == ipc.IO_ROI:
                    func = getattr(self.tool, "generate_roi", None)
                    if callable(func):
                        roi = func(wrapper=wrapper)
                        if roi is not None:
                            self.last_result["roi"] = roi
                            if not wrapper.store_images:
                                wrapper.store_image(
                                    image=roi.draw_to(
                                        dst_img=wrapper.current_image,
                                        line_width=wrapper.width // 200,
                                    ),
                                    text=self.name,
                                    force_store=True,
                                )
                    else:
                        self.do_call_back(
                            call_back=call_back,
                            res="ERROR",
                            msg=f"Failed to generate ROI from  {self.name}",
                            data=wrapper if self.root.parent.debug_mode else self,
                        )
                # Get data
                if hasattr(self.tool, "data_dict"):
                    self.last_result["data"] = self.tool.data_dict
                # Get image or mask
                key = "mask" if self.output_type == ipc.IO_MASK else "image"
                if self.uuid == target_module and len(wrapper.image_list) > 0:
                    self.last_result[key] = wrapper.image_list[-1]["image"]
                elif isinstance(self.tool.result, np.ndarray):
                    self.last_result[key] = self.tool.result
                elif len(wrapper.image_list) > 0:
                    self.last_result[key] = wrapper.image_list[-1]["image"]
                else:
                    self.last_result[key] = wrapper.current_image
                self.do_call_back(
                    call_back=call_back,
                    res="OK",
                    msg=f"Successfully processed {self.name} in {format_time(timer() - before)}",
                    data=wrapper if self.root.parent.debug_mode else self,
                )

            else:
                self.do_call_back(
                    call_back=call_back,
                    res="ERROR",
                    msg=f"Failed to processed {self.name}",
                    data=wrapper
                    if self.root.parent.debug_mode or self.uuid == target_module
                    else self,
                )

        return self.last_result

    def invalidate(self):
        self.last_result = {}

    def copy(self, parent):
        return ModuleNode(parent=parent, tool=self.tool, enabled=self.enabled, uuid=self.uuid,)

    def to_code(self, indent: int):
        pass

    def to_json(self):
        return {
            "node_type": "module",
            "tool": self.tool.to_json(),
            "enabled": self.enabled,
            "uuid": self.uuid,
        }

    @classmethod
    def from_json(cls, parent, json_data: dict):
        if json_data["node_type"] != "module":
            return None
        tool = IptBase.from_json(json_data["tool"])
        if isinstance(tool, Exception):
            pp_last_error.add_error(
                new_error_text=f"Failed to load module: {repr(tool)}",
                new_error_kind="pipeline_load_error",
            )
        elif isinstance(tool, IptBase):
            return ModuleNode(
                tool=tool, parent=parent, enabled=json_data["enabled"], uuid=json_data["uuid"]
            )

    def sugar_name(self):
        if self.tool.has_param("roi_name"):
            return f'{self.tool.name} {self.tool.get_value_of("roi_name")}'
        if self.tool.has_param("channel"):
            return f'{self.tool.name} {self.tool.get_value_of("channel")}'
        else:
            return self.tool.name

    @property
    def input_type(self):
        if isinstance(self.tool, IptBase):
            return self.tool.input_type
        else:
            return ipc.IO_NONE

    @property
    def output_type(self):
        if isinstance(self.tool, IptBase):
            return self.tool.output_type
        else:
            return ipc.IO_NONE

    @property
    def name(self):
        sn = self.sugar_name()
        nodes = [
            node
            for node in self.root.as_pivot_list(index=self, types=("modules",))["before"]
            if node.sugar_name() == sn
        ]
        return sn if len(nodes) == 0 else f"{sn} ({len(nodes)})"


class GroupNode(Node):
    def __init__(self, **kwargs):
        Node.__init__(self, **kwargs)
        self.merge_mode = kwargs.get("merge_mode")
        self.name = kwargs.get("name", "")
        self.nodes = kwargs.get("nodes", [])
        self.source = kwargs.get("source", "source")
        self.no_delete = kwargs.get("no_delete", False)
        self.last_result = {}

    def add_module(self, tool, enabled=1, uuid: str = "") -> ModuleNode:
        new_module = ModuleNode(parent=self, tool=tool, enabled=enabled, uuid=uuid)
        self.nodes.append(new_module)
        return new_module

    def add_group(
        self, merge_mode: str, name: str = "", source="", no_delete: bool = False, uuid: str = ""
    ):
        # Set source
        if not source:
            if len(self.nodes) > 0 and isinstance(self.nodes[-1], GroupNode):
                source = self.nodes[-1].uuid
            elif len(self.nodes) == 0:
                source = "source"
            else:
                source = "last_output"
        # Set unique name
        root = self.root
        group_names = [group.name for group in root.iter_items(types=("groups",))]
        if not name or name in group_names:
            if not name:
                name = "Group"
            i = 1
            while f"{name} {i}" in group_names:
                i += 1
            name = f"{name} {i}"
        # Create group
        new_node = GroupNode(
            parent=self, merge_mode=merge_mode, name=name, source=source, uuid=uuid
        )
        self.nodes.append(new_node)
        return new_node

    def remove_node(self, node: [int, object]):
        if isinstance(node, int):
            node = self.nodes[node]
        if not isinstance(node, GroupNode) or not node.no_delete:
            self.root.invalidate(node)
            self.nodes.remove(node)

    def insert_node(self, index, node):
        if isinstance(node, GroupNode) or isinstance(node, ModuleNode):
            self.nodes.insert(min(0, max(index, len(self.nodes))), node)

    def get_source_image(self, source: str, wrapper: AbstractImageProcessor, call_back):
        if source == "source":
            return wrapper.source_image
        elif source == "last_output":
            nodes = self.root.as_pivot_list(index=self)
            for node in reversed(nodes["before"]):
                if (
                    node.enabled
                    and node.output_type == ipc.IO_IMAGE
                    and node.last_result.get("image", None) is not None
                ):
                    return node.last_result["image"]
                    break
            else:
                return wrapper.current_image
        else:
            node = self.root.find_by_uuid(source)
            if node is None or node.last_result.get("image", None) is None or node.enabled == 0:
                self.last_result = {}
                self.do_call_back(
                    call_back=call_back,
                    res="WARNING",
                    msg=f"{self.name} - Failed to retrieve source {source}, selecting last output instead",
                    data=None,
                    is_progress=False,
                )
                return self.get_source_image(
                    source="last_output", wrapper=wrapper, call_back=call_back
                )
            else:
                return node.last_result.get("image")

    def execute(self, wrapper: AbstractImageProcessor, **kwargs):
        before = timer()
        call_back = kwargs.get("call_back", None)
        target_module = kwargs.get("target_module", "")
        wrapper.current_image = self.get_source_image(
            source=self.source, wrapper=wrapper, call_back=call_back
        )

        rois = []
        for node in self.nodes:
            if not node.enabled:
                continue
            if node.output_type != ipc.IO_ROI:
                only_rois = False
        else:
            only_rois = True

        if self.merge_mode == ipc.MERGE_MODE_NONE:
            for node in self.nodes:
                if not node.enabled:
                    continue
                res = node.execute(wrapper=wrapper, **kwargs)
                if self.target_reached:
                    return res
                if res:
                    if node.output_type == ipc.IO_DATA:
                        wrapper.csv_data_holder.data_list.update(res["data"])
                    elif node.output_type == ipc.IO_ROI:
                        wrapper.add_roi(new_roi=res["roi"])
                        rois.append(res["roi"])
                else:
                    self.last_result["outcome"] = False
                if node.uuid == target_module:
                    self.target_reached = True
                    return self.last_result
        elif self.merge_mode == ipc.MERGE_MODE_CHAIN:
            for node in self.nodes:
                if not node.enabled:
                    continue
                res = node.execute(wrapper=wrapper, **kwargs)
                if self.target_reached:
                    return res
                if res:
                    if node.output_type == ipc.IO_IMAGE:
                        wrapper.current_image = res["image"]
                    elif node.output_type == ipc.IO_MASK:
                        wrapper.mask = res["mask"]
                    elif node.output_type == ipc.IO_DATA:
                        wrapper.csv_data_holder.data_list.update(res["data"])
                    elif node.output_type == ipc.IO_ROI:
                        rois.extend(res["roi"])
                else:
                    self.last_result["outcome"] = False
                if node.uuid == target_module:
                    self.target_reached = True
                    return node.last_result
        elif self.merge_mode in [ipc.MERGE_MODE_AND, ipc.MERGE_MODE_OR]:
            images = []
            for node in self.nodes:
                if not node.enabled:
                    continue
                res = node.execute(wrapper=wrapper, **kwargs)
                if self.target_reached:
                    return res
                if res:
                    if node.output_type == ipc.IO_IMAGE:
                        images.append(res["image"])
                    elif node.output_type == ipc.IO_MASK:
                        images.append(res["mask"])
                else:
                    self.last_result["outcome"] = False
                if node.uuid == target_module:
                    self.target_reached = True
                    return node.last_result
            if self.merge_mode == ipc.MERGE_MODE_AND:
                res = wrapper.multi_and(images)
            else:
                res = wrapper.multi_or(images)
            if self.output_type == ipc.IO_IMAGE:
                wrapper.current_image = res
            elif self.output_type == ipc.IO_MASK:
                wrapper.mask = res
            else:
                self.do_call_back(
                    call_back=call_back,
                    res="ERROR",
                    msg=f'Invalid output type "{self.output_type}" for merge mode "{self.merge_mode}" in {self.name}',
                    data=None,
                    is_progress=False,
                )
                self.last_result["outcome"] = False
        else:
            pass

        if only_rois and rois:
            self.last_result["roi"] = rois
            self.last_result["image"] = wrapper.draw_rois(img=wrapper.current_image, rois=rois)
        else:
            self.last_result["image"] = wrapper.current_image
        self.last_result["mask"] = wrapper.mask
        self.last_result["data"] = wrapper.csv_data_holder.data_list

        status_message = f"Pipeline processed in {format_time(timer() - before)}"

        if self.is_root:
            if self.parent.settings.mosaic.enabled:
                self.do_call_back(
                    call_back=call_back,
                    res="OK",
                    msg=f"Pipeline processed in {format_time(timer() - before)}",
                    data={
                        "name": "final_mosaic",
                        "image": wrapper.build_mosaic(
                            image_names=self.parent.settings.mosaic.images,
                            images_dict=self.parent.stored_mosaic_images,
                        ),
                        "data": self.last_result["data"],
                    },
                    force_call_back=True,
                    is_progress=False,
                )
            else:
                self.do_call_back(
                    call_back=call_back,
                    res="OK",
                    msg=f"Pipeline processed in {format_time(timer() - before)}",
                    data=self,
                    force_call_back=True,
                    is_progress=False,
                )
        else:
            self.do_call_back(
                call_back=call_back,
                res="OK",
                msg=f"Successfully processed {self.name}, merge mode: {self.merge_mode} in {format_time(timer() - before)}",
                data=self,
                is_progress=False,
            )

        return self.last_result

    def copy(self, parent):
        return GroupNode(
            parent=parent,
            merge_mode=self.merge_mode,
            name=self.name,
            source=self.source,
            nodes=[node.copy(parent=self) for node in self.nodes],
        )

    def to_code(self, indent: int):
        pass

    def get_parent(self, item):
        for node in self.nodes:
            if hasattr(node, "uuid"):
                if item.uuid == node.uuid:
                    return self
            elif isinstance(node, GroupNode):
                parent = node.get_parent(item)
                if parent is not None:
                    return parent
        return None

    def to_json(self):
        return dict(
            node_type="group",
            merge_mode=self.merge_mode,
            name=self.name,
            uuid=self.uuid,
            source=self.source,
            no_delete=self.no_delete,
            nodes=[node.to_json() for node in self.nodes],
        )

    @classmethod
    def from_json(cls, parent, json_data: dict):
        res = GroupNode(
            parent=parent,
            merge_mode=json_data["merge_mode"],
            name=json_data["name"],
            uuid=json_data["uuid"],
            no_delete=json_data["no_delete"],
            source=json_data["source"],
        )
        for node in json_data["nodes"]:
            if node["node_type"] == "module":
                res.nodes.append(ModuleNode.from_json(parent=res, json_data=node))
            elif node["node_type"] == "group":
                res.nodes.append(GroupNode.from_json(parent=res, json_data=node))
            else:
                pp_last_error.add_error(
                    new_error_text=f"Unknown node type: {node['node_type']}",
                    new_error_kind="pipeline_load_error",
                )
        return res

    def modules(self):
        return [node for node in self.nodes if isinstance(node, ModuleNode)]

    def groups(self):
        return [node for node in self.nodes if isinstance(node, GroupNode)]

    def module(self, index) -> ModuleNode:
        lst = self.modules()
        if len(lst) > index:
            return lst[index]
        else:
            return None

    def group(self, index) -> Node:
        lst = self.groups()
        if len(lst) > index:
            return lst[index]
        else:
            return None

    def iter_items(self, types: tuple = ("groups", "modules")):
        def parse_children_(parent):
            for node in parent.nodes:
                if (("groups" in types) and isinstance(node, GroupNode)) or (
                    ("modules" in types) and isinstance(node, ModuleNode)
                ):
                    yield node
                if isinstance(node, GroupNode):
                    yield from parse_children_(node)

        if (("groups" in types) and isinstance(self, GroupNode)) or (
            ("modules" in types) and isinstance(self, ModuleNode)
        ):
            yield self
        yield from parse_children_(self)

    def as_pivot_list(self, index, types: tuple = ("groups", "modules")) -> dict:
        """Splits all nodes in three classes
            * before: all nodes before index
            * pivot: index
            * after: all nodes after index
        """
        nodes = [node for node in self.iter_items(types)]
        if index not in nodes:
            return {}
        res = {"before": [], "pivot": index, "after": []}
        matched_uuid = False
        for node in nodes:
            if node.uuid == index.uuid:
                matched_uuid = True
                continue
            if matched_uuid:
                res["after"].append(node)
            else:
                res["before"].append(node)
        return res

    def find_by_uuid(self, uuid):
        for node in self.iter_items():
            if node.uuid == uuid:
                return node
        else:
            return None

    def find_by_name(self, name):
        """ Returns the node that matches exactly the name
        There's no warranty that names are unique"""
        for node in self.iter_items():
            if node.name == name:
                return node
        else:
            return None

    def check_input(self, node) -> bool:
        if isinstance(node, GroupNode):
            if self.merge_mode in [ipc.MERGE_MODE_AND, ipc.MERGE_MODE_OR]:
                has_image, has_mask = False, False
                for node in self.nodes:
                    if node.output_type in [ipc.IO_DATA, ipc.IO_NONE, ipc.IO_ROI]:
                        return False
                    elif node.output_type == ipc.IO_IMAGE:
                        has_image = True
                    elif node.output_type == ipc.IO_MASK:
                        has_mask = True
                    else:
                        return False
                if has_image and has_mask:
                    return False
        if isinstance(node, GroupNode) and node.module_count > 0:
            n = node.module(0)
        else:
            n = node
        if isinstance(n, GroupNode):
            return True
        pivot_list = self.as_pivot_list(index=n, types=("modules"))
        if not pivot_list:
            return False
        if len(pivot_list["before"]) > 0:
            if n.input_type == ipc.IO_DATA:
                needed_output = ipc.IO_DATA
            elif n.input_type == ipc.IO_IMAGE:
                return True
            elif n.input_type == ipc.IO_MASK:
                needed_output = ipc.IO_MASK
            elif n.input_type == ipc.IO_NONE:
                return True
            elif n.input_type == ipc.IO_ROI:
                needed_output = ipc.IO_ROI
            for node in pivot_list["before"]:
                if node.output_type in needed_output:
                    return True
            else:
                return False
        else:
            return n.input_type in (ipc.IO_IMAGE)

    def invalidate(self, node):
        pivot_list = self.as_pivot_list(index=node)
        node.last_result = {}
        for node in pivot_list["after"]:
            if isinstance(node, ModuleNode):
                node.invalidate()
            elif isinstance(node, GroupNode):
                node.last_result = {}

    @property
    def input_type(self):
        if len(self.nodes) == 0:
            return ipc.IO_NONE
        else:
            return self.nodes[0].input_type

    @property
    def output_type(self):
        if len(self.nodes) == 0:
            return ipc.IO_NONE
        else:
            return self.nodes[-1].output_type

    @property
    def node_count(self):
        return len(self.nodes)

    @property
    def group_count(self):
        return len(self.groups())

    @property
    def module_count(self):
        return len(self.modules())

    @property
    def enabled(self):
        if self.node_count == 0:
            return 0
        else:
            has_enabled = False
            has_disabled = False
            for node in self.nodes:
                if isinstance(node, GroupNode):
                    enabled_state = node.enabled
                    if enabled_state == 0:
                        has_disabled = True
                    elif enabled_state == 1:
                        return 1
                    elif enabled_state == 2:
                        has_enabled = True
                elif isinstance(node, ModuleNode):
                    if node.enabled:
                        has_enabled = True
                    else:
                        has_disabled = True
                if has_enabled and has_disabled:
                    return 1
            return 2 if has_enabled else 0

    @enabled.setter
    def enabled(self, value):
        for node in self.nodes:
            node.enabled = value

    @property
    def is_root(self):
        return isinstance(self.parent, LoosePipeline)


class LoosePipeline(object):
    def __init__(self, **kwargs):
        self.root: GroupNode = GroupNode(
            merge_mode=ipc.MERGE_MODE_CHAIN, name="Pipeline", parent=self
        )
        self.target_data_base = None
        self.settings = PipelineSettings(pipeline=self)
        self.last_wrapper_luid = ""
        self.use_cache = True
        self.image_output_path = ""
        self.name = ""
        self.description = "Please insert description"
        self.stored_mosaic_images = {}
        self._target_reached = False
        self.set_template(kwargs.get("template", None))
        self.silent = False

        self.set_callbacks()

    def __repr__(self):
        return json.dumps(self.to_json(), indent=2, sort_keys=False)

    def __str__(self):
        return f"Pipeline {self.name}"

    def set_template(self, template):
        if isinstance(template, str):
            if template == "default":
                self.root.add_group(
                    name="Fix image",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="source",
                    uuid="fix_image",
                )
                self.root.add_group(
                    name="Pre process image",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source=self.root.group(0).uuid,
                    uuid="pre_process_image",
                )
                self.root.add_group(
                    name="Build mask",
                    merge_mode=ipc.MERGE_MODE_AND,
                    source=self.root.group(1).uuid,
                    uuid="build_mask",
                )
                self.root.add_group(
                    name="Clean mask",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source=self.root.group(1).uuid,
                    uuid="clean_mask",
                )
                self.root.add_group(
                    name="Extract features",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source=self.root.group(0).uuid,
                    uuid="extract_features",
                )
            elif template == "legacy":
                self.root.add_group(
                    name="ROIs from raw image",
                    merge_mode=ipc.MERGE_MODE_NONE,
                    source="source",
                    uuid="roi_raw",
                )
                self.root.add_group(
                    name="Fix image",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="source",
                    uuid="fix_image",
                )
                self.root.add_group(
                    name="Pre process image",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="fix_image",
                    uuid="pre_process_image",
                )
                self.root.add_group(
                    name="ROIs from raw pre processed image",
                    merge_mode=ipc.MERGE_MODE_NONE,
                    source="pre_process_image",
                    uuid="roi_pre_processed",
                )
                self.root.add_group(
                    name="Build mask",
                    merge_mode=ipc.MERGE_MODE_AND,
                    source="pre_process_image",
                    uuid="build_mask",
                )
                self.root.add_group(
                    name="Clean mask",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="pre_process_image",
                    uuid="clean_mask",
                )
                self.root.add_group(
                    name="Extract features",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="fix_image",
                    uuid="extract_features",
                )
                self.root.add_group(
                    name="Build images",
                    merge_mode=ipc.MERGE_MODE_CHAIN,
                    source="fix_image",
                    uuid="build_images",
                )

    def execute(self, src_image: str, silent_mode: bool = False, **kwargs):
        self._target_reached = False
        pp_last_error.clear()
        if isinstance(src_image, str):
            wrapper = AbstractImageProcessor(src_image)
            wrapper.lock = True
        elif isinstance(src_image, AbstractImageProcessor):
            wrapper = src_image
        else:
            pp_last_error.add_error(
                new_error_text="Unknown source", new_error_kind="pipeline_process_error"
            )
            return
        if self.last_wrapper_luid != wrapper.luid:
            self.invalidate()
            self.last_wrapper_luid = wrapper.luid
        wrapper.target_database = kwargs.get("target_data_base", None)
        wrapper.store_images = self.root.parent.debug_mode or kwargs.get("target_module", "")
        self.silent = silent_mode
        self.root.execute(wrapper=wrapper, **kwargs)
        return True

    def targeted_callback(self, param: IptParam):
        if param.name == "debug_mode":
            if self.root.nodes:
                self.root.invalidate(self.root)
        else:
            print(f"{param.name} was set")

    def set_callbacks(self):
        p = self.settings.find_by_name(name="debug_mode")
        if p is not None:
            p.on_change = self.targeted_callback

    def invalidate(self):
        for node in self.root.iter_items():
            if isinstance(node, ModuleNode):
                node.invalidate()
            elif isinstance(node, GroupNode):
                node.last_result = {}

    def save(self, file_name: str) -> bool:
        pp_last_error.clear()
        try:
            with open(file_name, "w") as f:
                json.dump(self.to_json(), f, indent=2)
        except Exception as e:
            pp_last_error.add_error(
                new_error_text=f'Failed to save pipeline "{repr(e)}"',
                new_error_kind="pipeline_save_error",
            )
            return False
        else:
            return True

    @classmethod
    def load(cls, file_name: str):
        with open(file_name, "r") as f:
            return cls.from_json(json_data=json.load(f))

    def copy(self):
        return self.__class__.from_json(self.to_json())

    def get_parent(self, item: [GroupNode, ModuleNode]) -> GroupNode:
        return self.root.get_parent(item=item)

    def remove_item(self, item: [GroupNode, ModuleNode]):
        self.root.remove_node(item)

    def to_code(self):
        pass

    def to_json(self):
        save_dict = {
            "title": "IPSO Phen pipeline V2",
            "name": self.name,
            "description": self.description,
            "date": dt.now().strftime("%Y_%b_%d_%H-%M-%S"),
            "version": last_script_version,
        }
        # Add settings
        save_dict["settings"] = self.settings.params_to_dict()
        # Add root node
        save_dict["Pipeline"] = self.root.to_json()
        return save_dict

    @classmethod
    def from_json(cls, json_data: dict):
        if json_data["title"].lower() == "ipso phen pipeline v2":
            res = cls()
            res.name = json_data["name"]
            res.description = json_data["description"]
            res.settings = PipelineSettings(pipeline=res, **json_data["settings"])
            res.root = GroupNode.from_json(parent=res, json_data=json_data["Pipeline"])
        elif json_data["title"].lower() == "ipso phen pipeline":
            res = cls(template="default_groups")
            tmp = IptStrictPipeline.from_json(json_data=json_data)

            # Import basic data
            res.name = tmp.name
            res.description = "Pipeline imported from old format, pleas check data"

            # Import settings
            for setting in res.settings.gizmos:
                p = tmp.settings.find_by_name(setting.name)
                if p is not None:
                    setting.value = p.value

            # create groups
            res.set_template(template="legacy")

            # Import nodes & modules
            for uuid, kinds in zip(
                [
                    "roi_raw",
                    "fix_image",
                    "pre_process_image",
                    "roi_pre_processed",
                    "build_mask",
                    "clean_mask",
                    "extract_features",
                    "build_images",
                ],
                [
                    ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR,
                    [ipc.TOOL_GROUP_WHITE_BALANCE_STR, ipc.TOOL_GROUP_EXPOSURE_FIXING_STR],
                    ipc.TOOL_GROUP_PRE_PROCESSING_STR,
                    ipc.TOOL_GROUP_ROI_PP_IMAGE_STR,
                    ipc.TOOL_GROUP_THRESHOLD_STR,
                    ipc.TOOL_GROUP_MASK_CLEANUP_STR,
                    ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR,
                    ipc.TOOL_GROUP_IMAGE_GENERATOR_STR,
                ],
            ):
                src_group = tmp.get_operators(constraints={"kind": kinds})
                dst_group = res.root.find_by_uuid(uuid=uuid)
                for tool_dict in src_group:
                    dst_group.add_module(
                        tool=tool_dict["tool"].copy(),
                        enabled=tool_dict["enabled"],
                        uuid=tool_dict["uuid"],
                    )
            res.root.find_by_uuid(uuid="build_mask").merge_mode = (
                ipc.MERGE_MODE_AND if tmp.merge_method == "multi_and" else ipc.MERGE_MODE_OR
            )

        res.set_callbacks()
        return res

    @property
    def node_count(self):
        return len(self.root.nodes)

    @property
    def threshold_only(self):
        return self.settings.get_value_of("threshold_only") == 1

    @threshold_only.setter
    def threshold_only(self, value):
        self.settings.set_value_of(
            key="threshold_only", value=1 if value is True else 0, update_widgets=False
        )

    @property
    def debug_mode(self):
        return self.settings.get_value_of("debug_mode") == 1

    @debug_mode.setter
    def debug_mode(self, value):
        self.settings.set_value_of(
            key="debug_mode", value=1 if value is True else 0, update_widgets=False
        )

    @property
    def image_output_path(self):
        return self.settings.get_value_of("image_output_path")

    @image_output_path.setter
    def image_output_path(self, value):
        self.settings.set_value_of("image_output_path", value)

    @property
    def last_image(self):
        return self.settings.get_value_of("last_image")

    @last_image.setter
    def last_image(self, value):
        self.settings.set_value_of("last_image", value)