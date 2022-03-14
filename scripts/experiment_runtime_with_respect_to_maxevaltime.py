from argparse import ArgumentError
from multiprocessing.sharedctypes import copy

from utils.UpdateParameter import *
import subprocess
import time
import re
from os.path import exists
import sys

savefigpath = "/home/paran/Dropbox/BCAM/07_estancia_1/code/results/figures/"
parameter_file="experiments/nipes/parameters.csv"

maxEvalTimes = [1.0, 3.0, 5.0, 10.0, 20.0, 30.0]
seeds = list(range(2,25))




if len(sys.argv) != 2:
    raise ArgumentError("this script requires only one argument --plot --launch_local or --launch_cluster")

if sys.argv[1] not in ("--plot", "--launch_local", "--launch_cluster"):
    raise ArgumentError("this script requires only one argument --plot --launch_local or --launch_cluster")


# update parameters
if sys.argv[1] in ("--launch_local", "--launch_cluster"):
    parameter_file = "experiments/nipes/parameters.csv"
    parameter_text = """
#experimentName,string,nipes
#subexperimentName,string,standard
#preTextInResultFile,string,seed_8_maxEvalTime_0.5
#resultFile,string,../results/data/runtimewrtmaxevaltime_results/runtimewrtmaxevaltime_exp_result_8_maxEvalTime_0.5.txt


#expPluginName,string,/usr/local/lib/libNIPES.so
#scenePath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models/scenes/shapes_exploration.ttt
#robotPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models/robots/model0.ttm
#modelsPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models

#repository,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/logs
#fitnessFile,string,fitnesses.csv
#evalTimeFile,string,eval_durations.csv
#behavDescFile,string,final_pos.csv
#stopCritFile,string,stop_crit.csv
#noveltyFile,string,novelty.csv
#archiveFile,string,archive.csv
#energyCostFile,string,energyCost.csv
#simTimeFile,string,simTime.csv

#isScreenshotEnable,bool,0
#isVideoRecordingEnable,bool,0

#jointControllerType,int,0
#verbose,bool,1
#instanceType,int,0
#killWhenNotConnected,bool,0
#shouldReopenConnections,bool,0
#seed,int,8

#populationSize,int,100
#maxEvalTime,float,30.0
#maxNbrEval,int,10000
#timeStep,float,0.1

#modifyMaxEvalTime,bool,0
#constantmodifyMaxEvalTime,float,0.0
#minEvalTime,float,3.0

#noiseLevel,double,0.
#maxVelocity,double,10.

#envType,int,1
#arenaSize,double,2.
#target_x,double,0.75
#target_y,double,0.75
#target_z,double,0.05
#init_x,float,0
#init_y,float,0
#init_z,float,0.12
#MaxWeight,float,1.0
#energyBudget,double,100
#energyReduction,bool,0
#NNType,int,2
#NbrInputNeurones,int,2
#NbrOutputNeurones,int,4
#NbrHiddenNeurones,int,8
#UseInternalBias,bool,1

#reloadController,bool,1
#CMAESStep,double,1.
#FTarget,double,-0.05
#elitistRestart,bool,0
#withRestart,bool,1
#incrPop,bool,0
#lengthOfStagnation,int,20
#kValue,int,15
#noveltyThreshold,double,0.9
#archiveAddingProb,double,0.4
#noveltyRatio,double,1.
#noveltyDecrement,double,0.05
#populationStagnationThreshold,float,0.01

#nbrWaypoints,int,50
#withBeacon,bool,1
#flatFloor,bool,1
#use_sim_sensor_data,bool,0
#withTiles,bool,1     
#jointSubs,sequence_int,-1;-1;-1;0;1;2
"""

    mass_update_parameters(parameter_file, parameter_text)


#region local_cluster

if sys.argv[1] == "--launch_cluster":
    import itertools
    import time

    def run_with_seed_and_runtime(maxEvalTime, seed, port):

        time.sleep(0.5)
        update_parameter(parameter_file, "seed", str(seed))
        update_parameter(parameter_file, "maxEvalTime", str(maxEvalTime))
        update_parameter(parameter_file, "resultFile", f"../results/data/runtimewrtmaxevaltime_results/runtimewrtmaxevaltime_exp_result_{seed}_maxEvalTime_{maxEvalTime}.txt")
        update_parameter(parameter_file, "preTextInResultFile", f"seed_{seed}_maxEvalTime_{maxEvalTime}")

        subprocess.run(f"bash launch.sh -e=nipes --vrep --cluster --parallel --port={port}",shell=True)

        
    port = int(26100000)
    for maxEvalTime, seed in itertools.product(maxEvalTimes, seeds):
        time.sleep(0.25)
        run_with_seed_and_runtime(maxEvalTime, seed, port)
        port += int(10e4)


