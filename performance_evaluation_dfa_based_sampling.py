from decompose import find_dfa_decompositions, enumerate_pareto_frontier
from dfa_identify import find_dfas
from dfa import dict2dfa, DFA, draw, dfa2dict
from dfa.utils import words, find_word, paths, minimize
import itertools
import time
import signal
import math
from functools import reduce
import funcy as fn
import networkx as nx

TIMEOUT_SECONDS = 10 * 60 # Timeout after 10 minutes

class TimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeOutException()

dfa_cache = {}

def generate_examples(n_tasks: int,
                      n_subtasks: int,
                      bound: int):

    assert n_tasks > 0
    assert n_subtasks > 1
    assert bound % 2 == 0 and bound > 0

    symbol_base = 'x'
    symbol_counter = 0
    tasks_symbols = []
    tasks_symbols_flatten = []
    dfas = []
    nxgs = []

    temp = None
    a = None
    for i in range(n_tasks, -1, -1):
        try:
            temp = dfa_cache[(i, n_subtasks)]
            a = i
            print('Found!', i, n_subtasks)
            break
        except:
            pass
    if temp == None:
        print('Generating DFAs')
        for _ in range(n_tasks):
            task_symbols = []
            nxg = nx.MultiDiGraph()
            nxg.add_node(0, label=False)
            for node in range(1, n_subtasks + 1):
                nxg.add_node(node, label=True if node == n_subtasks else False)
                nxg.add_edge(node - 1, node, label=symbol_base + str(symbol_counter))
                # task_symbols.append(symbol_base + str(symbol_counter))
                symbol_counter += 1
                # tasks_symbols.append(task_symbols)
                # tasks_symbols_flatten.extend(task_symbols)
            nxgs.append(nxg)
        print('Done generating DFAs')

        print('Generating DFA product')
        temp = nxgs[0]
        for temp2 in nxgs[1:]:
            temp = nx.cartesian_product(temp, temp2)
    # print(temp)
    # for e in temp.edges:
    #     print(e, temp.edges[e])
    # for n in temp.nodes:
    #     print(n, temp.nodes[n])
        print('Done generating DFA product')
    # input()
    else:
        symbol_counter = a*n_subtasks
        for _ in range(a, n_tasks):
            task_symbols = []
            nxg = nx.DiGraph()
            nxg.add_node(0, label=False)
            for node in range(1, n_subtasks + 1):
                nxg.add_node(node, label=True if node == n_subtasks else False)
                nxg.add_edge(node - 1, node, label=symbol_base + str(symbol_counter))
                # task_symbols.append(symbol_base + str(symbol_counter))
                symbol_counter += 1
                # tasks_symbols.append(task_symbols)
                # tasks_symbols_flatten.extend(task_symbols)
            temp = nx.cartesian_product(temp, nxg)

    dfa_cache[(n_tasks, n_subtasks)] = temp

    # for task_symbols in tasks_symbols:
    #     dfa_dict = {}
    #     for i in range(n_subtasks):
    #         dfa_dict[i] = (False, {sym: i + 1 if sym == task_symbols[i] else i for sym in tasks_symbols_flatten})
    #     dfa_dict[n_subtasks] = (True, {sym: n_subtasks for sym in tasks_symbols_flatten})
    #     dfas.append(dict2dfa(dfa_dict, start=0))

    # print('Generating DFA product')
    # dfa = reduce(lambda x, y: x & y, dfas)
    # # dfa = minimize(dfa)
    # # end = next(s for s in dfa.states() if dfa._label(s))
    # dfa_dict, init_node = dfa2dict(dfa)
    # print('Done generating DFA product')

    # nxg = nx.MultiDiGraph()
    # accepting_states = []
    # for start, (accepting, transitions) in dfa_dict.items():
    #     # pydot_graph.add_node(nodes[start])
    #     start = str(start)
    #     nxg.add_node(start)
    #     if accepting:
    #         accepting_states.append(start)
    #     for action, end in transitions.items():
    #         nxg.add_edge(start, str(end), label=action)
    accepting = []
    print('Collecting accepting strings')
    # print((0,) * n_tasks)
    # print((n_subtasks,) * n_tasks)
    # print(temp.nodes)
    init_state = 0
    for _ in range(1, n_tasks):
        init_state = (init_state,) + (0,)
    acceptting_state = n_subtasks
    for _ in range(n_tasks):
        acceptting_state = (acceptting_state,) + (n_subtasks,)
    for path in nx.all_simple_edge_paths(temp, init_state, acceptting_state):
        trace = [temp.edges[e]['label'] for e in path]
        # print(trace)
        accepting.append(trace)
        print(trace)
        if len(accepting) == bound:
            break
        # print(trace)
    print('Done collecting accepting strings')
        
    # input()
    # print('Done generating DFA product')
    # draw.write_dot(dfa, "temp.dot")

    # # print(1)
    # start = dfa.start
    # # print(2)

    # access_strings = paths(
    #     dfa, 
    #     start=start,
    #     randomize=True #  Randomize the order. Shorter paths still found first.
    # )
    # # print(3)
    # accepting = []
    # for _ in range(bound):
    #     # print(3.1)
    #     # print(len(dfa._states))
    #     trace = next(access_strings)
    #     # print(3.2)
    #     # print(trace)
    #     accepting.append(trace)
    #     # print(3.3)
    # # print(4)
    # # rejecting = list(set(fn.take(bound // 2, words(~dfa))))

    # assert len(accepting) == bound

    return accepting, []

