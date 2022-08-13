from estimator.vector import point

width = 0
height = 0


def import_data(_width, _height):
    global width, height

    width = _width
    height = _height


def sum(data):
    score = 0
    for value in data:
        score += value
    return score


def get_neighbors(x, y):
    neighbors = []
    if x > 0:
        neighbors.append(point(x-1, y))
    if x < width - 1:
        neighbors.append(point(x+1, y))
    if y > 0:
        neighbors.append(point(x, y-1))
    if y < height - 1:
        neighbors.append(point(x, y+1))

    return neighbors


def get_corners(x, y):
    corners = []
    if y > 0 and x > 0:
        corners.append(point(x-1, y-1))

    if y > 0 and x < width - 1:
        corners.append(point(x+1, y-1))

    if y < height - 1 and x > 0:
        corners.append(point(x-1, y+1))

    if y < height - 1 and x < width - 1:
        corners.append(point(x+1, y+1))

    return corners


def get_min_liberties(data, x, y):

    neighbors = get_neighbors(x, y)

    ret = 99999
    index = 0
    group = []
    out_neighbors = []
    while index < len(neighbors):

        group, out_neighbors = group_neighbors(
            data, neighbors[index], [], [])

        liberties = count_equal(data, out_neighbors, 0)
        if ret >= liberties:
            ret = liberties

        index += 1
    return ret


def trace_group(data, start_point, destination, value):
    tocheck = []
    visited = []

    index = 0
    while index < width * height:
        visited.append(0)
        index += 1

    matching_value = data[start_point.y * width + start_point.x]
    tocheck.append(start_point)
    visited[start_point.y * width + start_point.x] = 1

    while(len(tocheck) > 0):
        test_value = tocheck[0]
        tocheck.remove(test_value)

        if data[test_value.y * width + test_value.x] == matching_value:
            destination[test_value.y * width + test_value.x] = value
            neighbors = get_neighbors(test_value.x, test_value.y)
            for neighbor in neighbors:
                if visited[neighbor.y * width + neighbor.x] == 1:
                    continue
                visited[neighbor.y * width + neighbor.x] = 1
                tocheck.append(neighbor)
    return destination



def group_neighbors(data, start_point, group, out_neighbors):
    matching_value = data[start_point.y * width + start_point.x]
    tocheck = []
    visited = []

    index = 0
    while index < width * height:
        visited.append(0)
        index += 1

    visited[start_point.y * width + start_point.x] = 1
    tocheck.append(start_point)

    while(len(tocheck) > 0):

        test_value = tocheck[0]
        tocheck.remove(test_value)
        if tocheck == None:
            tocheck = []

        if data[test_value.y * width + test_value.x] == matching_value:
            group.append(test_value)
            test_neighbors = get_neighbors(test_value.x, test_value.y)
            for test_neighbor in test_neighbors:

                if visited[test_neighbor.y * width + test_neighbor.x] == 1:
                    continue
                visited[test_neighbor.y * width + test_neighbor.x] = 1

                tocheck.append(test_neighbor)
        else:
            out_neighbors.append(test_value)

    return group, out_neighbors


def count_equal(data, neighbors, value):
    ret = 0
    for neighbor in neighbors:
        if data[neighbor.y * width + neighbor.x] == value:
            ret += 1

    return ret


def all_equal_to(data, group, value):
    for cell in group:
        if data[cell.y * width + cell.x] != value:
            return False
    return True


def all_not_equal_to(data, group, value):
    for cell in group:
        if data[cell.y * width + cell.x] == value:
            return False
    return True


def all_abs_lte(rollout_pass, group, value):
    for cell in group:
        if abs(rollout_pass[cell.y * width + cell.x]) > value:
            return False
    return True


def match(rollout_pass, group, value):
    result = []
    for cell in group:
        if rollout_pass[cell.y * width + cell.x] == value:
            result.append(cell)
    return result
