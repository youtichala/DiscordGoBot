import estimator.broad
from estimator.color import Color
from enum import Enum
from estimator.vector import point
import random


class Result(Enum):
    OK = 0
    ILLEGAL = -1


global_visited = []
last_visited_counter = 0
do_ko_check = False
possible_ko = None

width = 0
height = 0
data = None


def estimate(_width, _height, _data, player_to_move, trials, tolerance):
    global width, height, data, global_visited
    width = _width
    height = _height
    data = _data

    index = 0
    while index < width * height:
        global_visited.append(0)
        index += 1

    estimator.broad.import_data(width, height)

    fill_false_eyes(get_false_eyes())

    seki_pass_iterations = trials
    seki_pass = rollout(seki_pass_iterations, player_to_move, False)

    seki = scan_for_seki(trials, 0.2, seki_pass)

    horseshoe_bias = []

    index = 0
    while index < height * width:
        horseshoe_bias.append(0)
        index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if data[y_coord * width + x_coord] == 0 and (is_safe_horseshoe(x_coord, y_coord, Color.BLACK.value) or is_safe_horseshoe(x_coord, y_coord, Color.WHITE.value)):
                neighbors = estimator.broad.get_neighbors(x_coord, y_coord)
                for neighbor in neighbors:
                    grs = try_group(neighbor)
                    for gr in grs:
                        horseshoe_bias[gr.y * width + gr.x] += 1
            x_coord += 1
        y_coord += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            horseshoe_bias[y_coord * width +
                           x_coord] *= data[y_coord * width + x_coord]

            horseshoe_bias[y_coord * width +
                           x_coord] *= int((trials * tolerance / 4))
            x_coord += 1
        y_coord += 1

    ret = []
    pass1 = []
    bias = []
    tolerance_scale = 1

    index = 0
    while index < height * width:
        ret.append(0)
        pass1.append(0)
        bias.append(0)
        index += 1

    territory_map = compute_territory()
    group_map = compute_group_map()
    liberty_map = compute_liberties()
    strong_life = compute_strong_life(group_map, territory_map)

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            bias[y_coord * width +
                 x_coord] += horseshoe_bias[y_coord * width + x_coord]
            x_coord += 1
        y_coord += 1

    pass1_iterations = trials
    pass1 = rollout(pass1_iterations, player_to_move,
                    True, strong_life, bias, seki)
 
    print("pass1")
    print_board(pass1) 
        
    dead = get_dead(pass1_iterations, tolerance, pass1)

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if pass1[y_coord * width + x_coord] > trials * tolerance:
                ret[y_coord * width + x_coord] = 1
            elif pass1[y_coord * width + x_coord] < trials * -tolerance:
                ret[y_coord * width + x_coord] = -1
            else:
                if data[y_coord * width + x_coord] != 0:
                    if abs(pass1[y_coord * width + x_coord]) < trials * tolerance / 3:
                        ret[y_coord * width + x_coord] = 0
                    else:
                        if pass1[y_coord * width + x_coord] > 0:
                            ret[y_coord * width + x_coord] = 1
                        else:
                            ret[y_coord * width + x_coord] = -1
                else:
                    ret[y_coord * width + x_coord] = 0
            x_coord += 1
        y_coord += 1

    print("adj")
    print_board(ret)
    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if ret[y_coord * width + x_coord] == 0:
                groups, neighbors = estimator.broad.group_neighbors(
                    data, point(x_coord, y_coord), [], [])

                if estimator.broad.all_not_equal_to(ret, neighbors, Color.WHITE.value):
                    for group in groups:
                        ret[group.y * width + group.x] = Color.BLACK.value

                elif estimator.broad.all_not_equal_to(ret, neighbors, Color.BLACK.value):
                    for group in groups:
                        ret[group.y * width + group.x] = Color.WHITE.value

            x_coord += 1
        y_coord += 1

    print("result")
    print_board(ret)
    return estimator.broad.sum(ret), ret


