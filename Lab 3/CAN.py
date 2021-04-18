import numpy as np
import random
import math
import cv2
import time
from queue import Queue


def euclidean_distance(point, zona):
    def distance(pt):
        return (math.sqrt((point[0] - pt[0]) ** 2) + ((point[1] - pt[1]) ** 2))

    def isRect(rect):
        x1, y1, x2, y2 = rect
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        rect1 = (x1, y1, x2, y2)
        return rect1

    def ditance_to_border(zona):
        x1, y1, x2, y2 = isRect(zona)
        x, y = point

        return min(distance((x1, y1)), distance((x2, y2)))
        if y1 == y2:
            if x >= x1 and x <= x2:
                return abs(y - y1)
            else:
                return min(distance((x1, y1)), distance((x2, y2)))
        elif x1 == x2:
            if y >= y1 and y <= y2:
                return abs(x - x1)
            else:
                return min(distance((x1, y1)), distance((x2, y2)))

        raise ValueError("CAN error")


    x1, y1, x2, y2 = isRect(zona)

    if x1 <= point[0] and point[0] <= x2 and y1 <= point[1] and point[1] <= y2:
        return 0

    return min(ditance_to_border((x1, y1, x1, y2)), ditance_to_border((x1, y2, x2, y2)),
               ditance_to_border((x2, y2, x2, y1)), ditance_to_border((x2, y1, x1, y1)))


def get_distance(point, rect):
    distance = 2.0
    for horizontal in [-1, 0, 1]:
        for vertical in [-1, 0, 1]:
            distance = min(distance,
                           euclidean_distance((point[0] + horizontal, point[1] + vertical), rect))
    return distance


def get_center(zona):
    return (zona[0] + zona[2]) / 2, (zona[1] + zona[3]) / 2

def stats_report(stats):
    stats['num_neighbors'] = np.array(stats['num_neighbors'])
    stats['path_length'] = np.array(stats['path_length'])
    stats['num_routes'] = np.array(stats['num_routes'])
    return {'num_neighbors': (stats['num_neighbors'].min(), stats['num_neighbors'].mean(), stats['num_neighbors'].max()),
           'path_length': (stats['path_length'].min(), stats['path_length'].mean(), stats['path_length'].max()),
           'num_routes': (stats['num_routes'].min(axis=1), stats['num_routes'].mean(axis=1), stats['num_routes'].max(axis=1))}

class Route():
    def __init__(self, sender_node, point, data, status="started"):
        self.sender = get_center(sender_node.zona)
        self.node = sender_node
        self.point = point
        self.data = data
        self.status = status
        self.num_steps = 0

class Peer():
    def __init__(self, name, zona):
        self.name = name
        self.zona = zona
        self.zone_neighbors = dict()
        self.new_route = []
        self.routes = Queue()

    def add_neighbor(self, neighbor):
        self.zone_neighbors[neighbor.name] = neighbor

    def remove_neighbor(self, neighbor_name):
        self.zone_neighbors.pop(neighbor_name)

    def add_route(self, route):
        route.node = self
        self.new_route.append(route)

    def finish_route(self, route):
        route.status = "finished"

    def send_action(self, route):
        min_distance = 2.0
        best_neighbor = None
        route.num_steps += 1

        for key in self.zone_neighbors.keys():
            current_distance = get_distance(route.point, self.zone_neighbors[key].zona)
            if current_distance < min_distance:
                min_distance = current_distance
                best_neighbor = self.zone_neighbors[key]

        if best_neighbor is None:
            route.status = "error"
        else:
            best_neighbor.add_route(route)

    def move(self):
        if not self.routes.empty():
            route = self.routes.get()
            if get_distance(route.point, self.zona) > 0:
                self.send_action(route)
            else:
                self.finish_route(route)

    def update(self):
        for route in self.new_route:
            self.routes.put(route)
        self.new_route = []


