class AbstractCsvWriter:
    def __init__(self):
        self.data_list = {}

    def clear(self):
        self.data_list = {}

    def clean_data(self):
        self.data_list = {k: v for k, v in self.data_list.items() if v is not None}

    def header_to_list(self):
        return [key.replace("-", "_") for key in self.data_list.keys()]

    def data_to_list(self):
        return [
            v.replace(",", " ") if isinstance(v, str) else v
            for v in self.data_list.values()
        ]

    def has_csv_key(self, key):
        return key in self.data_list.keys()

    def update_csv_value(self, key, value, force_pair=False):
        if force_pair or self.has_csv_key(key):
            self.data_list[key] = value

    def retrieve_csv_value(self, key):
        if key in self.data_list:
            return self.data_list[key]
        else:
            return None

    def fill_values(self, value="na"):
        for k, v in self.data_list.items():
            if not v:
                self.update_csv_value(k, value)

    def update_csv_dimensions(self, img, scale_width):
        self.update_csv_value("image_width", img.shape[1])
        self.update_csv_value("image_height", img.shape[0])
        if "scale_width" in self.data_list.keys():
            if scale_width == 1:
                self.update_csv_value(
                    "scale_width",
                    self.data_list["image_width"],
                )
            else:
                self.update_csv_value("scale_width", scale_width)
