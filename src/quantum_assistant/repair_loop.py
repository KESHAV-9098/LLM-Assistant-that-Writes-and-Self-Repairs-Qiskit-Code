
from urllib import response

from src.quantum_assistant.llm_client import generate_response
from src.quantum_assistant.code_generator import (
    generate_qiskit_code,
    extract_python_code
)
from src.quantum_assistant.code_executor import execute_code



def repair_qiskit_code(task, previous_code, error_message):
    prompt = f"""
You are repairing a broken Qiskit Python program.

IMPORTANT: The previous program is INCORRECT.
You MUST NOT repeat its deprecated imports or execution methods.

Original task:
{task}

Previous broken code:
{previous_code}

Execution error:
{error_message}

Installed environment:
- Python 3.11
- Qiskit 2.6.2
- Qiskit Aer 0.18.2

MANDATORY RULES:
1. Never import Aer from qiskit.
2. Never import execute from qiskit.
3. Never use execute().
4. Import QuantumCircuit using:
   from qiskit import QuantumCircuit
5. When simulation is required, import:
   from qiskit_aer import AerSimulator
6. Execute circuits using:
   simulator = AerSimulator()
   job = simulator.run(qc, shots=1000)
   result = job.result()
   counts = result.get_counts()
7. Include all required imports.
8. Preserve the original task.
9. Return a COMPLETE corrected Python program.
10. Do not repeat the previous broken code.

Return ONLY executable Python code inside a Python code block.
"""
    response = generate_response(prompt)
    print("\n===== LLM REPAIR RESPONSE =====")
    print(response)
    print("===== END REPAIR RESPONSE =====\n")
    corrected_code = extract_python_code(response)

    if not corrected_code:
        raise ValueError("The LLM did not generate corrected code.")

    return corrected_code



def run_self_repair(task, max_repairs=3, timeout=30, initial_code=None):
    """
    Generate, execute and repair Qiskit code.

    max_repairs specifies the maximum number of repair attempts
    after the initial generation.
    """

    # Generate initial code unless test code was supplied
    if initial_code is None:
        current_code = generate_qiskit_code(task)
    else:
        current_code = initial_code

    history = []

    # Execute initial code
    result = execute_code(current_code, timeout=timeout)

    history.append({
        "attempt": 0,
        "code": current_code,
        "success": result["success"],
        "stdout": result["stdout"],
        "stderr": result["stderr"]
    })

    # Continue repairing while execution fails
    for repair_number in range(1, max_repairs + 1):

        if result["success"]:
            break

        print(f"\nRepair attempt {repair_number}/{max_repairs}...")

        try:
            corrected_code = repair_qiskit_code(
                task,
                current_code,
                result["stderr"]
            )

        except Exception as error:
            print("Code repair request failed:", error)
            break

        current_code = corrected_code

        # Execute the corrected code
        result = execute_code(
            current_code,
            timeout=timeout
        )

        history.append({
            "attempt": repair_number,
            "code": current_code,
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"]
        })

    return {
        "success": result["success"],
        "initial_code": history[0]["code"],
        "final_code": current_code,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "repair_attempts": len(history) - 1,
        "history": history
    }


if __name__ == "__main__":

    task = """
    Create a 2-qubit Bell state using Qiskit.
    Apply a Hadamard gate to qubit 0.
    Apply a CNOT gate from qubit 0 to qubit 1.
    Measure both qubits.
    Simulate using Qiskit Aer and print the counts.
    """

    # Intentionally outdated code to demonstrate self-repair
    broken_code = """
from qiskit import QuantumCircuit, Aer, execute

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

simulator = Aer.get_backend('qasm_simulator')
job = execute(qc, simulator, shots=1024)
result = job.result()

print(result.get_counts())
"""

    print("Starting Qiskit self-repair demonstration...")

    report = run_self_repair(
        task=task,
        max_repairs=3,
        initial_code=broken_code
    )

    print("\n" + "=" * 50)
    print("SELF-REPAIR RESULTS")
    print("=" * 50)

    print("Initial execution: Failed")
    print("Repair attempts:", report["repair_attempts"])
    print("Final execution successful:", report["success"])

    print("\nFinal Qiskit Code:\n")
    print(report["final_code"])

    if report["stdout"]:
        print("\nFinal Program Output:")
        print(report["stdout"])

    if not report["success"]:
        print("\nFinal Error:")
        print(report["stderr"])
