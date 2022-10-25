import os
import random

from ipso_phen.ipapi.tools.common_functions import time_method
from ipso_phen.ipapi.base.image_wrapper import ImageWrapper

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class ImageList:
    def __init__(self, extensions):
        self._folders_paths = []
        self._extensions = extensions
        self.log_times = True

    def add_folder(self, folder_path):
        """Add source folder to folder list

        Arguments:
            folder_path {str} -- path of the folder to add
        """

        if os.path.isdir(folder_path):
            self._folders_paths.append(folder_path)

    def add_folders(self, folder_list):
        """Adds a list of folders as inputs

        Arguments:
            folder_list {list} -- list of source folders
        """

        for fld in folder_list:
            self.add_folder(fld)

    def _demux_commands(self, cmds):
        flts_ = []
        post_flts_ = []
        pick_ = 0
        grps_ = []
        acts_ = []
        exclusions_ = []
        forced_ = []
        cut_at_date_ = []

        if cmds:
            for cmd in cmds:
                if cmd["action"].lower() == "filter":
                    flts_.append(self._clean_mask(cmd["data"]))
                elif cmd["action"].lower() == "group":
                    grps_.append(cmd["data"])
                elif cmd["action"].lower() == "modify":
                    acts_.append(cmd["data"])
                elif cmd["action"].lower() == "post_filter":
                    post_flts_.append(self._clean_mask(cmd["data"]))
                elif cmd["action"].lower() == "decimate":
                    logger.info("Decimate command no longer supported")
                elif cmd["action"].lower() == "pick_random":
                    pick_ = cmd["data"]
                if cmd["action"].lower() == "exclude":
                    exclusions_.append(self._clean_mask(cmd["data"]))
                if cmd["action"].lower() == "force":
                    forced_.append(self._clean_mask(cmd["data"]))
                if cmd["action"].lower() == "cut_at_date":
                    cut_at_date_ = cmd["data"]

        return (
            flts_,
            post_flts_,
            grps_,
            acts_,
            pick_,
            exclusions_,
            forced_,
            cut_at_date_,
        )

    @staticmethod
    def _clean_mask(mask):
        """Cleans the mask

        Arguments:
            mask {dictionnary} -- the mask

        Returns:
            dictionnary -- entry mask with no jokers and fully lowercased
        """

        # Remove jokers
        to_del = []
        for key, value in mask.items():
            if "*" in value:
                to_del.append(key)
        if to_del:
            for to_del_key in to_del:
                del mask[to_del_key]

        # Lowercase everything
        return dict((k.lower(), [i.lower() for i in v]) for k, v in mask.items())

    @staticmethod
    def _is_file_matches_mask(filename, mask):
        """Tests if file name matches the mask
        and checks the override tag

        Arguments:
            filename {string} -- file name
            mask {dictionnary} -- convoluted mask

        Returns:
            boolean -- does the file match the mask
            str -- fail reason (for debug purposes)
        """

        # mask = self.__clean_mask(mask)

        if not mask:
            return True, "none"

        img_w = ImageWrapper(filename)

        for key, value in mask.items():
            if not img_w.matches(key, value):
                return False, key

        return True, "none"

    @time_method
    def _filter_extensions(self):
        """
        Filter accepted extension, WARNING folder parse is recursive
        """
        file_list = [
            os.path.join(root, name)
            for fld in self._folders_paths
            for root, _, files in os.walk(fld)
            for name in files
            if name.lower().endswith(self.extensions)
        ]
        logger.info(f"Extension filtering file count: {len(file_list)}")
        return file_list

    @staticmethod
    def match_end(target_path: str, file_end: str):
        """
        Filter accepted extension, WARNING folder parse is recursive
        """
        file_list = [
            os.path.join(root, name)
            for root, _, files in os.walk(target_path)
            for name in files
            if name.lower().endswith(file_end)
        ]
        return file_list

    @time_method
    def _cut_at_date(self, file_list, cut_date):
        year_, month_, day_ = cut_date["year"], cut_date["month"], cut_date["day"]
        i = 0
        while i < len(file_list):
            img_w = ImageWrapper(file_list[i])
            if img_w.is_after_date(year_, month_, day_):
                del file_list[i]
            else:
                i += 1

        return file_list

    @time_method
    def _apply_filters(self, file_list, filters, exclusions):
        i = 0
        while i < len(file_list):
            # Test exclusions
            is_rejected_ = False
            for mask in exclusions:
                is_rejected_, _ = self._is_file_matches_mask(file_list[i], mask)
                if is_rejected_:
                    break
            if is_rejected_:
                del file_list[i]
                continue
            if (file_list is not None) and filters:
                for mask in filters:
                    is_accepted_, _ = self._is_file_matches_mask(file_list[i], mask)
                    if is_accepted_:
                        break
                else:
                    is_accepted_ = True
                if is_accepted_:
                    i += 1
                else:
                    del file_list[i]
            else:
                i += 1
        logger.info(f"Comand filtering file count: {len(file_list)}")

        return file_list

    @time_method
    def _apply_post_filter(self, file_list, post_filter):
        i = 0
        while i < len(file_list):
            is_accepted_ = False
            for mask in post_filter:
                is_accepted_, _ = self._is_file_matches_mask(file_list[i], mask)
                if is_accepted_:
                    break
            if is_accepted_:
                i += 1
            else:
                del file_list[i]
        logger.info(f"Post filtering file count: {len(file_list)}")

        return file_list

    @time_method
    def _pick(self, file_list, pick):
        random.shuffle(file_list)
        return sorted(file_list[:pick])

    @time_method
    def _apply_actions(self, file_list, actions, groups, flatten):
        if len(actions) > 1:
            raise ValueError("Only one action command allowed")
        if len(actions) != 1:
            raise ValueError("Actions are only allowed on grouped lists")
        tmp_lst = []
        if "plant" in groups[0]:
            main_key = "plant"
        elif "exp" in groups[0]:
            main_key = "exp"
        else:
            raise NotImplementedError
        if actions[0] == "keep_lasts":
            parsed_names = []
            while True:
                # Find a new root item
                current_sub_key = ""
                best_group = ""
                best_date = ""
                for item in file_list:
                    if not item["key"][main_key] in parsed_names:
                        current_sub_key = item["key"][main_key]
                        parsed_names.append(current_sub_key)
                        best_date = item["wrappers"][0].date
                        best_group = item
                        break
                if not (current_sub_key and best_group and best_date):
                    break

                # find the latest entry for the sub key
                for item in file_list:
                    if (
                        item["key"][main_key] == current_sub_key
                        and item["wrappers"][0].date > best_date
                    ):
                        best_date = item["wrappers"][0].date
                        best_group = item

                # Append result
                if flatten:
                    for wrapper in best_group["wrappers"]:
                        tmp_lst.append(wrapper.file_path)
                else:
                    tmp_lst.append(best_group)

            return tmp_lst
        else:
            raise NotImplementedError

    def filter_db(self, input_list, masks, flat_list_out=True):
        """
        Returns a list containing only the files matching to the mask

        Arguments:
            input_list {list} -- list containing all the candidate files
            mask {dictionary} -- filtering mask
            flat_list_out {boolean} -- return flat list or list of dictionaries (only when group and actions are present)

        Returns:
            list -- file list
        """
        result = input_list[:]

        (
            filters_,
            post_filters_,
            groups_,
            actions_,
            pick_,
            exclusions_,
            forced_,
            cut_at_date_,
        ) = self._demux_commands(masks)

        # Filter
        if result and (filters_ or exclusions_):
            result = self._apply_filters(result, filters_, exclusions_)

        # Post Filter
        if result and post_filters_:
            result = self._apply_post_filter(result, post_filters_)

        # Decimate
        if result and pick_ > 0:
            result = self._pick(result, pick_)

        # Force some
        if forced_:
            result = result + self._apply_filters(input_list[:], forced_, [])

        # Remove all files after date
        if cut_at_date_:
            result = self._cut_at_date(result, cut_at_date_)

        # Group
        if result and groups_:
            if len(groups_) > 1:
                raise ValueError("Only one group command allowed")
            result = self._group_by_filter(result, groups_[0])
            if result and not actions_:
                if flat_list_out:
                    tmp_lst = [fw.file_path for item in result for fw in item["wrappers"]]
                else:
                    tmp_lst = [
                        dict(
                            {
                                "key": item["key"]["plant"],
                                "files": [fw.file_path for fw in item["wrappers"]],
                            }
                        )
                        for item in result
                    ]
                return tmp_lst

        # Action
        if result and actions_ and groups_:
            result = self._apply_actions(result, actions_, groups_, flat_list_out)

        return result

    def filter(self, masks, flat_list_out=True):
        """Returns a list containing only the files matching to the mask

        Arguments:
            mask {dictionary} -- filtering mask
            flat_list_out {boolean} -- return flat list or list of dictionaries (only when group and actions are present)

        Returns:
            list -- file list
        """

        if not self._folders_paths:
            return []
        else:
            result = self._filter_extensions()

            (
                filters_,
                post_filters_,
                groups_,
                actions_,
                pick_,
                exclusions_,
                _,
                _,
            ) = self._demux_commands(masks)

            # Filter
            if result and filters_:
                result = self._apply_filters(result, filters_, exclusions_)

            # Post Filter
            if result and post_filters_:
                result = self._apply_post_filter(result, post_filters_)

            # Decimate
            if result and pick_ > 0:
                result = self._pick(result, pick_)

            # Group
            if result and groups_:
                if len(groups_) > 1:
                    raise ValueError("Only one group command allowed")
                result = self._group_by_filter(result, groups_[0])
                if result and not actions_:
                    if flat_list_out:
                        tmp_lst = [
                            fw.file_path for item in result for fw in item["wrappers"]
                        ]
                    else:
                        tmp_lst = [
                            dict(
                                {
                                    "key": item["key"]["plant"],
                                    "files": [fw.file_path for fw in item["wrappers"]],
                                }
                            )
                            for item in result
                        ]
                    return tmp_lst

            # Action
            if result and actions_ and groups_:
                result = self._apply_actions(result, actions_, groups_, flat_list_out)

        return result

    @time_method
    def _group_by_filter(self, file_list, keys):
        """Group elements in file list by unique key

        Arguments:
            file_list {list} -- input files
            keys {list} -- key for grouping

        Returns:
            dictionnary -- dictionnary containing lists of files grouped by unique key
        """

        result = []
        if file_list:

            def build_key(image, key_list):
                return dict((key, image.value_of(key)) for key in key_list)

            img_lst = [ImageWrapper(fl) for fl in file_list]
            img = img_lst[0]
            cur_dict = {"key": build_key(img, keys), "wrappers": [img]}
            result.append(cur_dict)
            for img in img_lst[1:]:
                cur_key = build_key(img, keys)
                if cur_key == cur_dict["key"]:
                    cur_dict["wrappers"].append(img)
                else:
                    found_dic = False
                    for dico in result:
                        if dico["key"] == cur_key:
                            cur_dict = dico
                            found_dic = True
                            break
                    if not found_dic:
                        cur_dict = {"key": build_key(img, keys), "wrappers": [img]}
                        result.append(cur_dict)
                    else:
                        cur_dict["wrappers"].append(img)

        return result

    # Properties
    def _get_extensions(self):
        return self._extensions

    def _set_extensions(self, value):
        self._extensions = value

    extensions = property(_get_extensions, _set_extensions)
