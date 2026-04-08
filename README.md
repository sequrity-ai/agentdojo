<center>

# AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents

![GitHub License](https://img.shields.io/github/license/ethz-spylab/agentdojo) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ethz-spylab/agentdojo/lint-docs.yaml)
 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/agentdojo) ![PyPI - Downloads](https://img.shields.io/pypi/dm/agentdojo) ![PyPI - Version](https://img.shields.io/pypi/v/agentdojo)



[Edoardo Debenedetti](https://edoardo.science)<sup>1</sup>, [Jie Zhang](https://zj-jayzhang.github.io)<sup>1</sup>, [Mislav Balunović](https://www.sri.inf.ethz.ch/people/mislav)<sup>1,2</sup>, [Luca Beurer-Kellner](https://www.sri.inf.ethz.ch/people/luca)<sup>1,2</sup>, [Marc Fischer](https://marcfischer.at)<sup>1,2</sup>, [Florian Tramèr](https://floriantramer.com)<sup>1</sup>

<sup>1</sup>ETH Zurich and <sup>2</sup>Invariant Labs

[Read Paper](https://arxiv.org/abs/2406.13352) | [Inspect Results](https://agentdojo.spylab.ai/results/)
</center>

## Quickstart

```bash
pip install agentdojo
```

> [!IMPORTANT]
> Note that the API of the package is still under development and might change in the future.

If you want to use the prompt injection detector, you need to install the `transformers` extra:

```bash
pip install "agentdojo[transformers]"
```

## Running the benchmark

The benchmark can be run with the [benchmark](src/agentdojo/scripts/benchmark.py) script. Documentation on how to use the script can be obtained with the `--help` flag.

For example, to run the `workspace` suite on the tasks 0 and 1, with `gpt-4o-2024-05-13` as the LLM, the tool filter as a defense, and the attack with tool knowlege, run the following command:

```bash
python -m agentdojo.scripts.benchmark -s workspace -ut user_task_0 \
    -ut user_task_1 --model gpt-4o-2024-05-13 \
    --defense tool_filter --attack tool_knowledge
```

To run the above, but on all suites and tasks, run the following:

```bash
python -m agentdojo.scripts.benchmark --model gpt-4o-2024-05-13 \
    --defense tool_filter --attack tool_knowledge
```

## Inspect the results

To inspect the results, go to the dedicated [results page](https://agentdojo.spylab.ai/results/) of the documentation. AgentDojo results are also listed in the [Invariant Benchmark Registry](https://explorer.invariantlabs.ai/benchmarks/).Agent

## Documentation of the Dojo

Take a look at our [documentation](https://agentdojo.spylab.ai/).

## Development set-up

Take a look at the [development set-up](https://agentdojo.spylab.ai/docs/development) docs.

## Task Data-Dependency Classification

Tasks are classified based on their data dependency, as reflected in the [runner_scripts/](runner_scripts/) naming convention:

- **dd** — Data Dependent
- **diq** — Data Independent with QLLM
- **di** — Data Independent

> Note: Slack `user_task_17` appears in both dd and diq scripts.

### Banking

| Category | Tasks |
|----------|-------|
| **dd** | user_task_9, user_task_10, user_task_11, user_task_12, user_task_13, user_task_14, user_task_15 |
| **diq** | user_task_0, user_task_2, user_task_5, user_task_6, user_task_7, user_task_8 |
| **di** | user_task_1, user_task_3, user_task_4 |

### Slack

| Category | Tasks |
|----------|-------|
| **dd** | user_task_1, user_task_4, user_task_6, user_task_11, user_task_15, user_task_16, user_task_17, user_task_18, user_task_19, user_task_20 |
| **diq** | user_task_2, user_task_3, user_task_7, user_task_8, user_task_10, user_task_13, user_task_14, user_task_17 |
| **di** | user_task_0, user_task_5, user_task_9, user_task_12 |

### Workspace

| Category | Tasks |
|----------|-------|
| **dd** | user_task_13, user_task_19 |
| **diq** | user_task_1, user_task_4, user_task_14, user_task_15, user_task_17, user_task_18, user_task_22, user_task_23, user_task_25, user_task_28, user_task_29, user_task_30, user_task_31, user_task_32, user_task_33, user_task_34, user_task_36, user_task_37, user_task_39 |
| **di** | user_task_0, user_task_2, user_task_3, user_task_5, user_task_6, user_task_7, user_task_8, user_task_9, user_task_10, user_task_11, user_task_12, user_task_16, user_task_20, user_task_21, user_task_24, user_task_26, user_task_27, user_task_35, user_task_38 |

## Citing

If you use AgentDojo in your research, please consider citing our paper:

```bibtex
@inproceedings{
 debenedetti2024agentdojo,
 title={AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for {LLM} Agents},
 author={Edoardo Debenedetti and Jie Zhang and Mislav Balunovic and Luca Beurer-Kellner and Marc Fischer and Florian Tram{\`e}r},
 booktitle={The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track},
 year={2024},
 url={https://openreview.net/forum?id=m1YYAQjO3w}
}
```
