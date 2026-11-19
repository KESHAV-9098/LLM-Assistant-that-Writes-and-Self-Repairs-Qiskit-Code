
import subprocess
import sys
import tempfile
from pathlib import Path


def execute_code(code, timeout=30):
    """
    Execute generated Python code in a separate process.

    Returns execution status, output, errors and return code.
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        script_path = Path(temp_dir) / "generated_code.py"

        # Save generated code to a temporary Python file
        script_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=temp_dir
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "timed_out": False
            }

        except subprocess.TimeoutExpired as error:

            return {
                "success": False,
                "stdout": error.stdout or "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "return_code": None,
                "timed_out": True
            }

        except Exception as error:

            return {
                "success": False,
                "stdout": "",
                "stderr": str(error),
                "return_code": None,
                "timed_out": False
            }


if __name__ == "__main__":

    print("Testing Qiskit code executor...\n")

    # Test 1: Valid Python code
    valid_code = """
print("Qiskit code execution successful!")
print("Result: Bell State")
"""

    result = execute_code(valid_code)

    print("TEST 1: Valid Code")
    print("Success:", result["success"])
    print("Output:", result["stdout"])

    # Test 2: Invalid Python import
    invalid_code = """
from qiskit import Aer, execute
"""

    result = execute_code(invalid_code)

    print("\nTEST 2: Invalid Code")
    print("Success:", result["success"])
    print("Error:\n", result["stderr"])
