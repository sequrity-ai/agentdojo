import concurrent.futures
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from tqdm import tqdm


if False:
    flag = ""
else:
    flag = " --force-rerun "

base = "uv run --env-file .env.local python src/agentdojo/scripts/benchmark.py --model gpt-4o-2024-05-13 "

ut_templ = "-ut user_task_{num} "
command = "{base} -s {suite} " + ut_templ + "{flag}" + " --logdir {logdir} -dp '{configs}'"

max_scripts = 1
main_logs_name = "all_runs"

configurations_names = [] 

if True:
    configurations_names = [
        ("single_llm_no_tfilter", {"min_num_tools_for_filtering": 100, "dual_llm_mode": False}),
        ("single_llm_with_tfilter", {"min_num_tools_for_filtering": 2, "dual_llm_mode": False}),
    ]

if False:
    for op_type in ["merge", "best"]:
        for num_plans in [2, 4, 6]:
            configurations_names.append((
                        f"optype_{op_type}_numplans_{num_plans}", 
                        {
                            "plan_reduction": op_type,
                            "n_plans": num_plans,
                        }
                    ))



if True:
    for strict in [False]:
        for multistep in [False]:
            for reasoning_lvl in ["low",]:#, "medium", "high"]:
                for clearup in [1, 2, 4]:

                    if multistep and clearup != 1:
                        continue

                    configurations_names.append((
                        f"grllm_multistep_{multistep}_{reasoning_lvl}_strict_{strict}_clearup_{clearup}", 
                        {
                            "enable_multistep_planning": multistep, 
                            "reasoning_effort": reasoning_lvl,
                            "strict_mode": strict,
                            "clear_history_every_n_attempts": clearup,
                        }
                    ))

def run_script(script_command):
    """
    Runs a single bash script command.
    Returns a tuple: (command, return_code, stdout, stderr)
    """
    print(f"Starting: {script_command}")
    
    # subprocess.run is the modern way to invoke scripts

    result = subprocess.run(
        script_command,
        shell=True,          # Allows using string commands like "bash script.sh arg1"
        capture_output=True, # Captures the output so it doesn't mess up your console
        text=True            # Returns output as strings instead of bytes
    )
    return script_command, result.returncode, result.stdout, result.stderr


tasks = {}
# workspace
# Data Independent (DI)
w_di_task_ids = [0,2,3,5,6,7,8,9,10,11,12,16,20,21,24,26,27,35,38]
# Data Independent w/query llm (DIQ)
w_diq_task_ids = [1,4,14,15,17,18,22,23,25,28,29,30,31,32,33,34,36,37,39]
# Data Dependent (DD)
w_dd_task_ids = []#13,19]

# slack
# DI
s_di_task_ids = [0,5,9,12]
# DIQ
s_diq_task_ids = [2,3,7,8,10,13,14,17]
# DD
s_dd_task_ids = []#1,4,6,11,15,16,17,18,19,20]

# banking
# DI
b_di_task_ids = [1,3,4]
# DIQ
b_diq_task_ids = [0,2,5,6,7,8]
# DD
b_dd_task_ids = []#9,10,11,12,13,14,15]

tasks["workspace"] = [(w_di_task_ids, "di"), (w_diq_task_ids, "diq"), (w_dd_task_ids, "dd")]
tasks["banking"]   = [(b_di_task_ids, "di"), (b_diq_task_ids, "diq"), (b_dd_task_ids, "dd")]
tasks["slack"]     = [(s_di_task_ids, "di"), (s_diq_task_ids, "diq"), (s_dd_task_ids, "dd")]

commands = []
main_logs_name = "all_runs"

for name, configur in configurations_names:
    for suite in tasks:
        for task_ids, postfix in tasks[suite]:
            for task_id in task_ids: 
                ccommand = command.format(
                        base=base, suite=suite, num=task_id, flag=flag,
                        logdir=f"{main_logs_name}/{name}", configs=json.dumps(configur),
                        )
                ut = ut_templ.format(num=task_id)
                commands.append(ccommand)

#commands = commands[:1]
print("Overall commands:", len(commands))

errors = 0
oks = 0
with ThreadPoolExecutor(max_workers=max_scripts) as executor:
    future_to_script = {executor.submit(run_script, script): script for script in commands}
    
    for future in tqdm(as_completed(future_to_script)):
        script = future_to_script[future]
        try:
            cmd, rc, out, err = future.result()
            if rc == 0:
                oks += 1
            else:
                errors += 1
                
        except Exception as exc:
            print(f"💥 EXCEPTION for {script}: {exc}")

print("All scripts processed.")
print("Oks:", oks, "Errors:", errors)



