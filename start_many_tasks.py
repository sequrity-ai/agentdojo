import concurrent.futures
import subprocess


flag = " --force-rerun "

if False:
    flag = ""

base = "uv run --env-file .env.local python src/agentdojo/scripts/benchmark.py --model gpt-4o-2024-05-13 "

ut_templ = "-ut user_task_{num} "
command = "{base} -s {suite} " + ut_templ + "{flag}"


def run_script(task_id):
    """
    A simple worker that runs a bash script with a specific ID.
    It returns the script's output on success or an error message on failure.
    """
    print(ccommand)  

tasks = {}
# workspace
# Data Independent (DI)
w_di_task_ids = [0,2,3,5,6,7,8,9,10,11,12,16,20,21,24,26,27,35,38]
# Data Independent w/query llm (DIQ)
w_diq_task_ids = [1,4,14,15,17,18,22,23,25,28,29,30,31,32,33,34,36,37,39]
# Data Dependent (DD)
w_dd_task_ids = [13,19]

# slack
# DI
s_di_task_ids = [0,5,9,12]
# DIQ
s_diq_task_ids = [2,3,7,8,10,13,14,17]
# DD
s_dd_task_ids = [1,4,6,11,15,16,17,18,19,20]

# banking
# DI
b_di_task_ids = [1,3,4]
# DIQ
b_diq_task_ids = [0,2,5,6,7,8]
# DD
b_dd_task_ids = [9,10,11,12,13,14,15]

tasks["workspace"] = [(w_di_task_ids, "di"), (w_diq_task_ids, "diq"), (w_dd_task_ids, "dd")]
tasks["banking"]   = [(b_di_task_ids, "di"), (b_diq_task_ids, "diq"), (b_dd_task_ids, "dd")]
tasks["slack"]     = [(s_di_task_ids, "di"), (s_diq_task_ids, "diq"), (s_dd_task_ids, "dd")]

for suite in tasks:
    for task_ids, postfix in tasks[suite]:
        outfile = open(f"{suite}_starter_{postfix}.sh", "w")
        outfile_test = open(f"{suite}_starter_{postfix}_test.sh", "w")
        combined = ""

        print(postfix)

        for task_id in task_ids: 
            ccommand = command.format(base=base, suite=suite, num=task_id, flag=flag)

            ut = ut_templ.format(num=task_id)
            combined += ut

            outfile.write(ccommand + "&\n")
        
        outfile_test.write(base + f" -s {suite} " + combined)

        outfile.close()
        outfile_test.close()