def get_dead(num_iterations, tolerance, rollout_pass):
    removed = []
    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if rollout_pass[y_coord * width + x_coord] > num_iterations * tolerance:
                if data[y_coord * width + x_coord] == -1:
                    removed.append(point(x_coord, y_coord))

            elif rollout_pass[y_coord * width + x_coord] < num_iterations * -tolerance:
                if data[y_coord * width + x_coord] == 1:
                    removed.append(point(x_coord, y_coord))
            else:
                if data[y_coord * width + x_coord] != 0:
                    removed.append(point(x_coord, y_coord))

            x_coord += 1
        y_coord += 1

    return removed


def get_false_eyes():
    false_eyes = []
    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:

            if data[y_coord * width + x_coord] == 0:
                neighbors = estimator.broad.get_neighbors(x_coord, y_coord)
                corners = estimator.broad.get_corners(x_coord, y_coord)

                if estimator.broad.get_min_liberties(data, x_coord, y_coord) > 1:
                    x_coord += 1
                    continue

                if estimator.broad.all_equal_to(data, neighbors, Color.BLACK.value) and (estimator.broad.count_equal(data, corners, Color.WHITE.value) >= (len(corners) >> 1)):
                    false_eyes.append(point(x_coord, y_coord))
                elif estimator.broad.all_equal_to(data, neighbors, Color.WHITE.value) and (estimator.broad.count_equal(data, corners, Color.BLACK.value) >= (len(corners) >> 1)):
                    false_eyes.append(point(x_coord, y_coord))

            x_coord += 1
        y_coord += 1

    return false_eyes


def fill_false_eyes(false_eyes):
    for eyes in false_eyes:
        neighbors = estimator.broad.get_neighbors(eyes.x, eyes.y)
        player_color = data[neighbors[0].y * width + neighbors[0].x]
        place_and_remove(eyes, player_color, [])


def rollout(num_iterations, player_to_move, pullup_life_based_on_neigboring_territory, life_map=[], bias=[], seki=[]):

    if len(life_map) == 0:
        index = 0
        while index < height * width:
            life_map.append(0)
            index += 1

    if len(bias) == 0:
        index = 0
        while index < height * width:
            bias.append(0)
            index += 1

    if len(seki) == 0:
        index = 0
        while index < height * width:
            seki.append(0)
            index += 1

    global data
    ret = bias

    index = 0
    catch_data = data.copy()
    while index < num_iterations:
        play_out_position(player_to_move, life_map, seki)
        x_coord = 0
        y_coord = 0
        while y_coord < height:
            x_coord = 0
            while x_coord < width:
                if data[y_coord * width + x_coord] == 0:
                    if is_territory(point(x_coord, y_coord), Color.BLACK.value):
                        fill_territory(point(x_coord, y_coord),
                                       Color.BLACK.value)
                    if is_territory(point(x_coord, y_coord), Color.WHITE.value):
                        fill_territory(point(x_coord, y_coord),
                                       Color.WHITE.value)

                x_coord += 1
            y_coord += 1

        x_coord = 0
        y_coord = 0
        while y_coord < height:
            x_coord = 0
            while x_coord < width:
                ret[y_coord * width + x_coord] += data[y_coord * width + x_coord]
                x_coord += 1
            y_coord += 1

        data = catch_data.copy()
        index += 1

    visited = []
    index = 0
    while index < width * height:
        visited.append(0)
        index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            test = point(x_coord, y_coord)

            if visited[y_coord * width + x_coord] == 0 and data[y_coord * width + x_coord] != 0:
                group = []
                neighbors = []
                group, neighbors = estimator.broad.group_neighbors(
                    data, test, group, neighbors)

                minmax = 0
                for item in group:
                    value = ret[item.y * width + item.x]
                    if abs(minmax) < abs(value):
                        minmax = value

                for item in group:
                    visited[item.y * width + item.x] = 1

                if pullup_life_based_on_neigboring_territory:
                    if minmax < 0:
                        for neighbor in neighbors:
                            if minmax > ret[neighbor.y * width + neighbor.x]:
                                minmax = ret[neighbor.y * width + neighbor.x]

                    if minmax > 0:
                        for neighbor in neighbors:
                            if minmax < ret[neighbor.y * width + neighbor.x]:
                                minmax = ret[neighbor.y * width + neighbor.x]

                for item in group:
                    ret[item.y * width + item.x] = minmax
            x_coord += 1
        y_coord += 1

    return ret


