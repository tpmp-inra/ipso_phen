from uuid import uuid4
import json
from datetime import datetime as dt

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

last_script_version = "0.1.0.0"

IT_IMAGE = "input_type_image"
IT_MASK = "input_type_mask"

OT_IMAGE = "output_type_image"
OT_MASK = "output_type_mask"
OT_ROI = "output_type_roi"
OT_DATA = "output_type_data"

MO_AND = "merge_option_and"
MO_OR = "merge_option_or"
MO_CHAIN = "merge_option_chain"
MO_NONE = "merge_option_none"


pp_last_error = ErrorHolder("Loose pipeline")


class PipelineSettings(IptParamHolder):
    def __init__(self, **kwargs):
        self.update_feedback_items = []
        super(PipelineSettings, self).__init__(**kwargs)

    def build_params(self):
        self.add_checkbox(name="threshold_only", desc="Find mask only", default_value=0)
        self.add_checkbox(
            name="display_images", desc="Display step by step images", default_value=1
        )
        self.add_checkbox(name="build_mosaic", desc="Display mosaic", default_value=0)
        self.add_text_input(
            name="mosaic_items",
            desc="Mosaic items",
            default_value="""source,exposure_fixed,pre_processed_image\ncoarse_mask,clean_mask, mask_on_exp_fixed_bw_with_morph""",
            hint="""Names of the images to be included in the mosaic""",
            is_single_line=False,
        )
        self.add_text_output(
            is_single_line=True,
            name="image_output_path",
            desc="Images output folder",
            default_value="",
            hint="Path where images will be copied, if not absolute, will be relative to output CSV data file",
        )
        self.add_text_input(
            name="last_image",
            desc="Last image to be displayed",
            default_value="",
            hint="""Image to be displayed once the pipeline has finished.
            If empty last image will be displayed.
            Overridden by mosaic setting""",
        )

    def reset(self, is_update_widgets: bool = True):
        for p in self._param_list:
            if p.is_input:
                p.value = p.default_value
                p.clear_widgets()

    @property
    def node_count(self):
        return len(self.gizmos)


class ModuleNode(object):
    def __init__(self, **kwargs):
        self.tool = kwargs.get("tool")
        self.enabled = kwargs.get("enabled", 1)
        self.uuid = kwargs.get("uuid", str(uuid4()))
        self.parent = kwargs.get("parent")

    def execute(self, **kwargs):
        pass

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
    def from_json(cls, json_data: dict):
        if json_data["node_type"] != "module":
            return None
        tool = IptBase.from_json(json_data["tool"])
        if isinstance(tool, Exception):
            pp_last_error.add_error(
                new_error_text=f"Failed to load module: {repr(tool)}",
                new_error_kind="pipeline_load_error",
            )
        elif isinstance(tool, IptBase):
            return ModuleNode(tool=tool, enabled=json_data["enabled"], uuid=json_data["uuid"])

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


class GroupNode(object):
    def __init__(self, **kwargs):
        self.merge_mode = kwargs.get("merge_mode")
        self.name = kwargs.get("name", "")
        self.nodes = kwargs.get("nodes", [])
        self.parent = kwargs.get("parent")

    def add_module(self, tool, enabled=1, uuid: str = "") -> ModuleNode:
        new_module = ModuleNode(parent=self, tool=tool, enabled=enabled, uuid=uuid)
        self.nodes.append(new_module)
        return new_module

    def add_group(self, merge_mode: str, name: str = ""):
        new_node = GroupNode(
            parent=self, merge_mode=merge_mode, name=name if name else f"Group {len(self.nodes)}",
        )
        self.nodes.append(new_node)
        return new_node

    def remove_node(self, node: [int, object]):
        if isinstance(node, int):
            del self.nodes[node]
        elif isinstance(node, object):
            self.nodes.remove(node)

    def execute(self, **kwargs):
        pass

    def copy(self, parent):
        return GroupNode(
            parent=parent,
            merge_mode=self.merge_mode,
            name=self.name,
            nodes=[node.copy(parent=self) for node in self.nodes],
        )

    def to_code(self, indent: int):
        pass

    def to_json(self):
        return dict(
            node_type="group",
            merge_mode=self.merge_mode,
            name=self.name,
            nodes=[node.to_json() for node in self.nodes],
        )

    @classmethod
    def from_json(cls, parent, json_data: dict):
        return GroupNode(
            parent=parent,
            merge_mode=json_data["merge_mode"],
            name=json_data["name"],
            nodes=json_data["nodes"].from_json(),
        )

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


