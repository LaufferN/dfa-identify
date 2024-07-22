from functools import cache
from itertools import combinations_with_replacement

import funcy as fn
from functools import reduce
import operator as op
from dfa_identify.identify import find_dfas
from dfa_identify.decomposed import find_decomposed_dfas


def all_words(alphabet):
    """Enumerates all words in the alphabet."""
    n = 0
    while True:
        yield from combinations_with_replacement(alphabet, n)
        n += 1


def distinguishing_query(positive, negative, alphabet):
    """Return a string that seperates the two smallest (consistent) DFAs."""
    candidates = find_dfas(positive, negative, alphabet=alphabet)
    lang1 = next(candidates)

    # DFAs may represent the same language. Filter those out.
    candidates = (c for c in candidates if lang1 != c)
    lang2 = next(candidates, None)

    # Try to find a seperating word.
    if (lang1 is not None) and (lang2 is not None):
        return tuple((lang1 ^ lang2).find_word(True))

    # TODO: due to  a bug in dfa-identify allow_unminimized doesn't always work
    # so we need to come up with a word that is not in positive/negative but is
    # not constrained by positive / negative.
    constrained = set(positive) | set(negative)
    return fn.first(w for w in all_words(alphabet) if w not in constrained)


def find_dfa_decomposition(monolithic_dfa, alphabet, n_dfas, n_queries=10, n_init_examples=10):
    """
    Returns an iterator of cDFAs consistent with a monolithic DFA.
    """
    positive = []
    negative = []
    for word, _ in zip(all_words(alphabet), range(n_init_examples)):
        label = monolithic_dfa.label(word)
        if label is True:    positive.append(word)
        elif label is False: negative.append(word)

    cdfa_gen = find_decomposed_dfas(positive, negative, n_dfas, alphabet=alphabet)

    # 1. Ask membership queries that distiguish remaining candidates.
    for _ in range(n_queries):
        candidate_cdfa = next(cdfa_gen)
        candidate_mono = reduce(op.and_, candidate_cdfa)

        assert all(candidate_mono.label(w) for w in positive)
        assert not any(candidate_mono.label(w) for w in negative)

        sym_diff = (candidate_mono ^ monolithic_dfa)
        dist_word = sym_diff.find_word(True)
        if dist_word is None:
            # we found equiv cdfa
            # yield candidate_cdfa
            pass
        else:
            label = monolithic_dfa.label(tuple(dist_word))
            if label is True:    positive.append(dist_word)
            elif label is False: negative.append(dist_word)
            # recreate generator with example set
            cdfa_gen = find_decomposed_dfas(positive, negative, n_dfas, alphabet=alphabet)

    def check_equiv(cdfa):
        return reduce(op.and_, cdfa) == monolithic_dfa

    kwargs = {}
    # kwargs.setdefault('order_by_stutter', True)
    # kwargs.setdefault('allow_unminimized', True)
    yield from filter(check_equiv, find_decomposed_dfas(positive, negative, n_dfas, alphabet=alphabet, **kwargs))



def find_dfas_active(alphabet, oracle, n_queries,
                     positive=(), negative=(), **kwargs):
    """
    Returns an iterator of DFAs consistent with passively and actively
    collected examples.

    SAT based version space learner that actively queries the oracle
    for a string that distinguishes two "minimal" DFAs, where
    minimal is lexicographically ordered in (#states, #edges).

    - positive, negative: set of accepting and rejecting words.
    - oracle: Callable taking in a word and returning {True, False, None}.
              If None, then no constraint is added.
    - n_queries: Number of queries to ask the oracle.
    - additional kwargs are passed to find_dfas.
    """
    positive, negative = list(positive), list(negative)

    # 1. Ask membership queries that distiguish remaining candidates.
    for _ in range(n_queries):
        word = distinguishing_query(positive, negative, alphabet)

        label = oracle(word)
        if label is True:    positive.append(word)
        elif label is False: negative.append(word)
        else: assert label is None  # idk case.

    # 2. Return minimal consistent DFA.
    kwargs.setdefault('order_by_stutter', True)
    kwargs.setdefault('allow_unminimized', True)
    yield from find_dfas(positive, negative, alphabet=alphabet, **kwargs)


def find_dfa_active(alphabet, oracle, n_queries,
                    positive=(), negative=(), **kwargs):
    """
    Returns minimal DFA consistent with passively and actively collected
    examples.

    SAT based version space learner that actively queries the oracle
    for a string that distinguishes two "minimal" DFAs, where
    minimal is lexicographically ordered in (#states, #edges).

    - positive, negative: set of accepting and rejecting words.
    - oracle: Callable taking in a word and returning {True, False, None}.
              If None, then no constraint is added.
    - n_queries: Number of queries to ask the oracle.
    - additional kwargs are passed to find_dfas.
    """
    dfas = find_dfas_active(positive=positive,
                            negative=negative,
                            alphabet=alphabet,
                            oracle=oracle,
                            n_queries=n_queries,
                            **kwargs)
    return fn.first(dfas)


__all__ = ['find_dfas_active',
           'find_dfa_active',
           'find_dfa_decomposition',
           'all_words',
           'distinguishing_query']
