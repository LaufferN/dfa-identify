# n_syms 2, n_examples 10
for seed in {1..10}
do
    for n_dfas in {2..12}
    do
       poetry run python exp_run_baseline.py ${seed} 2 ${n_dfas} 10
       poetry run python exp_run_this_work.py ${seed} 2 ${n_dfas} 10
       poetry run python exp_run_baseline.py ${seed} 4 ${n_dfas} 10
    done
done

# n_syms 4, n_examples 10
for seed in {1..10}
do
    for n_dfas in {2..9}
    do
       poetry run python exp_run_this_work.py ${seed} 4 ${n_dfas} 10
    done
done

# n_syms 2, n_dfas 4
for seed in {1..10}
do
    for n_examples in `seq 20 10 70`
    do
       poetry run python exp_run_baseline.py ${seed} 2 4 ${n_examples}
       poetry run python exp_run_this_work.py ${seed} 2 4 ${n_examples}
    done
done

# n_syms 4, n_dfas 2
for seed in {1..10}
do
    for n_examples in `seq 20 10 200`
    do
       poetry run python exp_run_baseline.py ${seed} 4 2 ${n_examples}
       poetry run python exp_run_this_work.py ${seed} 4 2 ${n_examples}
    done
done

# n_syms 4, n_dfas 4
for seed in {1..10}
do
    for n_examples in `seq 20 10 30`
    do
       poetry run python exp_run_baseline.py ${seed} 4 4 ${n_examples}
       poetry run python exp_run_this_work.py ${seed} 4 4 ${n_examples}
    done
done
