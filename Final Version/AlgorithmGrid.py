import Cluster
import itertools
import numpy as np

def __sanitize_value(v):
    if v is np.inf:
        return "inf"
    if v is -np.inf:
        return "ninf"
    if isinstance(v, float):
        return str(v).replace(".", "p")
    return str(v)

def __getNames(final_combinations, prefix_str=""):
    results = []
    for combo in final_combinations:
        parts = []
        for d in combo:
            for k, v in d.items():
                parts.append(f"{k}_{__sanitize_value(v)}")
        s = "_".join(parts)
        s = f"{prefix_str}_{s}"
        results.append(s)
    return results


def getPipelines(params_list, algorithmDict):
    expanded = []
    for d in params_list:
        keys = list(d.keys())
        values = [d[k] for k in keys]
        combos = []
        for combo in itertools.product(*values):
            combos.append(dict(zip(keys, combo)))
        expanded.append(combos)

    # Now take cartesian product across dicts
    params_combinations = []
    for combo in itertools.product(*expanded):
        params_combinations.append(list(combo))

    # getNames
    experiment_names = __getNames(params_combinations, prefix_str=algorithmDict["base_name"])

    # prepare pipeline
    clusterers = algorithmDict["algs"]
    
    pipeline_list = []
    for i in range(len(params_combinations)):
        pipeline = []
        combo = params_combinations[i]
        for j in range(len(clusterers)):
            pipeline.append(clusterers[j](**combo[j]))
        pipeline_list.append(Cluster.ClusterPipeline(pipeline))

    return experiment_names, pipeline_list