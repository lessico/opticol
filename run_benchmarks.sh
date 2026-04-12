#!/usr/bin/env bash
set -euo pipefail

# Run all benchmarks one operation at a time to avoid OOM.
# Results are saved under .benchmarks/ by pytest-benchmark.
#
# Usage: ./run_benchmarks.sh <prefix>
# Example: ./run_benchmarks.sh main

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <prefix>" >&2
    exit 1
fi

PREFIX="$1"

# --- set immutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[set_immutable_.*\]"     --benchmark-save="${PREFIX}-set-immutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_contains\[set_immutable_.*\]" --benchmark-save="${PREFIX}-set-immutable-contains"
pytest benchmarks/ --benchmark-only --regex ".*bench_iter\[set_immutable_.*\]"     --benchmark-save="${PREFIX}-set-immutable-iter"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[set_immutable_.*\]"      --benchmark-save="${PREFIX}-set-immutable-len"

# --- set mutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[set_mutable_.*\]"       --benchmark-save="${PREFIX}-set-mutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_contains\[set_mutable_.*\]"   --benchmark-save="${PREFIX}-set-mutable-contains"
pytest benchmarks/ --benchmark-only --regex ".*bench_iter\[set_mutable_.*\]"       --benchmark-save="${PREFIX}-set-mutable-iter"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[set_mutable_.*\]"        --benchmark-save="${PREFIX}-set-mutable-len"
pytest benchmarks/ --benchmark-only --regex ".*bench_add\[set_mutable_.*\]"        --benchmark-save="${PREFIX}-set-mutable-add"
pytest benchmarks/ --benchmark-only --regex ".*bench_discard\[set_mutable_.*\]"    --benchmark-save="${PREFIX}-set-mutable-discard"

# --- sequence immutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[sequence_immutable_.*\]"    --benchmark-save="${PREFIX}-sequence-immutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_getitem\[sequence_immutable_.*\]" --benchmark-save="${PREFIX}-sequence-immutable-getitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[sequence_immutable_.*\]"     --benchmark-save="${PREFIX}-sequence-immutable-len"

# --- sequence mutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[sequence_mutable_.*\]"    --benchmark-save="${PREFIX}-sequence-mutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_getitem\[sequence_mutable_.*\]" --benchmark-save="${PREFIX}-sequence-mutable-getitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[sequence_mutable_.*\]"     --benchmark-save="${PREFIX}-sequence-mutable-len"
pytest benchmarks/ --benchmark-only --regex ".*bench_setitem\[sequence_mutable_.*\]" --benchmark-save="${PREFIX}-sequence-mutable-setitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_delitem\[sequence_mutable_.*\]" --benchmark-save="${PREFIX}-sequence-mutable-delitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_insert\[sequence_mutable_.*\]"  --benchmark-save="${PREFIX}-sequence-mutable-insert"

# --- mapping immutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[mapping_immutable_.*\]"    --benchmark-save="${PREFIX}-mapping-immutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_getitem\[mapping_immutable_.*\]" --benchmark-save="${PREFIX}-mapping-immutable-getitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_iter\[mapping_immutable_.*\]"    --benchmark-save="${PREFIX}-mapping-immutable-iter"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[mapping_immutable_.*\]"     --benchmark-save="${PREFIX}-mapping-immutable-len"

# --- mapping mutable ---
pytest benchmarks/ --benchmark-only --regex ".*bench_init\[mapping_mutable_.*\]"    --benchmark-save="${PREFIX}-mapping-mutable-init"
pytest benchmarks/ --benchmark-only --regex ".*bench_getitem\[mapping_mutable_.*\]" --benchmark-save="${PREFIX}-mapping-mutable-getitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_iter\[mapping_mutable_.*\]"    --benchmark-save="${PREFIX}-mapping-mutable-iter"
pytest benchmarks/ --benchmark-only --regex ".*bench_len\[mapping_mutable_.*\]"     --benchmark-save="${PREFIX}-mapping-mutable-len"
pytest benchmarks/ --benchmark-only --regex ".*bench_setitem\[mapping_mutable_.*\]" --benchmark-save="${PREFIX}-mapping-mutable-setitem"
pytest benchmarks/ --benchmark-only --regex ".*bench_delitem\[mapping_mutable_.*\]" --benchmark-save="${PREFIX}-mapping-mutable-delitem"
