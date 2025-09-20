uv run --env-file .env.local python src/agentdojo/scripts/benchmark.py --model gpt-4o-2024-05-13  -s banking -ut user_task_1  --force-rerun &
uv run --env-file .env.local python src/agentdojo/scripts/benchmark.py --model gpt-4o-2024-05-13  -s banking -ut user_task_3  --force-rerun &
uv run --env-file .env.local python src/agentdojo/scripts/benchmark.py --model gpt-4o-2024-05-13  -s banking -ut user_task_4  --force-rerun &
