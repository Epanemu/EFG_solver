from enum import IntEnum
from typing import List, Optional, Tuple

from copy import deepcopy
from itertools import combinations

# Do not print anything besides the tree in your submission.
# Implement all methods, the __str__ methods are optional (for nice labels).
# However if you wish, you can completely change structure of the code.
# What we care about is that the tree is exported in valid format.

infoset_counter = 0
infoset_map_agent = {}
infoset_map_bandit = {}

class HistoryType(IntEnum):
    decision = 1
    chance = 2
    terminal = 3


class Player(IntEnum):
    agent = 0
    bandit = 1


class ActionType(IntEnum):
    GoLeft = 1
    GoRight = 2
    GoUp = 3
    GoDown = 4
    Ambushed = 5
    Defended = 6
    PlaceBandits = 7
    SwapPlace = 8
    Stay = 9

    def opposite(self):
        return {
            ActionType.GoLeft: ActionType.GoRight,
            ActionType.GoRight: ActionType.GoLeft,
            ActionType.GoUp: ActionType.GoDown,
            ActionType.GoDown: ActionType.GoUp,
        }[self]

    def __str__(self):
        return self.name


class Action:
    def __init__(self,
                 action_type: ActionType,
                 position: Optional['Pos'] = None,
                 target: Optional['Pos'] = None):
        self.action_type = action_type
        self.pos = position
        self.target = target

    def __str__(self):
        if self.action_type == ActionType.SwapPlace:
            return f"{self.action_type.name} {self.pos} -> {self.target}"
        if self.action_type == ActionType.PlaceBandits:
            return f"{self.action_type.name} {self.pos}"
        return f"{self.action_type.name}"

    def __repr__(self):
        if self.action_type == ActionType.SwapPlace:
            return f"{self.action_type.name} {self.pos} -> {self.target}"
        if self.action_type == ActionType.PlaceBandits:
            return f"{self.action_type.name} {self.pos}"
        return f"{self.action_type.name}"


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


class Pos:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def apply_action(self, action: Action) -> 'Pos':
        return {
            ActionType.GoRight: Pos(self.x+1, self.y),
            ActionType.GoLeft: Pos(self.x-1, self.y),
            ActionType.GoDown: Pos(self.x, self.y+1),
            ActionType.GoUp: Pos(self.x, self.y-1),
        }[action.action_type]

    def __eq__(self, o):
        return self.x == o.x and self.y == o.y

    def __hash__(self):
        return hash(f"{self.x} {self.y}")

    def __str__(self):
        return f"[{self.x}, {self.y}]"

    def __repr__(self):
        return f"[{self.x}, {self.y}]"

class Game:
    def __init__(self):
        h = int(input())
        w = int(input())
        self.mazebox = [None] * h
        for i in range(h):
            self.mazebox[i] = list(map(map_tile, input()))
        self.n_bandits = int(input())
        self.ambush_prob = float(input())

        self.start_pos = None
        self.dangers = []
        for i, row in enumerate(self.mazebox):
            for j, tile in enumerate(row):
                if tile == Tile.start:
                    self.start_pos = Pos(j, i)
                if tile == Tile.danger:
                    self.dangers.append(Pos(j, i))

    def get_actions(self, pos: Pos) -> List[Action]:
        actions = []
        if self.mazebox[pos.y][pos.x+1] != Tile.blocked:
            actions.append(Action(ActionType.GoRight))
        if self.mazebox[pos.y][pos.x-1] != Tile.blocked:
            actions.append(Action(ActionType.GoLeft))
        if self.mazebox[pos.y+1][pos.x] != Tile.blocked:
            actions.append(Action(ActionType.GoDown))
        if self.mazebox[pos.y-1][pos.x] != Tile.blocked:
            actions.append(Action(ActionType.GoUp))
        return actions

    def walk_path(self, pos: Pos, action: Action) -> List[Tuple[Tile, Action, Pos]]:
        events = []
        while True:
            pos = pos.apply_action(action)
            if self.at(pos) in [Tile.danger, Tile.gold]:
                events.append((self.at(pos), action, pos))
            actions = self.get_actions(pos)
            if len(actions) != 2 or self.at(pos) in [Tile.goal, Tile.start]:
                break
            action = actions[0] if (actions[0].action_type != action.action_type.opposite()) else actions[1]
        events.append((None, action, pos))
        return events

    def at(self, pos: Pos) -> Tile:
        return self.mazebox[pos.y][pos.x]

    def goal(self, pos: Pos) -> bool:
        return self.mazebox[pos.y][pos.x] == Tile.goal

class Infoset:
    def __init__(self, curr_history: 'History'):
        self.h = curr_history

    def index(self) -> str:
        global infoset_counter, infoset_map_agent, infoset_map_bandit
        if self.h.player == Player.agent:
            id_infoset = "1" + f"{self.h.crossroad_actions} {self.h.n_bandits} {self.h.gold} {self.h.curr_pos} {self.h.combat_points} {self.h.seen_danger}"
            # print(id_infoset)
            if id_infoset not in infoset_map_agent:
                infoset_map_agent[id_infoset] = infoset_counter
                infoset_counter += 1
            return infoset_map_agent[id_infoset]
        if self.h.player == Player.bandit:
            id_infoset = "2"+" ".join(map(lambda x: f"{x}", self.h.bandits_positions))+f"{self.h.curr_pos}"
            # print(id_infoset)
            if id_infoset not in infoset_map_bandit:
                infoset_map_bandit[id_infoset] = infoset_counter
                infoset_counter += 1
            return infoset_map_bandit[id_infoset]
        # else:
        #     print("This does not happen")

    def __str__(self):
        return ""


