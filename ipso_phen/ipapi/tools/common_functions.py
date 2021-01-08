from timeit import default_timer as timer
import sys
import os
import subprocess
import platform
import re
import inspect
import pkgutil

import logging
from typing import Union

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

# Check PlantCV
try:
    from plantcv import plantcv as pcv
except Exception as e:
    allow_pcv = False
else:
    allow_pcv = True


# Functions
def format_time(seconds):
    """Transforms seconds in human readable time string

    Arguments:
        seconds {float} -- seconds to convert

    Returns:
        string -- seconds as human readable string
    """

    mg, sg = divmod(seconds, 60)
    hg, mg = divmod(mg, 60)
    return "{:02.0f}:{:02.0f}:{:02.3f}".format(hg, mg, sg)


class undefined_tqdm:
    def __init__(self, desc: str, lapse: float = 0.5, bar_length=10) -> None:
        self.desc = desc
        self.lapse = lapse
        self.calls_count = 0
        self.last_print = timer()
        self.first_call = None
        self.dot_pos = 0
        self.dot_dir = "right"
        self.bar_length = bar_length

    def step(self, force_print=False):
        if self.first_call is None:
            self.first_call = timer()

        self.calls_count += 1
        t = timer()
        if force_print or (t - self.last_print >= self.lapse):
            self.last_call = timer()
            desc = f"{self.desc}: "
            fill = (
                "".join("_" for _ in range(self.dot_pos))
                + ("|>" if self.dot_dir == "right" else "<|")
                + "".join("_" for _ in range(self.dot_pos + 1, self.bar_length))
            )
            if self.dot_dir == "right":
                self.dot_pos += 1
            else:
                self.dot_pos -= 1
            if self.dot_pos < 0:
                self.dot_dir = "right"
                self.dot_pos = 0
            elif self.dot_pos >= self.bar_length:
                self.dot_dir = "left"
                self.dot_pos = self.bar_length - 1
            res = f"{self.calls_count} iter, {self.calls_count / (self.last_call - self.first_call):.2f}/s"
            print(
                f"\r{desc} {fill} {res} - Total: {format_time(t - self.first_call)}",
                end="",
            )
            self.last_print = t

    def stop(self):
        self.step(force_print=True)
        print()


def print_progress_bar(iteration, total, prefix="", suffix="", bar_length=50, fill="#"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    if platform.system() == "Windows":
        percent = f"{iteration / float(total) * 100:.2f}"
        filled_length = int(bar_length * iteration // total)
        bar = fill * filled_length + " " * (bar_length - filled_length)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="")
        # Print New Line on Complete
        if iteration == total:
            print()
    else:
        str_format = "{0:." + str(2) + "f}"
        percents = str_format.format(100 * (iteration / float(total)))
        filled_length = int(round(bar_length * iteration / float(total)))
        bar = "=" * filled_length + "-" * (bar_length - filled_length)

        sys.stdout.write("\r%s |%s| %s%s %s" % (prefix, bar, percents, "%", suffix)),

        if iteration == total:
            # Print New Line on Complete
            sys.stdout.write("\n")
        sys.stdout.flush()


def open_file(filename: Union[tuple, str]) -> None:
    if isinstance(filename, tuple):
        filename = os.path.join(*filename)
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


def make_safe_name(text):
    ret = "".join(c if c not in '*"/\\[]:;|=,<>' else "_" for c in text)
    return ret.replace("'", "")


def force_directories(forced_path):
    if not os.path.exists(forced_path):
        os.makedirs(forced_path)


def _atoi(text_):
    return int(text_) if text_.isdigit() else text_


def natural_keys(text_):
    return [_atoi(c) for c in re.split(r"(\d+)", text_)]


def get_module_classes(
    package,
    class_inherits_from,
    remove_abstract: bool = True,
    exclude_if_contains: tuple = (),
):
    res = []
    if not allow_pcv:
        exclude_if_contains = exclude_if_contains + ("pcv",)
    for (module_loader, name, is_pkg) in pkgutil.iter_modules(package.__path__):
        try:
            exclude_module = False
            for exclusion_ in exclude_if_contains:
                if exclusion_ in name:
                    exclude_module = True
                    break
            if exclude_module:
                continue
            pkg_name = package.__name__ + "." + name
            pkg = __import__(pkg_name)
            module = sys.modules[pkg_name]
            for _, cls_ in inspect.getmembers(module):
                try:
                    if not inspect.isclass(cls_):
                        continue
                    if not issubclass(cls_, class_inherits_from):
                        continue
                    if remove_abstract and inspect.isabstract(cls_):
                        continue
                    res.append(cls_)
                except Exception as e:
                    print(f'Exception while handling {repr(cls_)} "{repr(e)}"')
        except Exception as e:
            logger.exception(f'Exception while parsing {repr(name)} "{repr(e)}"')

    # Create objects
    return list(set(res))


def add_header_footer(f):
    """Decorator: prints execution time with header and footer

    Arguments:
        f {function} -- function to decorate

    Returns:
        function -- created function
    """

    def new_function(*args, **kwargs):
        if (len(args) == 0) or not hasattr(args[0], "log_times") or args[0].log_times:
            print('______ Starting: "{}"'.format(str(args[0])))
            x = f(*args, **kwargs)
            print('______ Ended: "{}"'.format(str(args[0])))
            print("")
        else:
            x = f(*args, **kwargs)
        return x

    return new_function


def time_method(f):
    """Decorator: prints execution time

    Arguments:
        f {function} -- function to decorate

    Returns:
        function -- created function
    """

    def new_function(*args, **kwargs):
        before = timer()
        x = f(*args, **kwargs)
        after = timer()
        print('"{}" process time = {}'.format(f.__name__, format_time(after - before)))
        return x

    return new_function


# ____________________________________________________________