class LoosePipeline(object):
    def __init__(self, **kwargs):
        self.root: GroupNode = kwargs.get(
            "Root group", GroupNode(merge_mode=ipc.MERGE_MODE_CHAIN, name="root")
        )
        self.target_data_base = kwargs.get("target_data_base", None)
        self.settings = kwargs.get("settings", PipelineSettings())
        self.last_wrapper_luid = ""
        self.use_cache = kwargs.get("use_cache", True)
        self.image_output_path = kwargs.get("image_output_path", "")
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "Please insert description")

    def __repr__(self):
        return json.dumps(self.to_json(), indent=2, sort_keys=False)

    def __str__(self):
        return f"Pipeline {self.name}"

    def save(self, file_name: str) -> bool:
        pp_last_error.clear()
        try:
            with open(file_name, "w") as f:
                json.dump(self.to_json(), f, indent=2)
        except Exception as e:
            pp_last_error.add_error(
                new_error_text=f'Failed to save script generator "{repr(e)}"',
                new_error_kind="pipeline_save_error",
            )
            return False
        else:
            return True

    @classmethod
    def load(cls, file_name: str):
        with open(file_name, "r") as f:
            res = cls.from_json(json_data=json.load(f))

    def copy(self):
        lp = LoosePipeline(
            target_data_base=self.target_data_base.copy(),
            settings=self.settings.copy(),
            usecache=self.use_cache,
            image_output_path=self.image_output_path,
            name=self.name,
            description=self.description,
        )
        lp.root = self.root.copy()

    def add_group(self, merge_mode: str = ipc.MERGE_MODE_CHAIN, name: str = "") -> GroupNode:
        return self.root.add_group(merge_mode=merge_mode, name=name)

    def add_module(self, tool, enabled=1, uuid: str = "") -> ModuleNode:
        return self.root.add_module(tool=tool, enabled=enabled, uuid=uuid)

    def execute(self, **kwargs):
        pass

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
        save_dict["settings"] = self._settings.params_to_dict()
        # Add root node
        save_dict["root"] = self.root.to_json()
        return save_dict

    @classmethod
    def from_json(cls, json_data: dict):
        res = cls()
        if json_data["title"].lower() == "ipso phen pipeline v2":
            res.name = json_data["name"]
            res.description = json_data["description"]
            res.settings = PipelineSettings(**json_data["settings"])
            res.root = GroupNode.from_json(parent=res, json_data=json_data["root"])
        elif json_data["title"].lower() == "ipso phen pipeline":
            tmp = IptStrictPipeline.from_json(json_data=json_data)
            # Import basic data
            res.name = tmp.name
            # Import settings
            for setting in res.settings.gizmos:
                p = tmp.settings.find_by_name(setting.name)
                if p is not None:
                    setting.value = p.value
            # Import nodes & modules
            for k, v in tmp.group_tools(tool_only=False).items():
                current_group = res.add_group(merge_mode=MO_NONE, name=k,)
                for tool_dict in v:
                    current_group.add_module(
                        tool=tool_dict["tool"].copy(),
                        enabled=tool_dict["enabled"],
                        uuid=tool_dict["uuid"],
                    )

    @property
    def node_count(self):
        return len(self.root.nodes)
