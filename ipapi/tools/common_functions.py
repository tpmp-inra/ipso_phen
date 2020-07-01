from timeit import default_timer as timer
import sys
import os
import subprocess
import platform
import re
import inspect
import pkgutil

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


def open_file(filename: [tuple, str]) -> None:
    if isinstance(filename, tuple):
        filename = os.path.join(*filename)
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


def make_safe_name(text):
    ret = "".join(c if c not in '*"/\[]:;|=,<>' else "_" for c in text)
    return ret.replace("'", "")


def force_directories(forced_path):
    if not os.path.exists(forced_path):
        os.makedirs(forced_path)


def _atoi(text_):
    return int(text_) if text_.isdigit() else text_


def natural_keys(text_):
    return [_atoi(c) for c in re.split(r"(\d+)", text_)]


def get_module_classes(
    package, class_inherits_from, remove_abstract: bool = True, exclude_if_contains: tuple = ()
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
            print(f'Exception while handling {repr(cls_)} "{repr(e)}"')

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
        if (len(args) == 0) or not hasattr(args[0], "log_times") or args[0].log_times:
            before = timer()
            x = f(*args, **kwargs)
            after = timer()
            print('"{}" process time = {}'.format(f.__name__, format_time(after - before)))
        else:
            x = f(*args, **kwargs)
        return x

    return new_function


def forced_time_method(f):
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
        print(
            f'"{type(args[0]).__name__}.{f.__name__}" process time: {format_time(after - before)}'
        )
        return x

    return new_function


# ____________________________________________________________
