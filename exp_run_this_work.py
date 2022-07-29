from decompose import find_dfa_decompositions, enumerate_pareto_frontier
from dfa_identify import find_dfas
from dfa import dict2dfa, DFA, draw
import itertools
import time
import signal
import math
import random
import sys

TIMEOUT_SECONDS = 10 * 60 # Timeout after 10 minutes

class TimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeOutException()

def generate_examples(n_tasks: int,
                      n_subtasks: int,
                      bound: int):

    assert n_tasks > 1
    assert n_subtasks > 1
    assert bound % 2 == 0 and bound > 0

    symbol_base = 'x'
    symbol_counter = 0
    tasks_symbols = []
    tasks_symbols_flatten = []

    for _ in range(n_tasks):
        task_symbols = []
        for _ in range(n_subtasks):
            task_symbols.append(symbol_base + str(symbol_counter))
            symbol_counter += 1
        tasks_symbols.append(task_symbols)
        tasks_symbols_flatten.extend(task_symbols)

    positive_examples = []
    while len(positive_examples) < bound // 2:
        positive_example_heads = [0] * n_tasks
        trace = []
        while not all(symbol in trace for symbol in tasks_symbols_flatten):
            random_head_idx = random.randint(0, n_tasks - 1)
            trace.append(tasks_symbols[random_head_idx][positive_example_heads[random_head_idx]])
            positive_example_heads[random_head_idx] += 1
            positive_example_heads[random_head_idx] %= n_subtasks
        if trace not in positive_examples:
            positive_examples.append(trace)

    negative_examples = []
    while len(negative_examples) < bound // 2:
        negative_example_heads = [n_subtasks - 1] * n_tasks
        trace = []
        while not all(symbol in trace for symbol in tasks_symbols_flatten):
            random_head_idx = random.randint(0, n_tasks - 1)
            trace.append(tasks_symbols[random_head_idx][negative_example_heads[random_head_idx]])
            negative_example_heads[random_head_idx] += n_subtasks - 1
            negative_example_heads[random_head_idx] %= n_subtasks
        if trace not in negative_examples:
            negative_examples.append(trace)

    assert len(positive_examples) == bound // 2 and len(negative_examples) == bound // 2

    return positive_examples, negative_examples

def get_next_solution_and_check(generator, accepting, rejecting, is_monolithic):
    start_time = time.time()
    result = next(generator)
    end_time = time.time()
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

def exp_run_this_work(seed, n_syms, n_dfas, n_examples):

    random.seed(seed)

    signal.alarm(0)
    assert signal.alarm(0) == 0

    accepting, rejecting = generate_examples(n_dfas, n_syms, n_examples)
    this_work_generator = enumerate_pareto_frontier(accepting, rejecting, n_dfas, order_by_stutter=True)

    start = time.time()
    signal.alarm(TIMEOUT_SECONDS)
    try:
        result = get_next_solution_and_check(this_work_generator, accepting, rejecting, False)
    except TimeOutException:
        end = time.time()
        print('Timedout after', end - start, 'seconds')
        result = None
    signal.alarm(0)
    assert signal.alarm(0) == 0
    print('This Work', (n_syms, n_dfas, n_examples), result)

    f = open('exp_results/exp_this_work_seed' + str(seed) + '_n_syms' + str(n_syms) + '_n_dfas' + str(n_dfas) + '_n_examples' + str(n_examples) + '_results.csv', 'w+')
    f.write('n_syms,n_dfas,n_examples,time\n')
    f.write(str(n_syms) + ',' + str(n_dfas) + ',' + str(n_examples) + ',' + str(result) + '\n')
    f.close()

if __name__ == '__main__':

    default_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(default_recursion_limit**2)

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(0)
    assert signal.alarm(0) == 0

    seed = int(sys.argv[1])
    n_syms = int(sys.argv[2])
    n_dfas = int(sys.argv[3])
    n_examples = int(sys.argv[4])

    exp_run_this_work(seed, n_syms, n_dfas, n_examples)

    sys.setrecursionlimit(default_recursion_limit)
