import operator as op
from functools import reduce

import funcy as fn
from pysat.solvers import Glucose4

from dfa_identify import decomposed
from dfa_identify.active import find_dfa_decomposition
from dfa_identify.identify import find_models
from dfa_identify.graphs import APTA

def test_smoke():
    apta = APTA.from_examples(
        accepting=['a', 'abaa', 'bb'],
        rejecting=['abb', 'b'],
    )

    codec = decomposed.ConjunctiveCodec.from_apta(apta, (2,3))
    clauses = list(codec.clauses())
    assert len(clauses) > 0

    accepting = ['a', 'abaa', 'bb']
    rejecting = ['abb', 'b']

    sub_codec, sub_model = next(find_models(accepting=accepting,
                                            rejecting=rejecting))

    codec = decomposed.ConjunctiveCodec.from_apta(sub_codec.apta,
                                                  (sub_codec.n_colors, sub_codec.n_colors))
    sub_model2 = decomposed.offset_lits(sub_model, sub_codec.max_id)
    dfas = codec.interpret_model(sub_model + sub_model2)
    assert len(dfas) == 2
    assert dfas[0] == dfas[1]

    with Glucose4(bootstrap_with=codec.clauses()) as solver:
        if not solver.solve():
            return
        model = solver.get_model()

    decomposed_dfas = codec.interpret_model(model)
    monolithic_dfa = reduce(op.and_, dfas)
    assert all(monolithic_dfa.label(w) for w in accepting)
    assert not any(monolithic_dfa.label(w) for w in rejecting)

    dfas = next(decomposed.find_decomposed_dfas(accepting=accepting,
                                                rejecting=rejecting,
                                                n_dfas=2))
    monolithic_dfa = reduce(op.and_, dfas)
    assert all(monolithic_dfa.label(w) for w in accepting)
    assert not any(monolithic_dfa.label(w) for w in rejecting)
    sizes = [len(d.states()) for d in dfas]
    assert all(s1 < s2 for s1, s2 in fn.pairwise(sizes))


def test_fmcad_21_example():
    accepting = ['y', 'yy', 'gy', 'bgy', 'bbgy', 'bggy']
    rejecting = ['', 'r', 'ry', 'by', 'yr', 'gr', 'rr', 'rry', 'rygy']
    dfas = next(decomposed.find_decomposed_dfas(accepting=accepting,
                                                rejecting=rejecting,
                                                n_dfas=2,
                                                order_by_stutter=True))

    monolithic_dfa = reduce(op.and_, dfas)
    assert all(monolithic_dfa.label(w) for w in accepting)
    assert not any(monolithic_dfa.label(w) for w in rejecting)

    sizes = [len(d.states()) for d in dfas]
    assert all(s1 < s2 for s1, s2 in fn.pairwise(sizes))
    assert sizes == [2, 3]


def test_disjunction():
    accepting = ['y', 'yy', 'gy', 'bgy', 'bbgy', 'bggy']
    rejecting = ['', 'r', 'ry', 'by', 'yr', 'gr', 'rr', 'rry', 'rygy']

    gen_dfas = decomposed.find_decomposed_dfas(accepting=accepting,
                                               rejecting=rejecting,
                                               n_dfas=2,
                                               order_by_stutter=True,
                                               decompose_via="disjunction")

    dfas = next(gen_dfas)
    monolithic_dfa = reduce(op.or_, dfas)
    assert all(monolithic_dfa.label(w) for w in accepting)
    assert not any(monolithic_dfa.label(w) for w in rejecting)
    # Each dfa must reject a rejecting string.
    assert all(all(~d.label(w) for d in dfas) for w in rejecting)
    # At least one dfa must accept an accepting string.
    assert all(any(d.label(w) for d in dfas) for w in accepting)


def test_decompose_from_monolithic():
    alphabet = {'r', 'g', 'b', 'y'}
    accepting = ['y', 'yy', 'gy', 'bgy', 'bbgy', 'bggy']
    rejecting = ['', 'r', 'ry', 'by', 'yr', 'gr', 'rr', 'rry', 'rygy']
    dfas = next(decomposed.find_decomposed_dfas(accepting=accepting,
                                                rejecting=rejecting,
                                                n_dfas=2,
                                                order_by_stutter=True))

    monolithic_dfa = reduce(op.and_, dfas)

    decomp_size = 2
    n_queries=20
    n_init_examples=10
    decomps = find_dfa_decomposition(monolithic_dfa, alphabet, decomp_size, n_queries, n_init_examples)
    num_dfas = 10
    for cdfa, _ in zip(decomps, range(num_dfas)):
        dfa = reduce(op.and_, cdfa)
        assert dfa == monolithic_dfa


if __name__ == '__main__':
    test_decompose_from_monolithic()