import os
import logging
import json

import numpy as np

import tensorflow as tf
from tensorflow.keras.models import load_model

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.folders import ipso_folders
import ipso_phen.ipapi.base.ip_common as ipc


class IptTensorflowInference(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_text_input(
            name="model_name",
            desc="Model name without extension",
            default_value="",
            hint='All models should be located in "tensorflow_models" models folder',
        )
        self.add_text_input(
            name="variable_name", desc="CSV variable name", default_value="prediction"
        )

    def process_wrapper(self, **kwargs):
        """
        Tensorflow inference:
        'Use a Tensorflow model to predict value
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Model name without extension (model_name): All models should be located in "tensorflow_models" models folder
            * CSV variable name (variable_name):"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                with open(
                    os.path.join(
                        ipso_folders.get_path("tensorflow_models", force_creation=False),
                        f"{self.get_value_of('model_name')}_data.json",
                    ),
                    "r",
                ) as f:
                    model_data = json.load(f)

                model = load_model(
                    os.path.join(
                        ipso_folders.get_path("tensorflow_models", force_creation=False),
                        f"{self.get_value_of('model_name')}.h5",
                    ),
                    custom_objects=model_data["custom_objects"],
                )
                predictions = model.predict(
                    {
                        k: np.array([wrapper.csv_data_holder.data_list[k]])
                        for k in model_data["vars"]
                    }
                )
                self.add_value(
                    key=self.get_value_of("variable_name"),
                    value=predictions[0][0] * model_data["max_predicted_var"],
                    force_add=True,
                )

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Tensorflow inference FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Tensorflow inference"

    @property
    def package(self):
        return "Heliasen"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """'Use a Tensorflow model to predict value"""

    @property
    def skip_tests(self):
        return [ipc.TEST_IMG_IN_MSK_OUT]
