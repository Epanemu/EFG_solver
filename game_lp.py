# You can use your own implementation of game tree for testing.
# It should satisfy the original interfaces in game_tree.py
#
# The game tree implementation does not have to be the bandits game:
# you can use any game implementation, for example the simple poker.
# You have constructed the LP by hand at class, so you can check
# that for debugging.
#
# Note that the LP must support any EFG, especially including ones where
# the player makes multiple moves before it's opponent's turn.
#
# For automatic evaluation, test version of game_tree will be imported.
# In  your solution, submit only this file, i.e. game_lp.py
from game_tree import *


# Following packages are supported:
# Solvers:
import gurobipy as gb # == 9.0.3
from gurobipy import GRB
# import cvxopt # == 1.2.3
#
# Matrix manipulation:
# import numpy as np
from copy import deepcopy


# Do not print anything besides the final output in your submission.
# Implement the LP as a function of the game tree.
#
# You MUST SPECIFY the LP as a function of the player!
# I.e do NOT construct it only for player 0, and return the -value
# when asked for player 1 (do not use the zero-sum property
# for the value in the root). I.e. you are not allowed to make
# only one LP for both players, and find the value as `u_2(root) = -u_1(root)`.
#
# For each of the players you should have different sets of constraints,
# since they have different opponent infosets and player sequences.
# Within the constraints, you can of course use the fact that
# `u_2(z) = -u_1(z)` (where `z` is leaf in the tree), and you can specify
# the LP as maximization for both of the players.
#
# If you don't satisfy this, you will be heavily penalized.
#
# At the course webpage, we have calculated some testing game values for you.
# You can use them to check if your LP has been well specified.

class Sequence():
    def __init__(self):
        self.seq = []

    def append(self, elem):
        self.seq.append(elem)

    def __getitem__(self, i):
        return self.seq[i]

    def __hash__(self):
        return hash("_".join(map(lambda x:f"{x}", self.seq)))

    def __eq__(self, o):
        return self.seq == o.seq

    def __len__(self):
        return len(self.seq)


def root_value(root: History, player: Player) -> float:
    """
    Create sequence-form LP from supplied EFG tree and solve it.

    Do not rely on any specifics of the original maze problem.
    Your LP should solve this problem for any EFG tree, if it is described
    by the original interface.

    The LP must be constructed for the given player:
    you should also compute the realization plan for that player.

    Return the expected utility in the root node for the player.
    So for the first player this will be the game value.

    Tip: Actions are ordered in the sense that that for two histories
        h,g in the same infoset it holds that h.actions() == g.actions().
        You can use action's index in the list for it's identification.
        Do not use str(action) or some other way of encoding the action based
        on your previous implementation.

        To identify **sequences** it is not enough to use the list of actions indices!
        Consider simple poker: first player can fold or bet.
        Folding in one Infoset_1  (player has card J) is however not the same thing
        as folding in Infoset_2 (player has card Q)!

        In class, we identified folding as f1 and f2, based on the fact from which
        infoset they came from.

    :param root: root history of the EFG tree
    :param player: zero-indexed player: first player has index 0,
                    second player has index 1
    :return: expected value in the root for given player
    """
    # sequence is a list of tuples (infoset index, action index), this is list of sequences for each player
    # sequence is a list of tuples (infoset index, action index), this is map of sequences to their ids for each player
    sequences = {0:{}, 1:{}}

    # [(infoset index, action index)] -> int index - will be used to set a variable in lp - for player
    # seq_ID -> int index - will be used to set a variable in lp - for player - useless, use seq_ID
    # sequence_probs = {}

    # (infoset index, action index) -> [(my sequence, prob, g val) | (None, prob, infoset id)]  - for other player, potentially creates multiple same constraints
    # (infoset index, action index) -> [(seq_ID, prob, g val) | (None, prob, infoset id)]  - for other player, potentially creates multiple same constraints
    sum_constraints = {}

    # [(infoset index, action index)] -> [[(infoset index, action index)]] - for player, decides which sequences should sum to this one.
    # (seq_ID, curr_infoset_id) -> [seq_ID] - for player, decides which sequences should sum to this one.
    next_seqs = {}

    # id_counter = 0

    # root sequences
    curr_seq = {0:Sequence(), 1:Sequence()}
    sequences[0][Sequence()] = 0#id_counter
    sequences[1][Sequence()] = 1#id_counter + 1

    # next_seqs[(sequences[player][Sequence()], None)] = []
    sum_constraints[(None, None)] = []

    build_lp(root, curr_seq, 1, player, sequences, sum_constraints, next_seqs, 2)#id_counter+2)

    # for seq in sequences[player]:
    #     print(seq.seq, sequences[player][seq])

    # print()

    # for seq in sequences[(player+1) % 2]:
    #     print(seq.seq, sequences[(player+1) % 2][seq])

    m = gb.Model("tree_game")
    m.setParam("OutputFlag", 0)

    # for each of my sequences, create a prob sum constraint
    prob_vars = {}
    for seq_id in sequences[player].values():
        # print(seq_id)
        prob_vars[seq_id] = m.addVar(name=f"r_{seq_id}")
        m.addConstr(prob_vars[seq_id] >= 0)
    for s, next_ss in next_seqs.items():
        # print(next_ss)
        s = s[0] # take the sequence id, index is only to create mutliple sums for different infosets player can get to
        if len(next_ss) != 0:
            m.addConstr(sum(map(lambda ns: prob_vars[ns], next_ss)) == prob_vars[s])
    # player is 0 or 1, just like the root seq id
    m.addConstr(prob_vars[player] == 1)

    def compute_constraint(sum_elems):
        res = 0
        for seq_id, prob, g_val in sum_elems:
            if seq_id is None:
                infoset_id = g_val
                # print(infoset_id)
                res += val_vars[infoset_id] #* prob
            else:
                res += prob_vars[seq_id] * prob * g_val
        return res

    # for each sequence of other player
    # create one constraint
    val_vars = {}
    for infoset_id, action in sum_constraints.keys():
        if infoset_id is not None and infoset_id not in val_vars:
            val_vars[infoset_id] = m.addVar(name=f"val_{infoset_id}")

    val_root = m.addVar(name="val_root")
    if player == 0:
        for parent, children in sum_constraints.items():
            if parent != (None, None):
                m.addConstr(compute_constraint(children) >= val_vars[parent[0]])
        m.addConstr(compute_constraint(sum_constraints[(None, None)]) >= val_root)
        m.setObjective(val_root, GRB.MAXIMIZE)
    else:
        for parent, children in sum_constraints.items():
            # print(parent, " children: ", children)
            if parent != (None, None):
                m.addConstr(compute_constraint(children) <= val_vars[parent[0]])
        m.addConstr(compute_constraint(sum_constraints[(None, None)]) <= val_root)
        m.setObjective(val_root, GRB.MINIMIZE)

    m.optimize()
    # print()
    # print()
    # print()
    # m.display()

    # for v in m.getVars():
    #     print(f"{v.varName} = {v.x}")

    # I minimize the first player's utility, thus for the second player i must return the negative value
    return m.ObjVal if player == 0 else -m.ObjVal


