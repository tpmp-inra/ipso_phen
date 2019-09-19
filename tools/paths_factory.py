import os


def get_folders_paths(dst_seed='', output_kind='pictures'):
    """Returns destination folders according to ouput_kind

    Keyword Arguments:
        dst_seed {str} -- folder appended at the end of dst (default: {=''})

    Returns:
        str -- destination folder
    """    

    if os.path.isabs(dst_seed):
        return dst_seed
    else:
        user_folder = os.path.join(os.path.expanduser('~'), '')
        if output_kind.lower() == 'pictures':
            _sub_folder = 'Pictures'
        elif output_kind.lower() == 'videos':
            _sub_folder = 'Videos'
        else:
            _sub_folder = 'Documents'

        return os.path.join(user_folder, _sub_folder, 'ipso_phen_output', dst_seed, '')
