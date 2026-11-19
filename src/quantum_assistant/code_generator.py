
import re

from src.quantum_assistant.llm_client import generate_response


def extract_python_code(response):
    """
    Extract Python code from an LLM response.
    Supports responses with or without Markdown code fences.
    """

    # Find Python code inside Markdown code fences
    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    # If no code fence exists, use the complete response
    return response.strip()


def generate_qiskit_code(task):
    """
    Generate Qiskit Python code from a natural-language task.
    """

    prompt = f"""
You are an expert Qiskit Python programmer.

Environment:
- Python 3.11
- Qiskit 2.6.2
- Qiskit Aer 0.18.2

Task:
{task}

Instructions:
1. Generate correct, executable Python code.
2. Use current Qiskit APIs.
3. Import AerSimulator from qiskit_aer when simulation is required.
4. Do not use the deprecated execute() function.
5. Include all necessary imports.
6. Return only Python code inside a code block.
"""

    response = generate_response(prompt)

    code = extract_python_code(response)

    if not code:
        raise ValueError("The LLM did not generate any Python code.")

    return code


if __name__ == "__main__":

    example_task = """
    Create a 2-qubit Bell state circuit.
    Apply a Hadamard gate and a CNOT gate.
    Measure both qubits and simulate using Qiskit Aer.
    Print the measurement counts.
    """

    print("Generating Qiskit code using Ollama...\n")

    generated_code = generate_qiskit_code(example_task)

    print("Generated Code:\n")
    print(generated_code)
