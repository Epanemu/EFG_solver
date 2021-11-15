from enum import IntEnum
from typing import List

class Tile(IntEnum):
    blocked = 0
    free = 1
    danger = 2
    gold = 3
    start = 4
    goal = 5

    def __str__(self):
        return self.name

def map_tile(c: str):
    return {
        '#': Tile.blocked,
        '-': Tile.free,
        'E': Tile.danger,
        'G': Tile.gold,
        'S': Tile.start,
        'D': Tile.goal,
    }[c]

class Node:
    def __init__(self, pos, actions, final=False):
        self.y, self.x = pos
        self.final = final
        self.actions = actions

    def __str__(self):
        return f"[{self.x}, {self.y}] {'/FINAL/ ' if self.final else ''}({' '.join(map(lambda x: f'{x}', self.actions))})"

class Connection:
    def __init__(self, dst_i, events):
        self.dst_i = dst_i
        self.events = events

    def __str__(self):
        return f"to {self.dst_i} ({' '.join(map(lambda x: f'{x}', self.events))})"


class Maze:
    def __init__(self):
        h = int(input())
        w = int(input())
        self.mazebox = [None] * h
        for i in range(h):
            self.mazebox[i] = list(map(map_tile, input()))
        self.n_bandits = int(input())
        self.ambush_prob = float(input())

        self.start_i = None
        self.walkgraph = self.__create_walkgraph()

    def __create_walkgraph(self):
        self.nodes = []
        for i, row in enumerate(self.mazebox):
            for j, tile in enumerate(row):
                if tile == Tile.blocked:
                    continue
                actions = self.__get_actions(i, j)
                if tile == Tile.start:
                    self.start_i = len(self.nodes)
                    self.nodes.append(Node([i, j], actions))
                elif tile == Tile.goal:
                    self.nodes.append(Node([i, j], actions, final=True))
                elif len(actions) > 2: # it is not only Go, there is a potential for deciding
                    self.nodes.append(Node([i, j], actions))

        self.connections = [{} for _ in self.nodes]
        for node_i, node in enumerate(self.nodes):
            for a in node.actions:
                if a not in self.connections[node_i]:
                    x_conn, y_conn, in_action, events = self.__walk_Go(node.x, node.y, a)
                    conn_node_i = None
                    for i, other_node in enumerate(self.nodes):
                        if other_node.x == x_conn and other_node.y == y_conn:
                            conn_node_i = i
                            break
                    self.connections[node_i][a] = Connection(conn_node_i, events)
                    self.connections[conn_node_i][in_action] = Connection(node_i, list(reversed(events)))

    def __get_actions(self, y, x):
        actions = []
        if self.mazebox[y][x+1] != Tile.blocked:
            actions.append(Action.GoRight)
        if self.mazebox[y][x-1] != Tile.blocked:
            actions.append(Action.GoLeft)
        if self.mazebox[y+1][x] != Tile.blocked:
            actions.append(Action.GoDown)
        if self.mazebox[y-1][x] != Tile.blocked:
            actions.append(Action.GoUp)
        return actions

    def __apply_action(self, x, y, action):
        return {
            Action.GoRight: [x+1, y],
            Action.GoLeft: [x-1, y],
            Action.GoDown: [x, y+1],
            Action.GoUp: [x, y-1],
        }[action]

    def __walk_Go(self, x_in, y_in, action):
        x, y = self.__apply_action(x_in, y_in, action)
        actions = self.__get_actions(y, x)
        events = []
        while len(actions) == 2 and self.mazebox[y][x] not in [Tile.goal, Tile.start]:
            if self.mazebox[y][x] == Tile.danger:
                events.append(Tile.danger)
            elif self.mazebox[y][x] == Tile.gold:
                events.append(Tile.gold)
            op_a = action.opposite()
            action = actions[0] if actions[0] != op_a else actions[1]
            x, y = self.__apply_action(x, y, action)
            actions = self.__get_actions(y, x)
        return x, y, action.opposite(), events

    def __str__(self):
        res = "MAZE:\n"
        res += f"start node index: {self.start_i}\n"
        for i, node in enumerate(self.nodes):
            res += f"\tNODE {i}:\n"
            res += f"\t{node}\n"
            for a, connection in self.connections[i].items():
                res += f"\t\t{a} - {connection}\n"
            # res += "\n"
        return res

# Do not print anything besides the tree in your submission.
# Implement all methods, the __str__ methods are optional (for nice labels).
# However if you wish, you can completely change structure of the code.
# What we care about is that the tree is exported in valid format.

class HistoryType(IntEnum):
    decision = 1
    chance = 2
    terminal = 3


class Player(IntEnum):
    agent = 0
    bandit = 1


# class ActionType(IntEnum):
#     walk = 1

class Action(IntEnum):
    GoLeft = 1
    GoRight = 2
    GoUp = 3
    GoDown = 4
    Ambushed = 5
    Defended = 6
    SwapPlace = 7

    def opposite(self):
        return {
            Action.GoLeft: Action.GoRight,
            Action.GoRight: Action.GoLeft,
            Action.GoUp: Action.GoDown,
            Action.GoDown: Action.GoUp,
            Action.Ambushed: Action.Ambushed,
            Action.Defended: Action.Defended,
            Action.SwapPlace: Action.SwapPlace,
        }[self]

    def __str__(self):
        return self.name  # action label