def get_next_solution_and_check(generator, accepting, rejecting, is_monolithic):
    print('Hey')
    try:
        start_time = time.time()
        result = next(generator)
        end_time = time.time()
    except:
        return None
    if is_monolithic:
        assert all(result.label(x) for x in accepting)
        assert all(not result.label(x) for x in rejecting)
        # draw.write_dot(result, "temp.dot")
        # input('Done1')
    else:
        for my_dfa in result:
            assert all(my_dfa.label(x) for x in accepting)
            # draw.write_dot(my_dfa, "temp.dot")
            # input('Done2')
        for x in rejecting:
            assert any(not my_dfa.label(x) for my_dfa in result)
    return end_time - start_time

def exp_vary_dfas(n_syms, n_dfas_lower, n_dfas_upper, bound):
    baseline = {}
    this_work = {}

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(0)

    for n_dfas in range(n_dfas_lower, n_dfas_upper + 1):
        try:
            accepting, rejecting = generate_examples(n_dfas, n_syms, bound)
            baseline_generator = find_dfas(accepting, rejecting, order_by_stutter=True)
            signal.alarm(TIMEOUT_SECONDS)
            try:
                result = get_next_solution_and_check(baseline_generator, accepting, rejecting, True)
            except TimeOutException:
                result = None
            signal.alarm(0)
            baseline[(bound, n_syms, n_dfas)] = result
            print('Baseline', (bound, n_syms, n_dfas), baseline[(bound, n_syms, n_dfas)])
            this_work_generator = enumerate_pareto_frontier(accepting, rejecting, n_dfas, order_by_stutter=True)
            signal.alarm(TIMEOUT_SECONDS)
            try:
                result = get_next_solution_and_check(this_work_generator, accepting, rejecting, False)
            except TimeOutException:
                result = None
            signal.alarm(0)
            this_work[(bound, n_syms, n_dfas)] = result
            print('This Work', (bound, n_syms, n_dfas), this_work[(bound, n_syms, n_dfas)])
        except TimeOutException:
            pass
        signal.alarm(0)

    f = open('exp_vary_dfas_baseline_' + str(n_syms) + '_' + str(n_dfas_lower) + '_' + str(n_dfas_upper) + '_' + str(bound) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in baseline:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(baseline[result]) + '\n')
    f.close()

    f = open('exp_vary_dfas_this_work_' + str(n_syms) + '_' + str(n_dfas_lower) + '_' + str(n_dfas_upper) + '_' + str(bound) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in this_work:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(this_work[result]) + '\n')
    f.close()

