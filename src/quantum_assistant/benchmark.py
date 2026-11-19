import ast
import csv
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from src.quantum_assistant.llm_client import generate_response


# --------------------------------------------------
# PROJECT SETTINGS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_DIR / "data" / "benchmark" / "qiskit_humaneval.json"
)

RESULTS_DIR = PROJECT_DIR / "data" / "results"

NUM_TASKS = 10
MAX_REPAIRS = 3
TIMEOUT = 30

SUCCESS_MARKER = "BENCHMARK_TEST_PASSED"


# --------------------------------------------------
# CODE EXTRACTION
# --------------------------------------------------

def extract_code(response):
    """Extract Python code from an LLM response."""

    response = response.strip()

    if "```python" in response:
        response = response.split("```python", 1)[1]
        response = response.split("```", 1)[0]

    elif "```" in response:
        response = response.split("```", 1)[1]
        response = response.split("```", 1)[0]

    return response.strip()


def extract_function(response, entry_point, task_prompt):
    """
    Extract the required function from the LLM response.

    If the model returns only a function body, use the
    function signature from the original task prompt.
    """

    code = extract_code(response)

    try:
        tree = ast.parse(code)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == entry_point:
                    return ast.get_source_segment(code, node)

    except SyntaxError:
        pass

    # Handle responses containing only a function body.
    try:
        prompt_tree = ast.parse(task_prompt)

        for node in prompt_tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == entry_point:

                    signature = ast.get_source_segment(
                        task_prompt,
                        node
                    ).split('"""')[0].split("'''")[0].strip()

                    body = "\n".join(
                        line[4:] if line.startswith("    ") else line
                        for line in code.splitlines()
                    )

                    return signature + "\n" + body

    except (SyntaxError, AttributeError):
        pass

    return code


# --------------------------------------------------
# GENERATE QISKIT FUNCTION
# --------------------------------------------------

def generate_benchmark_function(task):

    prompt = f"""
You are an expert Python and Qiskit programmer.

Complete the following Qiskit HumanEval task.

TASK:
{task["prompt"]}

INSTRUCTIONS:
1. Implement the function named {task["entry_point"]}.
2. Return a complete Python function.
3. Use Qiskit 2.6.2 compatible APIs.
4. Follow the task description exactly.
5. Do not write example usage or test code.
6. Do not include explanations.
7. Return only Python code.

Generate the function now.
"""

    response = generate_response(prompt)

    return extract_function(
        response,
        task["entry_point"],
        task["prompt"]
    )


# --------------------------------------------------
# REPAIR FAILED FUNCTION
# --------------------------------------------------

def repair_benchmark_function(task, previous_code, error_message):

    prompt = f"""
You are an expert Python and Qiskit debugging assistant.

A generated Qiskit function failed its official test.

ORIGINAL TASK:
{task["prompt"]}

FUNCTION THAT FAILED:
{previous_code}

ERROR MESSAGE:
{error_message}

INSTRUCTIONS:
1. Identify the actual cause of the error.
2. Correct the function.
3. Use Qiskit 2.6.2 compatible APIs.
4. Preserve the original function name and purpose.
5. Do not return example usage or test code.
6. Return the complete corrected function only.
7. Do not repeat the same incorrect implementation.

Return the corrected Python function.
"""

    response = generate_response(prompt)

    return extract_function(
        response,
        task["entry_point"],
        task["prompt"]
    )


# --------------------------------------------------
# EXECUTE OFFICIAL TEST
# --------------------------------------------------

def execute_official_test(task, function_code):

    candidate_code = (
        task["prompt"]
        + "\n\n"
        + function_code
    )

    test_code = task["test"]

    script = f"""
{candidate_code}

{test_code}

check({task["entry_point"]})

print("{SUCCESS_MARKER}")
"""

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False
        ) as temp_file:

            temp_file.write(script)
            temp_path = temp_file.name

        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout
        error = result.stderr

        success = (
            result.returncode == 0
            and SUCCESS_MARKER in output
        )

        return {
            "success": success,
            "error": error if not success else "",
            "output": output,
            "return_code": result.returncode,
            "timed_out": False
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out.",
            "output": "",
            "return_code": -1,
            "timed_out": True
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "output": "",
            "return_code": -1,
            "timed_out": False
        }

    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()


# --------------------------------------------------
# ENVIRONMENT ERROR DETECTION
# --------------------------------------------------

def is_environment_error(error_message):

    environment_errors = [
        "ModuleNotFoundError",
        "No module named",
        "ImportError"
    ]

    return any(
        message in error_message
        for message in environment_errors
    )


# --------------------------------------------------
# RUN ONE BENCHMARK TASK
# --------------------------------------------------