def scan_for_seki(trials, tolerance, rollout_pass):
    seki = []
    visited = []

    if len(seki) == 0:
        index = 0
        while index < height * width:
            seki.append(0)
            index += 1

    if len(visited) == 0:
        index = 0
        while index < height * width:
            visited.append(0)
            index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if visited[y_coord * width + x_coord] == 1:
                x_coord += 1
                continue

            group, neighbors = estimator.broad.group_neighbors(
                data, point(x_coord, y_coord), [], [])
            for cell in group:
                visited[cell.y * width + cell.x] = 1

            color = Color.WHITE.value
            addversary_color = color * -1

            if data[y_coord * width + x_coord] == color and estimator.broad.all_abs_lte(rollout_pass, group, trials * tolerance):
                neighboring = estimator.broad.match(data, neighbors, addversary_color)
                my_liberties = estimator.broad.count_equal(
                    data, neighbors, Color.EMPTY.value)

                if estimator.broad.all_abs_lte(rollout_pass, neighboring, trials * tolerance):
                    in_seki = True

                    for neighbor in neighboring:
                        if abs(rollout_pass[neighbor.y * width + neighbor.x]) < trials * tolerance:
                            neighbor_group, neighbor_neighbors = estimator.broad.group_neighbors(
                                data, neighbor, [], [])

                            neighbor_liberties = estimator.broad.count_equal(
                                data, neighbor_neighbors, Color.EMPTY.value)

                            if neighbor_liberties != my_liberties:
                                in_seki = False
                    if in_seki == True:
                        for cell in group:
                            seki[cell.y * width + cell.x] = 1
                        territory = estimator.broad.match(
                            data, neighbors, Color.EMPTY.value)
                        for cell in territory:
                            seki[cell.y * width + cell.x] = 1

            color = Color.BLACK.value
            addversary_color = color * -1

            if data[y_coord * width + x_coord] == color and estimator.broad.all_abs_lte(rollout_pass, group, trials * tolerance):
                neighboring = estimator.broad.match(data, neighbors, addversary_color)
                my_liberties = estimator.broad.count_equal(
                    data, neighbors, Color.EMPTY.value)

                if estimator.broad.all_abs_lte(rollout_pass, neighboring, trials * tolerance):
                    in_seki = True

                    for neighbor in neighboring:
                        if abs(rollout_pass[neighbor.y * width + neighbor.x]) < trials * tolerance:
                            neighbor_group, neighbor_neighbors = estimator.broad.group_neighbors(
                                data, neighbor, [], [])

                            neighbor_liberties = estimator.broad.count_equal(
                                data, neighbor_neighbors, Color.EMPTY.value)

                            if neighbor_liberties != my_liberties:
                                in_seki = False
                    if in_seki == True:
                        for cell in group:
                            seki[cell.y * width + cell.x] = 1
                        territory = estimator.broad.match(
                            data, neighbors, Color.EMPTY.value)
                        for cell in territory:
                            seki[cell.y * width + cell.x] = 1

            x_coord += 1
        y_coord += 1

    return seki


def is_safe_horseshoe(x, y, player):
    neighbors = estimator.broad.get_neighbors(x, y)

    if estimator.broad.count_equal(data, neighbors, player) >= len(neighbors) - 1 and estimator.broad.count_equal(data, neighbors, -player) == 0:
        corners = estimator.broad.get_corners(x, y)
        if estimator.broad.count_equal(data, corners, -player) >= len(corners) >> 1 and estimator.broad.get_min_liberties(data, x, y) <= 1:
            return False
        return True
    return False


