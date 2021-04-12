def compute_euclidean_distance(point, rect):

    def point_dist(pt):
        return ((point[0] - pt[0]) ** 2) + ((point[1] - pt[1]) ** 2)

    def zona_point(zona):
        x1, y1, x2, y2 = zona
        x, y = point

        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        if y1 == y2:
            if x >= x1 and x <= x2:
                return abs(y - y1)
            else:
                return min(point_dist((x1, y1)), point_dist((x2, y2)))
        elif x1 == x2:
            if y >= y1 and y <= y2:
                return abs(x - x1)
            else:
                return min(point_dist((x1, y1)), point_dist((x2, y2)))

        raise ValueError("CAN rectangle error")


    x1, y1, x2, y2 = rect
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    if x1 <= point[0] and point[0] <= x2 and y1 <= point[1] and point[1] <= y2:
        return 0

    return min(zona_point((x1, y1, x1, y2)), zona_point((x1, y2, x2, y2)),
               zona_point((x2, y2, x2, y1)), zona_point((x2, y1, x1, y1)))

    def compute_distance(point, zone):
        dist = 2.0
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                dist = min(dist, compute_euclidean_distance((point[0] + i, point[1] + j), zone))
        return dist

    def find_center(zona):
        return (zona[0] + zona[2]) / 2, (zona[1] + zona[3]) / 2