#!/bin/ksh

# First function to test
function test_func1 {
    # Replace with your first function
    for i in {1..1000}; do
        echo "test" > /dev/null
    done
}

# Second function to test
function test_func2 {
    # Replace with your second function
    for i in $(seq 1 1000); do
        echo "test" > /dev/null
    done
}

# Benchmark function
function benchmark {
    typeset func_name=$1
    typeset iterations=$2
    typeset start_time end_time total_time
    
    start_time=$(date +%s.%N)
    
    for ((i=1; i<=iterations; i++)); do
        eval $func_name
    done
    
    end_time=$(date +%s.%N)
    total_time=$(printf "%.3f" $(echo "$end_time - $start_time" | bc))
    
    echo "$func_name took $total_time seconds for $iterations iterations"
}

# Number of times to run each function
iterations=10

# Run benchmarks
benchmark test_func1 $iterations
benchmark test_func2 $iterations

# Calculate average time per iteration