def exp_vary_examples(n_syms, n_dfas, bound_lower, bound_upper, step=10):
    baseline = {}
    this_work = {}

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(0)

    for bound in range(bound_lower, bound_upper + 1, step):
        try:
            accepting, rejecting = generate_examples(n_dfas, n_syms, bound)
            baseline_generator = find_dfas(accepting, rejecting, order_by_stutter=True)
            signal.alarm(TIMEOUT_SECONDS)
            try:
                result = get_next_solution_and_check(baseline_generator, accepting, rejecting, True)
            except TimeOutException:
                result = None
            signal.alarm(0)
            baseline[(bound, n_syms, n_dfas)] = result
            print('Baseline', (bound, n_syms, n_dfas), baseline[(bound, n_syms, n_dfas)])
            this_work_generator = enumerate_pareto_frontier(accepting, rejecting, n_dfas, order_by_stutter=True)
            signal.alarm(TIMEOUT_SECONDS)
            try:
                result = get_next_solution_and_check(this_work_generator, accepting, rejecting, False)
            except TimeOutException:
                result = None
            signal.alarm(0)
            this_work[(bound, n_syms, n_dfas)] = result
            print('This Work', (bound, n_syms, n_dfas), this_work[(bound, n_syms, n_dfas)])
        except TimeOutException:
            pass
        signal.alarm(0)

    f = open('exp_vary_examples_baseline_' + str(n_syms) + '_' + str(n_dfas) + '_' + str(bound_lower) + '_' + str(bound_upper) + '_' + str(step) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in baseline:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(baseline[result]) + '\n')
    f.close()

    f = open('exp_vary_examples_this_work_' + str(n_syms) + '_' + str(n_dfas) + '_' + str(bound_lower) + '_' + str(bound_upper) + '_' + str(step) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in this_work:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(this_work[result]) + '\n')
    f.close()

def exp_vary_solutions(n_syms, n_dfas, bound, solutions=100):
    baseline = {}
    this_work = {}

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(0)

    accepting, rejecting = generate_examples(n_dfas, n_syms, bound)
    print(accepting)
    print(rejecting)
    baseline_generator = find_dfas(accepting, rejecting, order_by_stutter=True)
    this_work_generator = enumerate_pareto_frontier(accepting, rejecting, n_dfas, order_by_stutter=True)
    baseline_result = 0
    this_work_result = 0
    for solution in range(solutions):
        try:
            signal.alarm(TIMEOUT_SECONDS)
            try:
                baseline_result += get_next_solution_and_check(baseline_generator, accepting, rejecting, True)
            except TimeOutException:
                break
            signal.alarm(0)
            baseline[(bound, n_syms, n_dfas)] = baseline_result
            print('Baseline', (bound, n_syms, n_dfas, solution), baseline[(bound, n_syms, n_dfas)])
            signal.alarm(TIMEOUT_SECONDS)
            try:
                this_work_result += get_next_solution_and_check(this_work_generator, accepting, rejecting, False)
            except TimeOutException:
                break
            signal.alarm(0)
            this_work[(bound, n_syms, n_dfas)] = this_work_result
            print('This Work', (bound, n_syms, n_dfas, solution), this_work[(bound, n_syms, n_dfas)])
        except TimeOutException:
            pass
        signal.alarm(0)

    f = open('exp_vary_solutions_baseline_' + str(n_syms) + '_' + str(n_dfas) + '_' + str(bound) + '_' + str(solutions) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in baseline:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(baseline[result]) + '\n')
    f.close()

    f = open('exp_vary_solutions_this_work_' + str(n_syms) + '_' + str(n_dfas) + '_' + str(bound) + '_' + str(solutions) + '_results.csv', 'w+')
    f.write('bound,n_syms,n_dfas,time\n')
    for result in this_work:
        f.write(str(result[0]) + ',' + str(result[1]) + ',' + str(result[2]) + ',' + str(this_work[result]) + '\n')
    f.close()

if __name__ == '__main__':

    # generate_examples(2, 2, 100)

    exp_vary_dfas(2, 2, 10, 10)
    exp_vary_dfas(4, 1, 10, 10)
    exp_vary_dfas(8, 1, 10, 10)

    exp_vary_dfas(2, 1, 10, 100)
    exp_vary_dfas(4, 1, 10, 100)
    exp_vary_dfas(8, 1, 10, 100)

    exp_vary_examples(2, 2, 10, 100)
    exp_vary_examples(2, 4, 10, 100)
    exp_vary_examples(2, 8, 10, 100)

    exp_vary_examples(4, 2, 10, 100)
    exp_vary_examples(4, 4, 10, 100)
    exp_vary_examples(4, 8, 10, 100)

    exp_vary_examples(8, 2, 10, 100)
    exp_vary_examples(8, 4, 10, 100)
    exp_vary_examples(8, 8, 10, 100)

    exp_vary_solutions(2, 2, 10, 100)
    exp_vary_solutions(2, 4, 10, 100)
    exp_vary_solutions(2, 8, 10, 100)

    exp_vary_solutions(4, 2, 10, 100)
    exp_vary_solutions(4, 4, 10, 100)
    exp_vary_solutions(4, 8, 10, 100)

    exp_vary_solutions(8, 2, 10, 100)
    exp_vary_solutions(8, 4, 10, 100)
    exp_vary_solutions(8, 8, 10, 100)

