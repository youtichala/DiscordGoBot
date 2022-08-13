import platform

root_path = ''
prefix = '!'

platform_str = platform.system()

def setup_path():
    global root_path
    if platform_str == 'Windows' :
        root_path = 'D:/Project/Python/DiscordGoBot-Chess/'
    elif platform_str == 'Darwin' :
        root_path = '/Users/user_name/DiscordGoBot-Chess/'
    elif platform_str == 'Linux' :
        root_path = '~/DiscordGoBot-Chess/'
    else :
        root_path = 'not_support_path'


def get_root_path():
    if root_path == '' :
        setup_path()

    return root_path