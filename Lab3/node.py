from queue import Queue
from distance import *

class Action():
    def __init__(self, sender_node, point, data, status="opened"):
        self.sender = find_center(sender_node.rect)
        self.node = sender_node
        self.point = point
        self.data = data
        self.status = status
        self.n_steps = 0


class Node():
    def __init__(self, name, rect):
        self.name = name
        self.rect = rect
        self.table = dict()
        self.new_actions = []
        self.actions = Queue()

    def add_neighbor(self, neighbor):
        self.table[neighbor.name] = neighbor

    def remove_neighbor(self, neighbor_name):
        self.table.pop(neighbor_name)

    def add_action(self, action):
        action.node = self
        self.new_actions.append(action)

    def close_action(self, action):
        action.status = "closed"

    def send_action(self, action):
        min_distance = 2.0
        best_neighbor = None
        action.n_steps += 1

        for key in self.table.keys():
            current_distance = compute_distance(action.point, self.table[key].rect)
            if current_distance < min_distance:
                min_distance = current_distance
                best_neighbor = self.table[key]

        if best_neighbor is None:
            action.status = "error"
        else:
            best_neighbor.add_action(action)

    def make_step(self):
        if not self.actions.empty():
            action = self.actions.get()
            if compute_distance(action.point, self.rect) > 0:
                self.send_action(action)
            else:
                self.close_action(action)

    def update(self):
        for action in self.new_actions:
            self.actions.put(action)
        self.new_actions = []