def run_benchmark_task(task):

    task_id = task["task_id"]

    print(f"\nEvaluating {task_id}...")

    start_time = time.time()

    result = {
        "task_id": task_id,
        "difficulty": task.get("difficulty_scale", "unknown"),
        "baseline_success": False,
        "repaired_success": False,
        "repair_attempts": 0,
        "environment_error": False,
        "baseline_error": "",
        "final_error": "",
        "repair_history": [],
        "generated_code": "",
        "repaired_code": ""
    }

    # Generate initial function.
    try:
        generated_code = generate_benchmark_function(task)
        result["generated_code"] = generated_code

    except Exception as error:
        result["baseline_error"] = str(error)
        result["final_error"] = str(error)
        result["execution_time"] = round(
            time.time() - start_time, 2
        )
        return result

    # Execute initial function.
    test_result = execute_official_test(
        task,
        generated_code
    )

    result["baseline_success"] = test_result["success"]

    if test_result["success"]:
        result["repaired_success"] = True
        result["repaired_code"] = generated_code
        result["execution_time"] = round(
            time.time() - start_time, 2
        )

        print("  Baseline: Passed")
        print("  Repair attempts: 0")

        return result

    error_message = test_result["error"]
    result["baseline_error"] = error_message

    # Skip tasks that cannot run because a dependency is missing.
    if is_environment_error(error_message):

        result["environment_error"] = True
        result["final_error"] = error_message
        result["execution_time"] = round(
            time.time() - start_time, 2
        )

        print("  Skipped: Environment dependency missing")

        return result

    print("  Baseline: Failed")

    current_code = generated_code

    # Attempt LLM-based repairs.
    for attempt in range(1, MAX_REPAIRS + 1):

        print(f"  Repair attempt: {attempt}")

        try:
            repaired_code = repair_benchmark_function(
                task,
                current_code,
                error_message
            )

            repair_result = execute_official_test(
                task,
                repaired_code
            )

            result["repair_attempts"] = attempt

            result["repair_history"].append({
                "attempt": attempt,
                "success": repair_result["success"],
                "error": repair_result["error"]
            })

            current_code = repaired_code
            error_message = repair_result["error"]

            if repair_result["success"]:

                result["repaired_success"] = True
                result["repaired_code"] = repaired_code
                result["final_error"] = ""

                print("  Repair successful!")
                break

            if is_environment_error(error_message):
                result["environment_error"] = True
                break

        except Exception as error:
            error_message = str(error)

            result["repair_attempts"] = attempt
            result["repair_history"].append({
                "attempt": attempt,
                "success": False,
                "error": error_message
            })

    if not result["repaired_success"]:
        result["final_error"] = error_message
        result["repaired_code"] = current_code

        print("  Repair unsuccessful")

    result["execution_time"] = round(
        time.time() - start_time, 2
    )

    print(
        "  Final:",
        "Passed" if result["repaired_success"] else "Failed"
    )

    return result


# --------------------------------------------------
# SAVE RESULTS
# --------------------------------------------------

def save_results(results):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    json_path = RESULTS_DIR / "benchmark_results.json"
    csv_path = RESULTS_DIR / "benchmark_results.csv"

    # Back up the previous result files before replacing them.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if json_path.exists():
        backup_path = RESULTS_DIR / (
            f"benchmark_results_{timestamp}.json"
        )
        json_path.replace(backup_path)

    if csv_path.exists():
        backup_path = RESULTS_DIR / (
            f"benchmark_results_{timestamp}.csv"
        )
        csv_path.replace(backup_path)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=4
        )

    csv_fields = [
        "task_id",
        "difficulty",
        "baseline_success",
        "repaired_success",
        "repair_attempts",
        "environment_error",
        "execution_time"
    ]

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=csv_fields
        )

        writer.writeheader()

        for result in results:
            writer.writerow({
                field: result.get(field, "")
                for field in csv_fields
            })

    print("\nResults saved:")
    print(json_path)
    print(csv_path)


# --------------------------------------------------
# DISPLAY SUMMARY
# --------------------------------------------------

def print_summary(results):

    evaluated = [
        result for result in results
        if not result["environment_error"]
    ]

    skipped = len(results) - len(evaluated)

    baseline_passes = sum(
        result["baseline_success"]
        for result in evaluated
    )

    repaired_passes = sum(
        result["repaired_success"]
        for result in evaluated
    )

    initially_failed = sum(
        not result["baseline_success"]
        for result in evaluated
    )

    successful_repairs = sum(
        not result["baseline_success"]
        and result["repaired_success"]
        for result in evaluated
    )

    total_attempts = sum(
        result["repair_attempts"]
        for result in evaluated
    )

    count = len(evaluated)

    baseline_rate = (
        baseline_passes / count * 100
        if count else 0
    )

    repaired_rate = (
        repaired_passes / count * 100
        if count else 0
    )

    repair_rate = (
        successful_repairs / initially_failed * 100
        if initially_failed else 0
    )

    average_attempts = (
        total_attempts / count
        if count else 0
    )

    print("\n" + "=" * 50)
    print("       QISKIT SELF-REPAIR BENCHMARK")
    print("=" * 50)

    print(f"Total tasks selected: {len(results)}")
    print(f"Tasks evaluated: {count}")
    print(f"Environment skips: {skipped}")

    print("-" * 50)

    print(
        f"Baseline passes: {baseline_passes}/{count} "
        f"({baseline_rate:.2f}%)"
    )

    print(
        f"After repair passes: {repaired_passes}/{count} "
        f"({repaired_rate:.2f}%)"
    )

    print(f"Initially failed: {initially_failed}")
    print(f"Successfully repaired: {successful_repairs}")

    print(f"Repair success rate: {repair_rate:.2f}%")
    print(f"Average repair attempts: {average_attempts:.2f}")

    print("=" * 50)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("Loading Qiskit HumanEval dataset...")

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        dataset = json.load(file)

    selected_tasks = dataset[:NUM_TASKS]

    print(f"Selected tasks: {len(selected_tasks)}")
    print("Model: qwen2.5-coder:3b")

    results = []

    for task in selected_tasks:

        result = run_benchmark_task(task)
        results.append(result)

    save_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()
