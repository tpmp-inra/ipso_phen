import os
import platform


def get_folders_paths(src_seed='', dst_seed='', output_kind='pictures'):
    """Returns source and destination folders according to platform

    Keyword Arguments:
        src_seed {str} -- folder appended at the end of src (default: {''})
        dst_seed {str} -- folder appended at the end of dst (default: {=''})

    Returns:
        str, str -- source and destination folders
    """

    src_path, dst_path = '', ''

    plat_sys = platform.system()
    if plat_sys == 'Windows':
        user_folder = os.path.join(os.path.expanduser('~'), '')

        if os.path.isabs(src_seed):
            src_path = src_seed
        else:
            src_path = os.path.join(user_folder, 'Pictures', 'TPMP_input')
            src_path = src_path + src_seed

        if os.path.isabs(dst_seed):
            dst_path = src_seed
        else:
            if output_kind.lower() == 'pictures':
                _sub_folder = 'Pictures'
            elif output_kind.lower() == 'videos':
                _sub_folder = 'Videos'
            else:
                _sub_folder = 'Documents'
            dst_path = os.path.join(user_folder, _sub_folder, 'TPMP_output', dst_seed, '')
    elif plat_sys == 'Linux':
        src_path = os.path.join('home', 'users', 'SRV_TPMP', 'fmavianemac', 'data', 'TPMP_input', 'src_seed', '')
        dst_path = os.path.join('home', 'users', 'SRV_TPMP', 'fmavianemac', 'data', 'TPMP_output', 'dst_seed', '')

    return src_path, dst_path
