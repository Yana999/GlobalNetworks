import numpy as np
import random
import cv2

from distance import *
from node import Action, Node


class CAN():
    def __init__(self, n, seed=10, mode='run', random_point=None):
        self.n = n
        self.seed = seed
        self.nodes = []
        self.importance = []
        self.actions = []
        self.action_colors = {'opened': (0, 150, 0), 'closed': (0, 0, 150), 'error': (150, 0, 0)}
        self.mode = mode
        self.random_point = random_point

    def add_node(self, node_id):

        def split(zona):
            if zona[2] - zona[0] == zona[3] - zona[1]:
                return (zona[0], zona[1], zona[0] + (zona[2] - zona[0]) / 2, zona[3]), (zona[0] + (zona[2] - zona[0]) / 2, zona[1], zona[2], zona[3])
            else:
                return (zona[0], zona[1], zona[2], zona[1] + (zona[3] - zona[1]) / 2), (zona[0], zona[1] + (zona[3] - zona[1]) / 2, zona[2], zona[3])

        def check_neighbor(rect1, rect2):

            def check_first(zona1, zona2):
                x1, y1, x2, y2 = zona1
                x12 = (x1 + x2) / 2
                y12 = (y1 + y2) / 2
                n_zeros = False
                n_zeros = n_zeros or (compute_distance((x1, y1), zona2) == 0 and compute_distance((x1, y2), zona2) == 0 and compute_distance((x1, y12), zona2) == 0)
                n_zeros = n_zeros or (compute_distance((x1, y2), zona2) == 0 and compute_distance((x2, y2), zona2) == 0 and compute_distance((x12, y2), zona2) == 0)
                n_zeros = n_zeros or (compute_distance((x2, y1), zona2) == 0 and compute_distance((x1, y1), zona2) == 0 and compute_distance((x12, y1), zona2) == 0)
                n_zeros = n_zeros or (compute_distance((x2, y2), zona2) == 0 and compute_distance((x2, y1), zona2) == 0 and compute_distance((x2, y12), zona2) == 0)
                return n_zeros and zona1 != zona2

            return check_first(rect1, rect2) or check_first(rect2, rect1)

        zona1, zona2 = split(self.nodes[node_id].rect)
        self.nodes[node_id].rect = zona1

        table = self.nodes[node_id].table
        self.nodes.append(Node(len(self.nodes), zona2))

        for key in list(table.keys()):
            if check_neighbor(zona2, table[key].rect):
                self.nodes[-1].add_neighbor(table[key])
                table[key].add_neighbor(self.nodes[-1])
            if not check_neighbor(zona1, table[key].rect):
                table[key].remove_neighbor(self.nodes[node_id].name)
                self.nodes[node_id].remove_neighbor(key)

        self.nodes[node_id].add_neighbor(self.nodes[-1])
        self.nodes[-1].add_neighbor(self.nodes[node_id])





    def add_random_pointers(self):
        if self.random_point is not None:
            for i in range(self.random_point):
                ind1, ind2 = 1, 1
                while ind1 == ind2:
                    ind1 = random.randint(0, len(self.nodes) - 1)
                    ind2 = random.randint(0, len(self.nodes) - 1)
                self.nodes[ind1].add_neighbor(self.nodes[ind2])
                self.nodes[ind2].add_neighbor(self.nodes[ind1])

    def generate(self, max_neighbors=10):
        random.seed(self.seed)
        self.nodes = []
        self.nodes.append(Node(0, (0.0, 0.0, 1.0, 1.0)))
        self.importance.append(1)
        for i in range(self.n - 1):
            node_id = random.choices(range(len(self.nodes)), self.importance)[0]
            self.add_node(node_id)
            space = (self.nodes[node_id].rect[3]-self.nodes[node_id].rect[1]) * (self.nodes[node_id].rect[2]-self.nodes[node_id].rect[0])
            self.importance.append(space)
            self.importance[node_id] = space
        self.add_random_pointers()

    def generate_action(self, position=None, sender_id=None):
        if sender_id is None:
            sender_id = random.randint(0, len(self.nodes) - 1)
        x = random.random()
        y = random.random()
        if position is not None:
            x, y = position
        action = Action(self.nodes[sender_id], (x, y), len(self.actions))
        self.actions.append(action)
        self.nodes[sender_id].add_action(action)

    def run(self):
        for node in self.nodes:
            node.make_step()
        for node in self.nodes:
            node.update()

    def draw_text(self, image, text, position, size, color=(200, 200, 200)):
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(str(text), font, size, 2)[0]
        x = int(position[0] - (textsize[0] / 2))
        y = int(position[1] + (textsize[1] / 2))
        cv2.putText(image, str(text), (x, y), font, size, color, 2)

    def draw_actions(self, source, size, show_path=0):

        def draw_circle(image, x, y, color, sz):
            sz = int(sz)
            x = int(x * size)
            y = int(y * size)
            image = cv2.circle(image, (x, y), sz, color, -1)
            return image

        def draw_number(image, name, step, x, y, sz):
            font = cv2.FONT_HERSHEY_SIMPLEX
            text = str(step)
            x = int(x * size)
            y = int(y * size)
            textsize = cv2.getTextSize(str(text), font, sz, 1)[0]
            x = int(x - (textsize[0] / 2))
            y = int(y + (textsize[1] / 2))
            cv2.putText(image, text, (x, y), font, sz, (255, 255, 255), 1)

        image = source
        if not show_path:
            image = source.copy()

        for action in self.actions:
            x, y = find_center(action.node.rect)
            if show_path:
                image = draw_circle(image, x, y, self.action_colors[action.status], sz=15*size/512)
                draw_number(image, action.data, action.n_steps, x, y, sz=size/1024)
            else:
                image = draw_circle(image, x, y, self.action_colors[action.status], sz=7*size/512)
            image = draw_circle(image, action.point[0], action.point[1], (0, 0, 0), sz=7*size/512)

        return image

    def draw_field(self, rect=(0, 0, 1, 1), size=512, show_names=True):
        image = np.ones((size, size, 3), np.uint8) * 255
        for node in self.nodes:
            x1 = int(node.rect[0] * size)
            y1 = int(node.rect[1] * size)
            x2 = int(node.rect[2] * size)
            y2 = int(node.rect[3] * size)
            image = cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), 1)
            if show_names:
                self.draw_text(image, node.name, ((x1 + x2) / 2, (y1 + y2) / 2), size=(node.rect[2]-node.rect[0])*size/50)
        return image

    def count_actions(self, status='closed'):
        counter = 0
        for action in self.actions:
            if action.status == status:
                counter += 1
        return counter

    def print_actions(self):
        for action in self.actions:
            print(action.sender, action.node.name, action.point, action.data, action.status, action.n_steps)

    def count_neighbors(self):
        neighbors = []
        for node in self.nodes:
            neighbors.append(len(node.table))
        return neighbors

    def visualize(self, rect=None, max_iter=10, size=512, show_names=True,
                  show_path=False, show_frames=True, save_folder=None, collect_stats=False):
        field = self.draw_field(size=size+1, show_names=show_names)
        image = self.draw_actions(field, size, show_path)

        stats = {'path_length': [], 'n_actions': []}

        i = 0
        while i < max_iter:
            self.run()

            if self.mode == 'debug':
                self.print_actions()
            if collect_stats:
                stats['n_actions'].append([])
                for node in self.nodes:
                    stats['n_actions'][-1].append(node.actions.qsize())

            image = self.draw_actions(field, size, show_path)

            if show_frames:
                cv2.imshow("CAN", image)
                cv2.waitKey(0)
            if save_folder is not None:
                cv2.imwrite(save_folder + str(i) + ".png", image)
            if self.count_actions('closed') == len(self.actions):
                i = max_iter

            i += 1

        cv2.destroyAllWindows()

        if collect_stats:
            stats['n_neighbors'] = self.count_neighbors()
            for action in self.actions:
                stats['path_length'].append(action.n_steps)
            return stats