def play_out_position(player_to_move, life_map, seki):
    global do_ko_check, possible_ko
    do_ko_check = 0
    possible_ko = point(-1, -1)

    possible_moves = []
    illegal_moves = []

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if data[y_coord * width + x_coord] == 0 and life_map[y_coord * width + x_coord] == 0 and seki[y_coord * width + x_coord] == 0:
                possible_moves.append(point(x_coord, y_coord))
            x_coord += 1
        y_coord += 1

    sanity = 1000
    passed = False
    while len(possible_moves) > 0 and sanity > 0:
        sanity -= 1
        move_idx = random.randint(0, len(possible_moves)-1)
        
        mv = possible_moves[move_idx]

        if is_eye(mv, player_to_move):
            illegal_moves.append(mv)
            possible_moves[move_idx] = possible_moves[len(possible_moves)-1]
            del possible_moves[len(possible_moves)-1]

            if len(possible_moves) == 0:
                if passed == True:
                    break

                passed = True
                possible_moves.extend(illegal_moves)
                illegal_moves = []
                player_to_move = -player_to_move
            continue

        result = place_and_remove(mv, player_to_move, possible_moves)
        if result == Result.OK:
            passed = False
            possible_moves[move_idx] = possible_moves[len(possible_moves)-1]
            del possible_moves[len(possible_moves)-1]
            player_to_move = -player_to_move
            possible_moves.extend(illegal_moves)
            illegal_moves = []
            continue
        elif result == Result.ILLEGAL:
            illegal_moves.append(mv)
            possible_moves[move_idx] = possible_moves[len(possible_moves)-1]
            del possible_moves[len(possible_moves)-1]

            if len(possible_moves) == 0:
                if passed == True:
                    break

                passed = True
                possible_moves.extend(illegal_moves)
                illegal_moves = []
                player_to_move = -player_to_move
            continue


def place_and_remove(move, player_color, possible_moves):
    global global_visited, last_visited_counter, do_ko_check, possible_ko

    if do_ko_check:
        if move == possible_ko:
            return Result.ILLEGAL

    reset_ko_check = True
    removed = False
    neighbors = estimator.broad.get_neighbors(move.x, move.y)
    data[move.y * width + move.x] = player_color
    last_visited_counter += 1

    for neighbor in neighbors:
        if data[neighbor.y * width + neighbor.x] == player_color * -1:
            if global_visited[neighbor.y * width + neighbor.x] != last_visited_counter and not has_liberties(neighbor):
                n_removed, possible_moves = remove_group(
                    neighbor, possible_moves)
                if n_removed == 1:
                    reset_ko_check = False
                    do_ko_check = True
                    possible_ko = neighbor
                removed = True

    if removed == False:
        if not has_liberties(move):
            data[move.y * width + move.x] = 0
            return Result.ILLEGAL

    if reset_ko_check:
        do_ko_check = False

    return Result.OK


def has_liberties(cell):
    global global_visited, last_visited_counter
    last_visited_counter += 1
    my_visited_counter = last_visited_counter
    tocheck = []
    tocheck.append(cell)
    global_visited[cell.y * width + cell.x] = my_visited_counter

    while len(tocheck) > 0:
        test = tocheck[len(tocheck)-1]
        del tocheck[len(tocheck)-1]

        if test.x > 0:
            neighbor = point(test.x-1, test.y)
            t_color = data[neighbor.y * width + neighbor.x]
            if t_color == 0:
                return True
            if t_color == data[cell.y * width + cell.x] and global_visited[neighbor.y * width + neighbor.x] != my_visited_counter:
                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)

        if test.x < width-1:
            neighbor = point(test.x+1, test.y)
            t_color = data[neighbor.y * width + neighbor.x]
            if t_color == 0:
                return True
            if t_color == data[cell.y * width + cell.x] and global_visited[neighbor.y * width + neighbor.x] != my_visited_counter:
                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)

        if test.y > 0:
            neighbor = point(test.x, test.y-1)
            t_color = data[neighbor.y * width + neighbor.x]
            if t_color == 0:
                return True
            if t_color == data[cell.y * width + cell.x] and global_visited[neighbor.y * width + neighbor.x] != my_visited_counter:
                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)

        if test.y < height-1:
            neighbor = point(test.x, test.y+1)
            t_color = data[neighbor.y * width + neighbor.x]
            if t_color == 0:
                return True
            if t_color == data[cell.y * width + cell.x] and global_visited[neighbor.y * width + neighbor.x] != my_visited_counter:
                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)

    return False