class Infoset:
    def index(self) -> int:
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class History:
    def __init__(self, maze: Maze):
        self.maze = maze

    def type(self) -> HistoryType:
        raise NotImplementedError

    def current_player(self) -> Player:
        raise NotImplementedError

    # infoset index: histories with the same infoset index belong to the same infoset
    def infoset(self) -> Infoset:
        raise NotImplementedError

    def actions(self) -> List[Action]:
        raise NotImplementedError

    # for player 1
    def utility(self) -> float:
        raise NotImplementedError

    def chance_prob(self, action: Action) -> float:
        raise NotImplementedError

    def child(self, action: Action) -> 'History':
        raise NotImplementedError

    def __str__(self):
        return ""  # history label



# read the maze from input and return the root node
def create_root() -> History:
    maze = Maze()
    print(maze)
    return History(maze)



########### Do not modify code below.

def export_gambit(root_history: History) -> str:
    players = ' '.join([f"\"Pl{i}\"" for i in range(2)])
    ret = f"EFG 2 R \"\" {{ {players} }} \n"

    terminal_idx = 1
    chance_idx = 1

    def build_tree(history, depth):
        nonlocal ret, terminal_idx, chance_idx

        ret += " " * depth  # add nice spacing

        if history.type() == HistoryType.terminal:
            util = history.utility()
            ret += f"t \"{history}\" {terminal_idx} \"\" "
            ret += f"{{ {util}, {-util} }}\n"
            terminal_idx += 1
            return

        if history.type() == HistoryType.chance:
            ret += f"c \"{history}\" {chance_idx} \"\" {{ "
            ret += " ".join([f"\"{str(action)}\" {history.chance_prob(action):.3f}"
                            for action in history.actions()])
            ret += " } 0\n"
            chance_idx += 1

        else:  # player node
            player = int(history.current_player()) + 1  # cannot be indexed from 0
            infoset = history.infoset()
            ret += f"p \"{history}\" {player} {infoset.index()} \"\" {{ "
            ret += " ".join([f"\"{str(action)}\"" for action in history.actions()])
            ret += " } 0\n"

        for action in history.actions():
            child = history.child(action)
            build_tree(child, depth + 1)

    build_tree(root_history, 0)
    return ret


if __name__ == '__main__':
    print(export_gambit(create_root()))

## Following is an example implementation of the game of simple poker.
#
# from copy import deepcopy
#
# class HistoryType(IntEnum):
#   decision = 1
#   chance = 2
#   terminal = 3
#
#
# class Player(IntEnum):
#   first = 0
#   second = 1
#   chance = 2
#   terminal = 3
#
#
# class Action(IntEnum):
#   CardsJJ = 0
#   CardsJQ = 1
#   CardsQJ = 2
#   CardsQQ = 3
#   Fold = 4
#   Bet = 5
#   Call = 6
#
#   def __str__(self):
#     return self.name  # action label
#
#
# def action_to_cards(action):
#   return {
#     Action.CardsJJ: ["J", "J"],
#     Action.CardsJQ: ["J", "Q"],
#     Action.CardsQJ: ["Q", "J"],
#     Action.CardsQQ: ["Q", "Q"],
#   }[action]
#
#
# class Infoset:
#   def __init__(self, card: str, player: int):
#     self.card = card
#     self.player = player
#
#   def index(self) -> int:
#     return ord(self.card) * (self.player+1)
#
#   def __str__(self):
#     return self.card
#
#
# class History:
#   def __init__(self):
#     self.player = Player.chance
#     self.player_cards = []
#     self.action_history = []
#
#   def type(self) -> HistoryType:
#     if self.player == Player.chance:
#       return HistoryType.chance
#     elif self.player == Player.terminal:
#       return HistoryType.terminal
#     else:
#       return HistoryType.decision
#
#   def current_player(self) -> Player:
#     return self.player
#
#   # infoset index: histories with the same infoset index belong to the same infoset
#   def infoset(self) -> Infoset:
#     return Infoset(self.player_cards[self.player], self.player)
#
#   def actions(self) -> List[Action]:
#     if self.player == Player.chance:
#       return [Action.CardsJJ, Action.CardsJQ, Action.CardsQJ, Action.CardsQQ]
#     if self.player == Player.first:
#       return [Action.Fold, Action.Bet]
#     if self.player == Player.second:
#       return [Action.Fold, Action.Call]
#
#   # for player 1
#   def utility(self) -> float:
#     if self.action_history[1] == Action.Fold:
#       return -1
#     if self.action_history[2] == Action.Fold:
#       return 1
#     # otherwise it was bet followed by call:
#     if self.action_history[0] in [Action.CardsJJ, Action.CardsQQ]:
#       return 0
#     if self.action_history[0] == Action.CardsJQ:
#       return -3
#     if self.action_history[0] == Action.CardsQJ:
#       return 3
#
#   def chance_prob(self, action: Action) -> float:
#     if action in [Action.CardsJJ, Action.CardsQQ]:
#       return 1 / 6.
#     else:
#       return 1 / 3.
#
#   def child(self, action: Action) -> 'History':
#     next = self.clone()
#     next.action_history.append(action)
#
#     if self.player == Player.chance:
#       next.player = Player.first
#       next.player_cards = action_to_cards(action)
#     elif self.player == Player.first:
#       next.player = Player.second
#     elif self.player == Player.second:
#       next.player = Player.terminal
#
#     if action == Action.Fold:
#       next.player = Player.terminal
#
#     return next
#
#   def clone(self) -> 'History':
#     return deepcopy(self)
#
#   def __str__(self):
#     return ""  # history label
#
#
# def create_root() -> History:
#   return History()