#endregion
    





#region local_launch

if sys.argv[1] == "--launch_local":
    import itertools
    import time

    def run_with_seed_and_runtime(maxEvalTime, seed):

        time.sleep(0.5)
        update_parameter(parameter_file, "seed", str(seed))
        update_parameter(parameter_file, "maxEvalTime", str(maxEvalTime))
        update_parameter(parameter_file, "resultFile", f"../results/data/runtimewrtmaxevaltime_results/runtimewrtmaxevaltime_exp_result_{seed}_maxEvalTime_{maxEvalTime}.txt")
        update_parameter(parameter_file, "preTextInResultFile", f"seed_{seed}_maxEvalTime_{maxEvalTime}")

        exec_res=subprocess.run(f"bash launch.sh --coppelia -e=nipes --parallel",shell=True, capture_output=True)
        with open(f"logs_{seed}.txt", "w") as f:
            f.write("OUT: ------------------")
            f.write(exec_res.stdout.decode("utf-8"))
            f.write("ERR: ------------------")
            f.write(exec_res.stderr.decode("utf-8"))
        
    for maxEvalTime, seed in itertools.product(maxEvalTimes, seeds):
        run_with_seed_and_runtime(maxEvalTime, seed)


#endregion




#region plot

if sys.argv[1] == "--plot":

    from matplotlib import pyplot as plt
    import numpy as np
    from cycler import cycler
    from statistics import mean,median
    from pylab import polyfit
    import subprocess
    import sys


    savefig_paths = ["results/figures", "/home/paran/Dropbox/BCAM/07_estancia_1/paper/images"]

    def load_bw_theme(ax: plt.Axes):
        # taken from http://olsgaard.dk/monochrome-black-white-plots-in-matplotlib.html
        # Create cycler object. Use any styling from above you please
        monochrome = (cycler('color', ['k']) * cycler('marker', [' ', '.', 'x', '^']) * cycler('linestyle', ['-', '--', ':', '-.']))
        ax.set_prop_cycle(monochrome)
        #ax.grid()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)



    fig, ax = plt.subplots(1,1)
    load_bw_theme(ax)

    # ax.boxplot(max_eval_time_5,positions=[50],widths=[40])
    # ax.boxplot(max_eval_time_15,positions=[150],widths=[40])
    # ax.boxplot(max_eval_time_30,positions=[300],widths=[40])
    # ax.boxplot(max_eval_time_60,positions=[600],widths=[40])
    # ax.boxplot(max_eval_time_90,positions=[900],widths=[40])
    # ax.boxplot(max_eval_time_120,positions=[1200],widths=[40])

    average_runtimes = []
    x_lower = min(maxEvalTimes)
    x_upper = max(maxEvalTimes)
    for maxEvalTime in maxEvalTimes:
        runtimes = []
        for seed in seeds:
            res_filepath = f"results/data/runtimewrtmaxevaltime_results/runtimewrtmaxevaltime_exp_result_{seed}_maxEvalTime_{maxEvalTime}.txt"
            if exists(res_filepath):
                with open(res_filepath, "r") as f:
                    all_text = f.readlines()
                    if len(all_text) != 1:
                        continue
                    split_line = all_text[0].strip("\n").split(",")
                    runtime = float(split_line[-1])
                    runtimes.append(runtime)
        print(len(runtimes))
        average_runtimes.append(mean(runtimes))
        ax.boxplot(runtimes, positions=[maxEvalTime],widths=[(x_upper - x_lower) / len(maxEvalTimes) / 2])

    x = np.array(maxEvalTimes)
    y = np.array(average_runtimes) 

 

    m,b = polyfit(x, y, 1)
    ax.plot([x_lower,x_upper], [x_lower*m+b, x_upper*m+b], label=f"$f(x) = {m:2f} \cdot x  + {b:2f}$", linestyle="--")

    ax.scatter(maxEvalTimes, average_runtimes, marker="+", label="Average")
    # ax.scatter(x[0],median(maxEvalTimes[0]),marker="_", color="orange", label="Median")
    ax.legend()

    plt.xlabel("maxEvalTime for each controller")
    plt.ylabel("Runtime of the evolutionary algorithm")
    plt.savefig(savefigpath + "runtime_of_one_controller_evaluation_with_respect_to_max_eval_time.pdf")
    plt.close()

#endregion