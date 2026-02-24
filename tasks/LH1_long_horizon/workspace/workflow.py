"""
Long-horizon workflow with failure injection.
Some steps may fail on first attempt; agent must detect and recover.
"""
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    with open("pipeline_config.json", "r") as f:
        return json.load(f)


def append_log(log_path, entry):
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# Steps that fail on first attempt — hidden in code logic
_FRAGILE_STEPS = {5, 11}


def execute_step(step, intermediates_dir, attempt_tracker):
    step_id = step["id"]
    marker = os.path.join(intermediates_dir, f"step{step_id}_fail")
    output_file = os.path.join(intermediates_dir, f"step{step_id}_output.txt")

    # Failure injection: check internal counter file
    counter_file = os.path.join(intermediates_dir, f".step{step_id}_attempts")
    attempt_count = 0
    if os.path.exists(counter_file):
        attempt_count = int(open(counter_file).read().strip())
    attempt_count += 1
    with open(counter_file, "w") as f:
        f.write(str(attempt_count))

    if step_id in _FRAGILE_STEPS and attempt_count == 1:
        # Create failure marker
        with open(marker, "w") as f:
            f.write("FAILED")
        raise RuntimeError(f"Step {step_id} ({step['name']}) failed (transient error)")

    # Check if previous failure marker exists (agent must clean it up)
    if os.path.exists(marker):
        raise RuntimeError(f"Step {step_id}: failure marker exists. Remove {marker} to retry.")

    # Normal execution: produce output
    content = f"step_{step_id}_{step['name']}_output_{step.get('action', 'default')}"
    with open(output_file, "w") as f:
        f.write(content)

    return content


def main():
    config = load_config()
    steps = config["steps"]
    max_execs = config["max_total_executions"]

    os.makedirs("output", exist_ok=True)
    os.makedirs("intermediates", exist_ok=True)

    log_path = "output/workflow_log.jsonl"
    # Clear log
    open(log_path, "w").close()

    total_executions = 0
    recovered = 0
    all_outputs = []

    for step in steps:
        retries = 0
        while retries < 2:
            total_executions += 1
            if total_executions > max_execs:
                append_log(log_path, {"step": step["id"], "status": "budget_exceeded", "ts": now_iso()})
                print(f"ERROR: Exceeded max executions ({max_execs})")
                sys.exit(1)

            try:
                output = execute_step(step, "intermediates", set())
                all_outputs.append(output)
                append_log(log_path, {"step": step["id"], "name": step["name"],
                                       "status": "pass", "attempt": retries + 1, "ts": now_iso()})
                break
            except RuntimeError as e:
                append_log(log_path, {"step": step["id"], "name": step["name"],
                                       "status": "fail", "error": str(e),
                                       "attempt": retries + 1, "ts": now_iso()})
                # Attempt cleanup before retry
                cleanup_dir = os.path.join("intermediates", "temp")
                if os.path.exists(cleanup_dir):
                    shutil.rmtree(cleanup_dir)
                retries += 1
                if retries >= 2:
                    print(f"FATAL: Step {step['id']} failed after 2 attempts")
                    sys.exit(1)
                recovered += 1

    # Compute checksum
    combined = "".join(all_outputs)
    checksum = hashlib.sha256(combined.encode()).hexdigest()

    result = {
        "steps_completed": len(all_outputs),
        "recovered_failures": recovered,
        "checksum": checksum,
    }

    with open("output/final_result.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"Workflow complete: {json.dumps(result)}")


if __name__ == "__main__":
    main()