def build_lp(h, curr_seq, prob, player, sequences, sum_constraints, next_seqs, id_counter):
    # chance nodes, terminals
    t = h.type()
    if t == HistoryType.terminal:
        o_player = (player + 1) % 2
        constr_id = curr_seq[o_player][-1]
        if constr_id not in sum_constraints:
            sum_constraints[constr_id] = []
        seq_id = sequences[player][curr_seq[player]]
        # sum_constraints[constr_id].append((seq_id, prob, -2 * (player - 1/2) * h.utility()))
        sum_constraints[constr_id].append((seq_id, prob, h.utility())) # there can be more with same seq id, if the previous is chance node

    elif t == HistoryType.chance:
        actions = h.actions()
        for a in actions:
            next_prob = h.chance_prob(a) * prob
            id_counter = build_lp(h.child(a), curr_seq, next_prob, player, sequences, sum_constraints, next_seqs, id_counter)

    else:
        curr_player = int(h.current_player())
        actions = h.actions()
        info_idx = h.infoset().index()
        # print(actions)

        for a_id, a in enumerate(actions):
            # before entering next history add it to next seqs, sum const etc...
            next_p_seq = deepcopy(curr_seq[curr_player])
            next_p_seq.append((info_idx, a_id))
            if next_p_seq not in sequences[curr_player]:
                sequences[curr_player][next_p_seq] = id_counter
                if curr_player == player:
                    seq_id = sequences[player][curr_seq[player]]
                    # print(seq_id, "adding", id_counter, "c_seq", curr_seq[player].seq, curr_player, a)
                    # for ns, val in sequences[0].items():
                    #     print(ns.seq, "->", val)
                    # for ns, val in sequences[1].items():
                    #     print(ns.seq, "->", val)
                    # for ns in next_seqs:
                    #     print(ns, end=" ")
                    # print()
                    if (seq_id, info_idx) not in next_seqs:
                        next_seqs[(seq_id, info_idx)] = []
                    next_seqs[(seq_id, info_idx)].append(id_counter)
                    # next_seqs[id_counter] = []
                id_counter += 1
            next_seq = deepcopy(curr_seq)
            next_seq[curr_player] = next_p_seq
            next_h = h.child(a)
            # print(a)
            if curr_player != player:
                o_player = (player + 1) % 2
                if len(curr_seq[o_player]) == 0:
                    constr_id = (None, None)
                else:
                    constr_id = curr_seq[o_player][-1]
                    if constr_id not in sum_constraints:
                        sum_constraints[constr_id] = []
                # print(constr_id)
                if (None, prob, info_idx) not in sum_constraints[constr_id]:
                    sum_constraints[constr_id].append((None, prob, info_idx))#next_h.infoset().index()))
            # if next_h.type() == HistoryType.decision:
            #     # if int(next_h.current_player()) == player:
            #     #     seq_id = sequences[player][curr_seq[player]]
            #     #     print(seq_id, "adding", id_counter+1, "c_seq", curr_seq[player].seq, curr_player, a)
            #     #     for ns, val in sequences[0].items():
            #     #         print(ns.seq, "->", val)
            #     #     for ns, val in sequences[1].items():
            #     #         print(ns.seq, "->", val)
            #     #     for ns in next_seqs:
            #     #         print(ns, end=" ")
            #     #     print()
            #     #     next_seqs[seq_id].append(id_counter+1)
            #     #     next_seqs[id_counter+1] = []
            #     if int(next_h.current_player()) != player:
            #     # else:
            #         o_player = (player + 1) % 2
            #         if len(curr_seq[o_player]) == 0:
            #             constr_id = (None, None)
            #         else:
            #             constr_id = curr_seq[o_player][-1]
            #         if constr_id not in sum_constraints:
            #             sum_constraints[constr_id] = []
            #         sum_constraints[constr_id].append((None, prob, next_h.infoset().index()))
            id_counter = build_lp(next_h, next_seq, prob, player, sequences, sum_constraints, next_seqs, id_counter)

    return id_counter


########### Do not modify code below.

if __name__ == '__main__':
    # read input specification in the body of this function
    root_history = create_root()
    # additionally specify for which player it should be solved
    # import sys
    # player = int(sys.argv[1])
    player = int(input())
    # print(export_gambit(root_history))

    print(root_value(root_history, player))