def try_group(point):
    tocheck = []
    visited = []
    ret = []
    color = data[point.y * width + point.x]

    index = 0
    while index < width * height:
        visited.append(0)
        index += 1

    tocheck.append(point)
    visited[point.y * width + point.x] = 1
    while len(tocheck) > 0:
        test = tocheck[0]
        tocheck[0] = tocheck[len(tocheck)-1]
        del tocheck[len(tocheck)-1]
        if data[test.y * width + test.x] == color:
            ret.append(test)
            neighbors = estimator.broad.get_neighbors(test.x, test.y)
            for neighbor in neighbors:
                if visited[neighbor.y * width + neighbor.x] == 1:
                    continue
                visited[neighbor.y * width + neighbor.x] = 1
                tocheck.append(neighbor)

    return ret


def remove_group(move, possible_moves):
    tocheck = []
    visited = []
    n_removed = 0
    color = data[move.y * width + move.x]
    index = 0
    while index < width * height:
        visited.append(0)
        index += 1

    tocheck.append(move)
    visited[move.y * width + move.x] = 1
    while len(tocheck) > 0:
        test = tocheck[0]
        del tocheck[0]
        tocheck = tocheck[::-1]
        data[test.y * width + test.x] = 0
        possible_moves.append(test)
        n_removed += 1

        neighbors = estimator.broad.get_neighbors(test.x, test.y)

        for neighbor in neighbors:

            if visited[neighbor.y * width + neighbor.x] == 1:
                continue
            visited[neighbor.y * width + neighbor.x] = 1
            if color == data[neighbor.y * width + neighbor.x]:
                tocheck.append(neighbor)

    return n_removed, possible_moves


def is_eye(cell, player):

    if cell.x == 0:
        pass
    elif data[cell.y * width + cell.x-1] == player:
        pass
    else:
        return False

    if cell.x == width-1:
        pass
    elif data[cell.y * width + cell.x+1] == player:
        pass
    else:
        return False

    if cell.y == 0:
        pass
    elif data[(cell.y-1) * width + cell.x] == player:
        pass
    else:
        return False

    if cell.y == height-1:
        pass
    elif data[(cell.y+1) * width + cell.x] == player:
        pass
    else:
        return False

    corners = estimator.broad.get_corners(cell.x, cell.y)

    if (estimator.broad.count_equal(data, corners, -player) >= len(corners) >> 1) and estimator.broad.get_min_liberties(data, cell.x, cell.y) <= 1:
        return False

    return True


def is_territory(cell, player):
    global global_visited, last_visited_counter
    last_visited_counter += 1
    my_visited_counter = last_visited_counter
    adjacent_player_stones = 0
    tocheck = []
    tocheck.append(cell)
    global_visited[cell.y * width + cell.x] = my_visited_counter

    while len(tocheck) > 0:
        test = tocheck[0]
        tocheck[0] = tocheck[len(tocheck)-1]
        del tocheck[len(tocheck)-1]

        if data[test.y * width + test.x] == 0:
            neighbors = estimator.broad.get_neighbors(test.x, test.y)

            for neighbor in neighbors:
                if global_visited[neighbor.y * width + neighbor.x] == my_visited_counter:
                    continue

                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)
        else:
            if data[test.y * width + test.x] != player:
                return False
            adjacent_player_stones += 1

    return adjacent_player_stones > 0


def fill_territory(cell, player):
    global global_visited, last_visited_counter
    last_visited_counter += 1
    my_visited_counter = last_visited_counter
    tocheck = []
    tocheck.append(cell)
    global_visited[cell.y * width + cell.x] = my_visited_counter

    while len(tocheck) > 0:
        test = tocheck[0]
        del tocheck[0]
        if data[test.y * width + test.x] == 0:
            data[test.y * width + test.x] = player
            neighbors = estimator.broad.get_neighbors(test.x, test.y)

            for neighbor in neighbors:
                if global_visited[neighbor.y * width + neighbor.x] == my_visited_counter:
                    continue

                global_visited[neighbor.y * width +
                               neighbor.x] = my_visited_counter
                tocheck.append(neighbor)


