import os


def get_parent_dir(directory, depth=1):
    path = directory
    for i in range(0, depth):
        path = os.path.dirname(path)
    return path


def get_subdirs(directory, fullpath=False):
    '''
    Gets the folder in a folder. Not recursive.
    Only returns folder names by default.

    Parameters
        directory (path str) : The parent folder to get the children of
                               fullpath (bool).

        fullpath (bool) : Whether or not to return full folder paths.
                          Default value: False
    '''
    if fullpath:
        return [os.path.join(directory, dI).replace("\\", "/")
                for dI in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, dI))]
    else:
        return [dI.replace("\\", "/") for dI in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, dI))]
