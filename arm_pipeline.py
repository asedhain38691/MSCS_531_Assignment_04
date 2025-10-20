from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.branch_predictors import OneBitBranchPredictor
from gem5.isas import ISA
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires
from m5.objects import Process
import os

# Function to run a simulation
def run_simulation(workload_cmd, cpu_config, output_dir):
    requires(isa_required=ISA.ARM)
    
    cache_hierarchy = NoCache()
    memory = SingleChannelDDR3_1600(size="32MiB")
    processor = SimpleProcessor(**cpu_config)
    
    board = SimpleBoard(
        clk_freq="1GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )
    
    # Workload assignment
    if isinstance(workload_cmd, list):
        # Multiple threads (SMT)
        threads = []
        for cmd in workload_cmd:
            proc = Process()
            proc.cmd = [cmd]
            threads.append(proc)
        board.set_se_multi_workload(threads)
    else:
        # Single thread
        process = Process()
        process.cmd = [workload_cmd]
        board.set_se_workload(process)
    
    sim = Simulator(board=board, output_dir=output_dir)
    sim.run()
    return output_dir

# Function to parse stats
def parse_stats(stats_dir):
    stats_file = os.path.join(stats_dir, "stats.txt")
    num_insts = sim_ticks = 0
    with open(stats_file) as f:
        for line in f:
            if line.startswith("system.cpu.num_insts"):
                num_insts = float(line.split()[1])
            elif line.startswith("sim_ticks"):
                sim_ticks = float(line.split()[1])
    ipc = num_insts / sim_ticks
    latency = sim_ticks / num_insts
    return num_insts, sim_ticks, ipc, latency

# Define workloads (compile these first for ARM)
single_thread_prog = "./test"
int_prog = "./int_test"
fp_prog = "./fp_test"
mem_prog = "./mem_test"

# CPU configurations
cpu_configs = {
    "single_issue": {"cpu_type": CPUTypes.TIMING, "isa": ISA.ARM, "num_cores": 1, "width": 1},
    "branch_pred": {"cpu_type": CPUTypes.TIMING, "isa": ISA.ARM, "num_cores": 1,
                    "width": 1, "branch_predictor": OneBitBranchPredictor()},
    "superscalar": {"cpu_type": CPUTypes.TIMING, "isa": ISA.ARM, "num_cores": 1,
                    "width": 4, "branch_predictor": OneBitBranchPredictor()},
    "SMT_2threads": {"cpu_type": CPUTypes.TIMING, "isa": ISA.ARM, "num_cores": 1,
                      "width": 4, "num_threads": 2, "branch_predictor": OneBitBranchPredictor()}
}

# Output directories
output_dirs = {
    "single_issue": "m5out_single",
    "branch_pred": "m5out_bp",
    "superscalar": "m5out_superscalar",
    "SMT_2threads": "m5out_smt"
}

# Workloads for each config
workloads = {
    "single_issue": single_thread_prog,
    "branch_pred": single_thread_prog,
    "superscalar": int_prog,              # can also try fp_prog or mem_prog
    "SMT_2threads": [int_prog, mem_prog]  # two threads for SMT
}

# Run simulations
results = {}
for key in cpu_configs:
    print(f"Running simulation: {key} ...")
    run_simulation(workloads[key], cpu_configs[key], output_dirs[key])
    results[key] = parse_stats(output_dirs[key])

# Print comparative report
print("\n=== Performance Summary ===")
for key in results:
    num_insts, ticks, ipc, latency = results[key]
    print(f"{key}: IPC = {ipc:.3f}, Avg Latency = {latency:.3f} cycles")