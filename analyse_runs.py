import json
import logging
import re
from collections import defaultdict
from pathlib import Path
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from agentdojo.task_suite import get_suites, get_suite
from agentdojo.types import ChatMessage
from matplotlib.lines import Line2D
from pydantic import BaseModel, ConfigDict, model_validator
from statsmodels.stats import proportion

errors = set()

class TaskResults(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    suite_name: str
    pipeline_name: str
    user_task_id: str
    injection_task_id: str | None
    attack_type: str | None
    injections: dict[str, str]
    messages: list[ChatMessage]
    error: str | None
    utility: float
    security: float
    duration: float


def load_task_results(pipeline_name, suite_name, user_task, attack_name, injection_task, logdir=Path("runs")):
    path = logdir / pipeline_name / suite_name / user_task / attack_name / f"{injection_task}.json"
    with path.open() as f:
        res_dict = json.load(f)
    return res_dict 



def load_experiment_results(suite_name, pipeline_name, attack_name, logdir=Path("runs")):
    suite = get_suite("v1", suite_name)
    results_without_injections = {}
    results_with_injections = {}
    
    for user_task_id in suite.user_tasks.keys():
        try:
            results_without_injections[(user_task_id, None)] = load_task_results(
                pipeline_name, suite_name, user_task_id, "none", "none", logdir
            )
        except:
            print(f"{user_task_id} doesnt exist...")
    return results_without_injections


def make_dataframe(model_names, attack, logdir):
    rows = []
    for model in model_names:
        print(model)
        for suite in get_suites("v1"):
            if suite == "travel":
                continue

            #if suite != "workspace":
            #    continue

            try:
                results_without = load_experiment_results(suite, model, attack, logdir=logdir)
            except Exception as e:
                print(e)
                continue
            utilities = []
            defence_params = []
            unsolved = []
            durations = []
            usages = []

            for usertask in results_without:
                try:
                    #print(usertask[0], int(results_without[usertask]['duration']), "s", 'Utility:', results_without[usertask]['utility'])
                    utilities.append(results_without[usertask]['utility'])
                    durations.append(results_without[usertask]['duration'])
                    defence_params.append(results_without[usertask]['defence_params'])
                    if "usage" in results_without[usertask]:
                        usages.append(results_without[usertask]['usage'])
                    else:
                        usages.append(None)
                except:
                    #print(usertask[0], 'error')
                    unsolved.append(True)

            print("+", suite, "Utility:", np.mean(utilities), "unsolved", sum(unsolved))
            if len(durations) > 0:
                print("++Duration:", "mean", np.mean(durations), "medium", np.median(durations), "max", max(durations), "min", min(durations))
            print("+Tokens:")
            for tname in ['completion_tokens', 'prompt_tokens', 'total_tokens']:
                _usages = [i[tname] for i in usages if i is not None]
                if len(_usages) > 0:
                    print("++", tname, "mean", np.mean(_usages), "medium", np.median(_usages), "max", max(_usages), "min", min(_usages))

            #return (utilities, durations, usages, unsolved, defence_params)

model_names = ["gpt-4o-2024-05-13"]#, "singlellm_gpt-4o-2024-05-13", "not_strict_dualllm_gpt-4o-2024-05-13"]
logdir = "all_runs"

for run_dir in os.listdir(logdir):
    combined_dir = f"{logdir}/{run_dir}"
    print(combined_dir)
    df = make_dataframe(model_names, "none", logdir=Path(combined_dir))