def compute_territory():
    ret = []

    index = 0
    while index < height * width:
        ret.append(0)
        index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:

            if(ret[y_coord * width + x_coord] == 1):
                x_coord += 1
                continue

            group = []
            neighbors = []

            if data[y_coord * width + x_coord] == 0 and is_territory(point(x_coord, y_coord), Color.BLACK.value):
                group, neighbors = estimator.broad.group_neighbors(
                    data, point(x_coord, y_coord), [], [])
                for cell in group:
                    ret[cell.y * width +
                        cell.x] = len(group) * Color.BLACK.value

            if data[y_coord * width + x_coord] == 0 and is_territory(point(x_coord, y_coord), Color.WHITE.value):
                group, neighbors = estimator.broad.group_neighbors(
                    data, point(x_coord, y_coord), group, neighbors)
                for cell in group:
                    ret[cell.y * width +
                        cell.x] = len(group) * Color.WHITE.value

            x_coord += 1
        y_coord += 1

    return ret


def compute_liberties():
    ret = []
    visited = []

    index = 0
    while index < height * width:
        visited.append(0)
        ret.append(0)
        index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if visited[y_coord * width + x_coord] == 1:
                x_coord += 1
                continue

            group, neighbors = estimator.broad.group_neighbors(
                data, point(x_coord, y_coord), [], [])
            for cell in group:
                visited[cell.y * width + cell.x] = 1

            liberty_count = 0

            if data[y_coord * width + x_coord] == 0:
                for neighbor in neighbors:
                    liberty_count += data[neighbor.y * width + neighbor.x]
            else:
                for neighbor in neighbors:
                    if data[neighbor.y * width + neighbor.x] == 0:
                        liberty_count += data[y_coord * width + x_coord]

            for cell in group:
                ret[cell.y * width + cell.x] = liberty_count

            x_coord += 1
        y_coord += 1

    return ret


def compute_strong_life(groups, territory):
    ret = []
    visited = []
    unified_territory_and_stones = []
    index = 0
    while index < height * width:
        unified_territory_and_stones.append(0)
        visited.append(0)
        ret.append(0)
        index += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if data[y_coord * width + x_coord] == 0:
                if territory[y_coord * width + x_coord] <= -1:
                    unified_territory_and_stones[y_coord *
                                                 width + x_coord] = -1
                else:
                    if territory[y_coord * width + x_coord] >= 1:
                        unified_territory_and_stones[y_coord *
                                                     width + x_coord] = 1
                    else:
                        unified_territory_and_stones[y_coord *
                                                     width + x_coord] = 0
            else:
                unified_territory_and_stones[y_coord * width +
                                             x_coord] = data[y_coord * width + x_coord]
            x_coord += 1
        y_coord += 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if visited[y_coord * width + x_coord] == 1:
                x_coord += 1
                continue

            groups, neighbors = estimator.broad.group_neighbors(
                unified_territory_and_stones, point(x_coord, y_coord), [], [])
            num_eyes = 0
            num_territory = 0
            for group in groups:
                if visited[group.y * width + group.x] == 1:
                    continue

                if territory[group.y * width + group.x] == 1:
                    territory_group, territory_neighbors = estimator.broad.group_neighbors(
                        data, group, [], [])

                    for territory_cell in territory_group:
                        visited[territory_cell.y *
                                width + territory_cell.x] = 1

                    num_eyes += 1
                    num_territory += len(territory_group)

            for group in groups:
                visited[group.y * width + group.x] = 1

            if num_eyes >= 2 or num_territory >= 5:
                for group in groups:
                    ret[group.y * width + group.x] = num_territory

            x_coord += 1
        y_coord += 1

    return ret


def compute_group_map():
    ret = []
    index = 0
    while index < height * width:
        ret.append(0)
        index += 1
    cur_group = 1

    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        while x_coord < width:
            if ret[y_coord * width + x_coord] == 0:
                ret = estimator.broad.trace_group(data, point(
                    x_coord, y_coord), ret, cur_group)
                cur_group += 1
            x_coord += 1
        y_coord += 1

    return ret


def print_board(table):
    x_coord = 0
    y_coord = 0
    while y_coord < height:
        x_coord = 0
        line = ''
        while x_coord < width:
            value = str(table[y_coord * width + x_coord])
            if len(value) == 1:
                value = '  ' + value
            if len(value) == 2:
                value = ' ' + value
            if len(value) == 3:
                value = value

            line += value + ' '
            x_coord += 1

        print(line)
        y_coord += 1
    print("")