class CAN():
        def __init__(self, num_peers):
            self.num_peers = num_peers
            self.nodes = []
            self.s = []
            self.routing = []
            self.action_colors = {'started': (0, 255, 0), 'finished': (255, 0, ), 'error': (255, 0, 0)}

        def add_node(self, node_id):

            def split_zona(zona):
                if zona[2] - zona[0] == zona[3] - zona[1]:
                    return (zona[0], zona[1], zona[0] + (zona[2] - zona[0]) / 2, zona[3]), (
                        zona[0] + (zona[2] - zona[0]) / 2, zona[1], zona[2], zona[3])
                else:
                    return (zona[0], zona[1], zona[2], zona[1] + (zona[3] - zona[1]) / 2), (
                        zona[0], zona[1] + (zona[3] - zona[1]) / 2, zona[2], zona[3])

            def zona_neighbor(zona1, zona2):

                def check_one(zona1, zona2):
                    x1, y1, x2, y2 = zona1

                    is_neighbor = False
                    is_neighbor = is_neighbor or (get_distance((x1, y1), zona2) == 0 and get_distance((x1, y2), zona2) == 0)
                    is_neighbor = is_neighbor or (get_distance((x1, y2), zona2) == 0 and get_distance((x2, y2), zona2) == 0)
                    is_neighbor = is_neighbor or (get_distance((x2, y1), zona2) == 0 and get_distance((x1, y1), zona2) == 0)
                    is_neighbor = is_neighbor or (get_distance((x2, y2), zona2) == 0 and get_distance((x2, y1), zona2) == 0)

                    return is_neighbor and zona1 != zona2

                return check_one(zona1, zona2) or check_one(zona2, zona1)

            zona1, zona2 = split_zona(self.nodes[node_id].zona)
            self.nodes[node_id].zona = zona1

            zone_neighbors = self.nodes[node_id].zone_neighbors
            self.nodes.append(Peer(len(self.nodes), zona2))

            for key in list(zone_neighbors.keys()):
                if zona_neighbor(zona2, zone_neighbors[key].zona):
                    self.nodes[-1].add_neighbor(zone_neighbors[key])
                    zone_neighbors[key].add_neighbor(self.nodes[-1])
                if not zona_neighbor(zona1, zone_neighbors[key].zona):
                    zone_neighbors[key].remove_neighbor(self.nodes[node_id].name)
                    self.nodes[node_id].remove_neighbor(key)

            self.nodes[node_id].add_neighbor(self.nodes[-1])
            self.nodes[-1].add_neighbor(self.nodes[node_id])

        def generate(self):
            random.seed(42)
            self.nodes = []
            self.nodes.append(Peer(0, (0.0, 0.0, 1.0, 1.0)))
            self.s.append(1)
            for i in range(self.num_peers - 1):
                node_id = random.choices(range(len(self.nodes)), self.s)[0]
                self.add_node(node_id)
                space = (self.nodes[node_id].zona[3] - self.nodes[node_id].zona[1]) * (
                            self.nodes[node_id].zona[2] - self.nodes[node_id].zona[0])
                self.s.append(space)
                self.s[node_id] = space

        def generate_route(self, position=None, point_id=None):
            if point_id is None:
                point_id = random.randint(0, len(self.nodes) - 1)
            x = random.random()
            y = random.random()
            if position is not None:
                x, y = position
            route = Route(self.nodes[point_id], (x, y), len(self.routing))
            self.routing.append(route)
            self.nodes[point_id].add_route(route)

        def run(self):
            for node in self.nodes:
                node.move()
            for node in self.nodes:
                node.update()

        def draw_text(self, image, text, position, size, color=(200, 200, 200)):
            font = cv2.FONT_HERSHEY_SIMPLEX
            textsize = cv2.getTextSize(str(text), font, size, 2)[0]
            x = int(position[0] - (textsize[0] / 2))
            y = int(position[1] + (textsize[1] / 2))
            cv2.putText(image, str(text), (x, y), font, size, color, 2)

        def draw_route(self, source, size, show_path=0):

            def draw_circle(image, x, y, color, radius):
                radius = int(radius)
                x = int(x * size)
                y = int(y * size)
                image = cv2.circle(image, (x, y), radius, color, -1)
                return image

            def draw_number(image, step, x, y, size):
                font = cv2.FONT_HERSHEY_SIMPLEX
                text = str(step)
                x = int(x * size)
                y = int(y * size)
                textsize = cv2.getTextSize(str(text), font, size, 1)[0]
                x = int(x - (textsize[0] / 2))
                y = int(y + (textsize[1] / 2))
                cv2.putText(image, text, (x, y), font, size, (255, 255, 255), 1)

            image = source
            if not show_path:
                image = source.copy()

            for route in self.routing:
                x, y = get_center(route.node.zona)
                if show_path:
                    image = draw_circle(image, x, y, self.action_colors[route.status], radius=6 * size / 512)
                    m = size / 1024
                    draw_number(image, route.num_steps, x, y, size=m)
                else:
                    image = draw_circle(image, x, y, self.action_colors[route.status], radius=6 * size / 512)
                image = draw_circle(image, route.point[0], route.point[1], (0, 0, 0), radius=6 * size / 512)

            return image

        def draw_field(self, size=512, show_names=True):
            image = np.ones((size, size, 3), np.uint8) * 255
            for node in self.nodes:
                x1 = int(node.zona[0] * size)
                y1 = int(node.zona[1] * size)
                x2 = int(node.zona[2] * size)
                y2 = int(node.zona[3] * size)
                image = cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), 1)

                if show_names:
                    self.draw_text(image, node.name + 1, ((x1 + x2) / 2, (y1 + y2) / 2), size=(node.zona[2] - node.zona[0]) * size / 50)
            return image

        def count_route(self, status='finished'):
            counter = 0
            for route in self.routing:
                if route.status == status:
                    counter += 1
            return counter


        def count_neighbors(self):
            neighbors = []
            for node in self.nodes:
                neighbors.append(len(node.zone_neighbors))
            return neighbors

        def visualize(self, max_iter = 10,  img_size=512, show_names=True, show_path=False, show=True, save_folder=None, stat=False):

            field = self.draw_field(size=img_size + 1, show_names=show_names)
            image = self.draw_route(field, img_size, show_path)

            stats = {'path_length': [], 'num_routes': []}

            i = 0
            while i < math.sqrt(self.num_peers):
                self.run()

                if stat:
                    stats['num_routes'].append([])
                    for node in self.nodes:
                        stats['num_routes'][-1].append(node.routes.qsize())

                image = self.draw_route(field, img_size, show_path)

                if show:
                    cv2.imshow("CAN", image)
                    cv2.waitKey(0)
                if save_folder is not None:
                    cv2.imwrite(save_folder + str(i) + ".png", image)
                if self.count_route('finished') == len(self.routing):
                    i = max_iter

                i += 1

            cv2.destroyAllWindows()

            if stat:
                stats['num_neighbors'] = self.count_neighbors()
                for route in self.routing:
                    stats['path_length'].append(route.num_steps)
                return stats

can = CAN(1000)
can.generate()
start_time = time.time()

for i in range(1000):
    can.generate_route()
about_graph = can.visualize(img_size=512, max_iter=1000, show_names=False, show_path=False, show=False, stat=True, save_folder="'D:\\Programming\\Python\\GlobalNetworks\\Lab3\\test1\\")

# can.generate_route(position= (0.72, 0.52), point_id=0)
# about_graph = can.visualize(img_size=512, max_iter=100, show_names=False, show_path=True, show=True, stat=True, save_folder='D:\\Programming\\Python\\GlobalNetworks\\Lab3\\test\\')

print("--- %s seconds ---" % (time.time() - start_time))
print(stats_report(about_graph))