# LLM Assistant That Writes and Self-Repairs Qiskit Code

An AI-powered quantum programming assistant that generates Qiskit code from natural language instructions, executes the generated programs, and attempts to automatically repair errors using a Large Language Model (LLM).

## Overview

Quantum programming requires knowledge of quantum computing concepts, Python programming, and frameworks such as Qiskit. Beginners often encounter errors due to incorrect syntax, outdated APIs, deprecated functions, and compatibility issues.

This project introduces an LLM-based assistant that simplifies quantum programming through natural language interaction and automated code correction.

The system uses a locally hosted **Qwen2.5-Coder 3B** model through Ollama to generate Qiskit programs. Generated code is executed in a Python environment. If execution fails, the error message and previous code are provided to the LLM, which attempts to generate a corrected version.

The process continues until the program executes successfully or the maximum number of repair attempts is reached.

## Key Features

- **Natural Language to Qiskit Code:** Generate quantum programs from user instructions.
- **LLM-Based Code Generation:** Uses Qwen2.5-Coder 3B through Ollama.
- **Automatic Code Execution:** Executes generated Python programs and captures their outputs.
- **Self-Repair Mechanism:** Identifies execution failures and sends error feedback to the LLM for correction.
- **Iterative Repair:** Supports up to three repair attempts.
- **Interactive Web Interface:** Built using Streamlit.
- **Execution History:** Displays generated code, execution outputs, errors, and repair attempts.
- **Benchmark Evaluation:** Evaluates code generation and repair performance using the Qiskit HumanEval dataset.
- **Local Model Integration:** Uses Ollama instead of requiring a paid external LLM API.

## System Architecture

The system follows an iterative code generation and self-repair workflow.

1. The user enters a quantum programming task using natural language.
2. The LLM interprets the instruction and generates Qiskit code.
3. The generated code is executed in the Python environment.
4. If execution succeeds, the final code and output are displayed.
5. If execution fails, the error message and previous code are sent back to the LLM.
6. The LLM generates corrected code, which is executed again.
7. The process stops when execution succeeds or the maximum repair limit is reached.

The benchmark module separately evaluates predefined quantum programming tasks and records performance results.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.11 | Main programming language |
| Qiskit 2.6.2 | Quantum circuit construction |
| Qiskit Aer 0.18.2 | Quantum circuit simulation |
| Ollama | Local LLM execution |
| Qwen2.5-Coder 3B | Code generation and repair |
| Streamlit | Interactive web application |
| Pandas | Benchmark data handling |
| Matplotlib / Plotly | Data visualization |
| Requests | Communication with Ollama API |
| Git and GitHub | Version control and project hosting |

## Project Structure

```text
Quantum/
│
├── app.py
├── first_circuit.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── benchmark/
│   │   └── qiskit_humaneval.json
│   │
│   └── results/
│       ├── benchmark_results.csv
│       └── benchmark_results.json
│
├── src/
│   ├── __init__.py
│   │
│   └── quantum_assistant/
│       ├── __init__.py
│       ├── benchmark.py
│       ├── code_executor.py
│       ├── code_generator.py
│       ├── llm_client.py
│       ├── metrics.py
│       └── repair_loop.py
│
└── tests/
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project directory:

```bash
cd Quantum
```

### 2. Create a Python Environment

Using Conda:

```bash
conda create -n quantum_env python=3.11
conda activate quantum_env
```

Alternatively, create a virtual environment:

```bash
python -m venv quantum_env
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure the `requests` package is included in `requirements.txt` because it is required for communication with Ollama.

### 4. Install and Configure Ollama

Download and install Ollama:

https://ollama.com/download

Pull the required model:

```bash
ollama pull qwen2.5-coder:3b
```

Make sure Ollama is running locally and the model is available.

### 5. Run the Application

From the project root directory:

```bash
streamlit run app.py
```

The application will open in your browser, normally at:

```text
http://localhost:8501
```

## How to Use

1. Open the Streamlit application.
2. Navigate to the Quantum Code Assistant section.
3. Enter a natural language instruction describing the quantum program.
4. Click the code generation and execution button.
5. The LLM generates the Qiskit program.
6. The system executes the generated code.
7. If an error occurs, the self-repair mechanism attempts to correct it.
8. View the final generated code, execution output, and repair history.

### Example Input

```text
Create a Bell State using two qubits.
Apply a Hadamard gate to the first qubit.
Apply a CNOT gate with the first qubit
as control and the second as target.
Measure both qubits and simulate
the circuit using 1000 shots.
Print the measurement counts.
```

### Expected Output

The measurement results should predominantly contain:

```text
{'00': approximately 500, '11': approximately 500}
```

The exact counts vary between simulation runs.

## Benchmark Evaluation

The project uses the Qiskit HumanEval dataset to evaluate code generation and self-repair performance on predefined quantum programming tasks.

The benchmark evaluates:

- Initial code generation success.
- Code execution correctness.
- Successful repairs after execution failures.
- Number of repair attempts.
- Final execution success rate.

### Experimental Results

The following results were obtained from a pilot evaluation of 10 selected tasks.

| Evaluation Metric | Result |
|---|---:|
| Total selected tasks | 10 |
| Tasks evaluated | 9 |
| Environment skips | 1 |
| Baseline passes | 5/9 |
| Baseline pass rate | 55.56% |
| After-repair passes | 6/9 |
| After-repair pass rate | 66.67% |
| Initially failed tasks | 4 |
| Successfully repaired tasks | 1 |
| Repair success rate | 25.00% |
| Average repair attempts | 1.22 |

**Note:** One task was skipped because a required dependency was unavailable. These results represent a limited pilot evaluation, not a complete evaluation of all 151 dataset tasks.

## Deployment

The Streamlit application can be deployed using Streamlit Community Cloud by connecting the GitHub repository.

Deployment link:

**https://llm-assistant-that-writes-and-self-repairs-qiskit-code.streamlit.app/**

**Important:** The current LLM integration uses a local Ollama endpoint (`http://localhost:11434/api/chat`). Consequently, the deployed Streamlit application can display its interface and available benchmark results, but live code generation and self-repair require an accessible remote LLM service. The local Ollama setup continues to work when running the application on a computer where Ollama is installed and running.

## Limitations

- Generated code may contain incorrect syntax, outdated APIs, or logical errors.
- Repair success depends on the LLM's ability to understand execution feedback.
- The current implementation supports a maximum of three repair attempts by default.
- Benchmark evaluation currently covers only a selected subset of Qiskit HumanEval tasks.
- The local code executor is not a secure sandbox and is intended for controlled local demonstrations.
- Public deployment requires a remote model service and a properly isolated code execution environment.

## Future Enhancements

- Improve code-generation accuracy through better prompting and model evaluation.
- Support additional quantum programming frameworks.
- Introduce secure sandboxed code execution.
- Integrate remote LLM services for public deployment.
- Expand benchmark evaluation to the complete dataset.
- Add detailed error explanations and quantum programming guidance.
- Improve the self-repair mechanism using execution feedback and validation.

## Dataset Reference

Qiskit HumanEval dataset:

https://github.com/qiskit-community/qiskit-human-eval

Refer to the original repository for dataset licensing and attribution requirements.

## Contributors

**Developed as an academic quantum computing project.**

## License

Choose an appropriate open-source license before publishing this repository. If you choose MIT, add a `LICENSE` file containing the MIT License text.

