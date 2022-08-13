import subprocess
import time
import src.leelazGoGUI
import estimator.estimator
import config
import re
import platform

alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L',
            'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
levle_table = ['20K', '15K', '11K', '7K', '5K', '3K', '1K',
               '1D', '3D', '5D', '7D', '9D', '11D', 'best-network', '對局']
platform_str = platform.system()
is_battle = False
escape_pharse = ''


def run_leelaz(level):
    global is_battle, escape_pharse
    leelaz_path = config.get_root_path() + "leela-zero-0.17/leelaz.exe"

    if platform_str == 'Windows':
        leelaz_path = config.get_root_path() + "leela-zero-0.17/leelaz.exe"
        escape_pharse = b'\r\n'
    elif platform_str == 'Darwin':
        leelaz_path = config.get_root_path() + "leela-zero-0.17/leelaz-mac"
        escape_pharse = b'\n'

    if not level in levle_table:
        return None

    if level == '對局':
        level = '20K'
        is_battle = True
    else:
        is_battle = False

    process = subprocess.Popen([leelaz_path, "--gtp", "--noponder", "-w", config.get_root_path() + 'leela-zero-0.17/' + level],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    stage = 0
    print('initialing...')
    while True:
        line = process.stdout.readline()
        if 'Setting max tree' in line.decode('ascii'):
            process.stdin.write(b'komi 6.5\n')
            process.stdin.flush()
            stage = 1
        elif '=' in line.decode('ascii') and stage == 1:
            process.stdin.write(b'boardsize 19\n')
            process.stdin.flush()
            stage = 2
        elif '=' in line.decode('ascii') and stage == 2:
            process.stdin.write(b'clear_board\n')
            process.stdin.flush()
            stage = 3
        elif '=' in line.decode('ascii') and stage == 3:
            print('leelaz activated.\n')
            return process


def clear_board(process):
    process.stdin.write(b'clear_board\n')
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if '=' in line.decode('ascii'):
            return True


def add_move(process, color, postion):
    command = 'play ' + color + ' ' + postion + '\n'
    print('play ' + color + ' ' + postion)
    process.stdin.write(command.encode())
    process.stdin.flush()
    start_reading = False
    result = False
    while True:
        line = process.stdout.readline()

        if escape_pharse == line and start_reading:
            return result
        else:
            result = line.decode('ascii')[::].rstrip()

            if '=' in line.decode('ascii'):
                start_reading = True
                result = True
            elif 'illegal move' in line.decode('ascii'):
                start_reading = True
                result = False


def think(process, think_time):
    command = 'lz-analyze\n'
    process.stdin.write(command.encode())
    process.stdin.flush()
    print('thinking...')
    time.sleep(think_time)
    process.stdin.write("\n".encode())
    process.stdin.flush()
    choose = []
    start_catch = False
    while True:
        line = process.stdout.readline()
        if '-> ' in line.decode('ascii'):
            start_catch = True
            output = line.decode('ascii')
            select_key = '([A-Z,a-z]{1,4}[0-1]?[0-9]?) -> .* \(V: (.*)%\) \(L'

            if len(re.search(select_key, output).groups()) > 0:
                position = re.search(select_key, output).groups()[0]
                wining_rate = re.search(select_key, output).groups()[1]

                pos_key = '([A-Z,a-z]{1,4})([0-1]?[0-9]?)'
                is_pass = False
                x_coord = -1
                y_coord = -1

                if re.search(pos_key, position).groups()[0].upper() == 'PASS':
                    is_pass = True
                else:
                    x_coord = str(
                        int(alphabet.index(re.search(pos_key, position).groups()[0].upper())+1))
                    y_coord = str(
                        int(re.search(pos_key, position).groups()[1]))
                    is_pass = False

                choose.append(
                    (position, wining_rate, x_coord, y_coord, is_pass))
        elif start_catch == True and 'visits,' in line.decode('ascii'):
            return choose


def estimate_score(process):
    boardstr = show_board(process)
    board_output_list = board_pharser(boardstr, 19)
    board = []

    index = 0
    while index < 19 * 19:
        board.append(0)
        index += 1

    for board_output in board_output_list:
        split = board_output.split(',')
        if split[0] == 'black':
            board[(19 - int(split[2])) * 19 + int(split[1])] = -1
        elif split[0] == 'white':
            board[(19 - int(split[2])) * 19 + int(split[1])] = 1

    sum, result = estimator.estimator.estimate(19, 19, board, -1, 200, 0.1)
    return sum, result


def show_board(process):
    command = 'showboard\n'
    print('showboard')
    process.stdin.write(command.encode())
    process.stdin.flush()
    boardstr = ''
    start_catch = False
    while True:
        line = process.stdout.readline()

        if 'White (O) Prisoners' in line.decode('ascii'):
            start_catch = True
        elif start_catch:
            if 'Hash:' in line.decode():
                boardstr += 'end'
                return boardstr[2::]
            else:
                boardstr = boardstr + line.decode()


def board_pharser(boardstr, size):
    result = []
    x_coord = 1
    y_coord = 1
    while x_coord <= size:
        while y_coord <= size:

            index = 0
            if platform_str == 'Windows':
                index = 1 + 2 * x_coord + \
                    (size * 2 + 5) * (size - y_coord + 1) + 2 * (size - y_coord)
            elif platform_str == 'Darwin':
                index = 42 + (2 * x_coord) + (44 * (19 - y_coord))

            if boardstr[index] == 'X':
                result.append('black,'+str(x_coord)+','+str(y_coord)+'')
            elif boardstr[index] == 'O':
                result.append('white,'+str(x_coord)+','+str(y_coord)+'')
            y_coord += 1
        x_coord += 1
        y_coord = 1
    return result


def score(process):
    command = 'final_score\n'
    process.stdin.write(command.encode())
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if '+' in line.decode():
            result = line.decode('ascii')[2::].rstrip()
            if result[0] == 'W':
                return 'White', float(result[2::])
            elif result[0] == 'B':
                return 'Black', float(result[2::])


def undo(process):
    command = 'undo\n'
    print('undo')
    process.stdin.write(command.encode())
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if '=' in line.decode('ascii'):
            return True
        elif 'cannot undo' in line.decode('ascii'):
            return False


def history(process):
    command = 'move_history\n'
    print('move_history')
    process.stdin.write(command.encode())
    process.stdin.flush()
    select_key = '([A-Z,a-z]{1,4})([0-1]?[0-9]?)'
    history_list = []
    start_reading = False
    while True:
        line = process.stdout.readline()

        if escape_pharse == line and start_reading:
            return history_list
        else:
            result = line.decode('ascii')[::].rstrip()

            if '=' in line.decode('ascii'):
                start_reading = True
                result = line.decode('ascii')[2::].rstrip()

            if 'white' in result:
                position = result.replace('white ', '')
                if re.search(select_key, position).groups()[0].upper() == "PASS":
                    history_list.append(('w', -1, -1))
                else:
                    x_coord = str(
                        int(alphabet.index(re.search(select_key, position).groups()[0].upper())+1))
                    y_coord = str(
                        int(re.search(select_key, position).groups()[1]))
                    history_list.append(('w', x_coord, y_coord))

            elif 'black' in result:
                position = result.replace('black ', '')
                if re.search(select_key, position).groups()[0].upper() == "PASS":
                    history_list.append(('b', -1, -1))
                else:
                    x_coord = str(
                        int(alphabet.index(re.search(select_key, position).groups()[0].upper())+1))
                    y_coord = str(
                        int(re.search(select_key, position).groups()[1]))
                    history_list.append(('b', x_coord, y_coord))


def show_board_GUI(process, show_text, recommand_positions, score_estimate):
    boardstr = show_board(process)
    board_output_list = board_pharser(boardstr, 19)
    history_list = history(process)
    return src.leelazGoGUI.create_image(19, 30, board_output_list, history_list, show_text, recommand_positions, score_estimate)
