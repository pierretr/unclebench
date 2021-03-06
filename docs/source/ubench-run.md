% ubench-run(1)

# NAME


ubench-run -  Run benchmarks

# SYNOPSIS


    ubench run -p <platform> -b <bench> [<bench> ...] [-w <W> [<W> ...]]\
    [-customp <param>:<new_value> [<param>:<new_value> ...]]

    ubench run -h

# DESCRIPTION


*ubench run*  execute benchmarks with given platform settings.

# OPTIONS


# -p <platform>
  Name of the configuration that prodives platform settings needed to run the benchmark.


# -b <bench> [<bench> ...]
  Names of the benchmarks to run.


# -w <W> [<W> ...]
  Nodes on which benchmarks should be run ex: -w 6 cn184 cn[380,431-433] would\
  run the benchmark on three different configurations (6 available nodes, one node\
  named cn184 and four nodes named cn[380,431-433]). You can also launch a job on all idle nodes\
  ex : -w all4 to launch a benchmark with 4 nodes jobs covering evry idle node.


# -customp <CUSTOMP> [<CUSTOMP> ...]
  Modify a benchmark parameter on command line.\
  ex: -customp mpi_v:1 would launch a benchmark with the mpi_v parameter set to 1.
  

# ENVIRONMENT


## UBENCH_PLATFORM_DIR
   **default :** /usr/share/unclebench/platform
   Path to platform files.


## UBENCH_BENCHMARK_DIR
   **default :** /usr/share/unclebench/benchmarks'
   Path where the benchmark configuration files are located.


## UBENCH_RUN_DIR_BENCH
   **default :** /scratch/<user>/Ubench/benchmarks
   Path where benchmarks are executed.


## UBENCH_RESOURCE_DIR
   **default :** /scratch/<user>/Ubench/resource
   Path where ubench can find the benchmark resource files.

# SEE ALSO

ubench-fetch(1), ubench-result(1), ubench-list(1), ubench-log(1), ubench-report(1), ubench-listparams(1)