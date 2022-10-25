from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor


class TpmpImageProcessorBlueScreenTest(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionnary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["demo_blue"]
