"""Module for model augmented prefix tree acceptor and consistency graphs.

See Heule, "Exact DFA Identification Using SAT Solve" for details.
"""
from __future__ import annotations
from itertools import chain, combinations
from typing import Any, Iterable, Tuple

import attr
import networkx as nx
import funcy as fn
from bidict import bidict


Word = list[Any]
Node = Any


def transition(tree: nx.DiGraph, node: Node, char: Any) -> Node:
    for node in tree.neighbors(node):
        if tree.nodes[node]['source'] == char:
            return node


@attr.s(auto_detect=True, auto_attribs=True, frozen=True)
class APTA:
    """Augmented Prefix Tree Acceptor."""
    tree: nx.DiGraph
    alphabet: bidict  # Mapping from token to int.
    ord_prefs: set[Tuple[Node, Node]]  # MemReP 'ordered' preferences (less_preferred_word, more_preferred_word)
    eq_prefs: set[Tuple[Node, Node]]  # MemReP 'equivalent' preferences (equiv_word_1, equiv_word_2)

    @property
    def nodes(self) -> Iterable[Node]:
        return self.tree.nodes

    @property
    def root(self) -> Node:
        return 0

    @property
    def accepting(self) -> set[Node]:
        return {n for n, d in self.nodes(data=True) if d.get('label')}

    @property
    def rejecting(self) -> set[Node]:
        nodes = self.nodes(data=True)
        return {n for n, d in nodes if not d.get('label', True)}

    @property
    def ordered_preferences(self) -> set[Tuple[Node, Node]]:
        return self.ord_prefs

    @property
    def equivalent_preferences(self) -> set[Tuple[Node, Node]]:
        return self.eq_prefs

    @staticmethod
    def from_examples(
            accepting: list[Word],
            rejecting: list[Word],
            ordered_preference_words: list[Tuple[Word, Word]] = None,
            equivalent_preference_words: list[Tuple[Word, Word]] = None,
            alphabet: frozenset = None) -> APTA:
        # If preference tuples weren't provided, initialize them as empty lists
        if ordered_preference_words is None:
            ordered_preference_words = []
        if equivalent_preference_words is None:
            equivalent_preference_words = []
        """Return Augmented Prefix Tree Automata for accepting, rejecting."""
        # Create prefix tree.
        tree, root = nx.prefix_tree(chain(accepting, rejecting, list(chain(*ordered_preference_words)),
                                    list(chain(*equivalent_preference_words)))), 0
        tree.remove_node(-1)  # <-- sink node added by nx.

        def access(word: Word) -> Node:
            node = root
            for char in word:  # Walk tree for node accessed by word.
                node = transition(tree, node, char)
            return node

        # Augment tree with node labels.
        for label, words in [(True, accepting), (False, rejecting)]:
            for word in words:
                tree.nodes[access(word)]['label'] = label

        # Build the ordered preferences tuple set.
        ordered_preference_nodes = set()
        for (word_one, word_two) in ordered_preference_words:
            ordered_preference_nodes.add((access(word_one), access(word_two)))

        # Build the incomparable preference tuple set.
        equivalent_preference_nodes = set()
        for (word_one, word_two) in equivalent_preference_words:
            equivalent_preference_nodes.add((access(word_one), access(word_two)))

        # Label nodes with integers. With root = 0.
        relabels = {n: i + 1 for i, n in enumerate(set(tree.nodes) - {root})}
        relabels[root] = 0
        nx.relabel_nodes(tree, relabels, copy=False)

        # Construct alphabet for DFA.
        alphabet2 = {d['source'] for n, d in tree.nodes(data=True) if n != 0}
        if (alphabet is not None):
            if alphabet2 - alphabet:
                raise ValueError("Symbols in examples not in alphabet")
            alphabet |= alphabet2
        else:
            alphabet = alphabet2

        if None in alphabet:
            raise ValueError("None not allowed in alphabet.")

        # If possible, respect the alphabet's predefined ordering.
        try:
            alphabet = sorted(alphabet)
        except Exception:
            pass

        alphabet = bidict(enumerate(alphabet)).inv

        return APTA(tree, alphabet, ordered_preference_nodes, equivalent_preference_nodes)

    def consistency_graph(self) -> nx.Graph:
        """Return consistency graph for APTA via repeated DFS."""
        graph = nx.Graph()
        graph.add_nodes_from(self.tree.nodes)
        for pair in combinations(self.tree.nodes, 2):
            if not self._can_merge(graph, pair):
                graph.add_edge(*pair)
        return graph

    def _can_merge(self, graph: nx.Graph, pair: tuple[Node, Node]) -> bool:
        succ = self.tree.neighbors
        nodes = self.tree.nodes

        stack, visited = [pair], set()
        while stack:  # DFS for inconsistency in states.
            left, right = stack.pop()

            if (left, right) in visited:
                continue
            visited.add((left, right))

            if (left, right) in graph.edges:
                return False  # Reached known distinguished nodes.

            left_lbl = nodes[left].get('label')
            right_lbl = nodes[right].get('label')
            if None not in {left_lbl, right_lbl} and left_lbl != right_lbl:
                return False  # Discovered distiguishing path.

            # Group neighbors by access token.
            succ_left = {nodes[n]['source']: n for n in succ(left)}
            succ_right = {nodes[n]['source']: n for n in succ(right)}
            merged = list(fn.merge_with(set, succ_left, succ_right).values())

            # Interchange pair[0] and pair[1] is applicable.
            for p1, p2 in [pair, pair[::-1]]:
                merged.extend([(p | {p1}) - {p2} for p in merged if p2 in p])

            # Add un-reconciled successors to stack.
            stack.extend([p for p in merged if len(p) == 2])

        return True


__all__ = ['APTA', 'Node', 'Word']