class History:
    def __init__(self, game: Game):
        self.game = game
        self.player = Player.bandit
        if game.n_bandits <= 0 or len(game.dangers) == 0:
            self.player = Player.agent

        # agent's information
        self.visited_crossroads = []
        self.combat_points = []
        self.crossroad_actions = []
        self.last_action = None
        self.gold = 0
        self.n_bandits = game.n_bandits
        self.dead = False
        self.seen_danger = False
        self.event_buffer = []

        # somewhat shared information
        self.curr_pos = game.start_pos

        # bandits' information
        self.bandits_positions = set()
        self.bandit_swapped = None

        self.iset = Infoset(self)

    def __ambush(self):
        return self.curr_pos in self.bandits_positions

    def __stuck(self):
        return self.curr_pos in self.visited_crossroads

    def __agent_actions(self):
        if self.game.goal(self.curr_pos) or self.__stuck() or self.dead:
            return []
        actions = self.game.get_actions(self.curr_pos)
        back_a_t = self.last_action.action_type.opposite() if self.last_action is not None else None
        return list(filter(lambda a: a.action_type != back_a_t, actions))

    def __all_swappings(self):
        swaps = []
        non_targetable = list(self.bandits_positions) + [self.curr_pos]
        for danger in self.game.dangers:
            if danger not in non_targetable:
                for source in self.bandits_positions:
                    swaps.append(Action(ActionType.SwapPlace, source, danger))
        # print(swaps)
        return swaps

    def __exec_events(self):
        i = 0
        for event in self.event_buffer:
            i += 1
            tile, action, pos = event
            self.last_action = action
            self.curr_pos = pos
            if tile is None:
                self.event_buffer = []
                self.player = Player.agent
                return
            if tile == Tile.gold:
                self.gold += 1
            elif tile == Tile.danger:
                if self.__ambush():
                    self.seen_danger = True
                    break
                if not self.seen_danger:
                    self.seen_danger = True
                    self.player = Player.bandit
                    break
        self.event_buffer = self.event_buffer[i:]


    def type(self) -> HistoryType:
        if self.dead or (len(self.event_buffer) == 0 and len(self.__agent_actions()) == 0):
            return HistoryType.terminal
        if self.__ambush():
            return HistoryType.chance
        return HistoryType.decision

    def current_player(self) -> Player:
        return self.player

    # infoset index: histories with the same infoset index belong to the same infoset
    def infoset(self) -> Infoset:
        return self.iset

    def actions(self) -> List[Action]:
        if self.__ambush():
            return [Action(ActionType.Ambushed), Action(ActionType.Defended)]
        actions = []
        if self.player == Player.bandit:
            if self.last_action == None:
                for c in combinations(self.game.dangers, self.game.n_bandits):
                    actions.append(Action(ActionType.PlaceBandits, c))
            # cannot be an ambush at this point -> swap
            elif self.game.at(self.curr_pos) == Tile.danger:
                actions = [Action(ActionType.Stay)] + self.__all_swappings()
            else:
                print("PROBLEMATIC SITUATION")
        else:
            actions = self.__agent_actions()
        return actions

    # for player 1
    def utility(self) -> float:
        if self.game.goal(self.curr_pos):
            return 10 + self.gold
        else:
            return 0

    def chance_prob(self, action: Action) -> float:
        if action.action_type == ActionType.Ambushed:
            return self.game.ambush_prob
        else:
            return 1 - self.game.ambush_prob

    def child(self, action: Action) -> 'History':
        next_h = deepcopy(self)
        if action.action_type == ActionType.Ambushed:
            next_h.dead = True
        elif action.action_type == ActionType.Defended:
            next_h.n_bandits -= 1
            next_h.bandits_positions.remove(self.curr_pos)
            next_h.combat_points.append(self.curr_pos)
            next_h.__exec_events()
        elif self.player == Player.agent:
            # next_h.curr_pos = next_h.curr_pos.apply_action(action)
            next_h.crossroad_actions.append(action)
            next_h.visited_crossroads.append(self.curr_pos)
            next_h.event_buffer = self.game.walk_path(self.curr_pos, action)
            # for b in next_h.event_buffer:
            #     print(b)
            next_h.__exec_events()
        else:
            if action.action_type == ActionType.PlaceBandits:
                next_h.bandits_positions = set(action.pos)
                next_h.player = Player.agent
            elif action.action_type == ActionType.SwapPlace:
                next_h.bandits_positions.remove(action.pos)
                next_h.bandits_positions.add(action.target)
                next_h.bandit_swapped = (action.pos, action.target)
                next_h.__exec_events()
            elif action.action_type == ActionType.Stay:
                next_h.__exec_events()
            else:
                print("OOF, a problem with actions :D")
        # for b in next_h.event_buffer:
        #     print(b)
        # if action.action_type == ActionType.SwapPlace:
        #     print(action, self.curr_pos, self.__all_swappings(), self.bandits_positions)
        # print(action, next_h.curr_pos, next_h.type(), next_h.utility())
        return next_h

    def __str__(self):
        return ""  # history label



# read the maze from input and return the root node
def create_root() -> History:
    game = Game()
    return History(game)



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