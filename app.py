
import json
from pathlib import Path

import streamlit as st

from src.quantum_assistant.repair_loop import run_self_repair


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

RESULTS_FILE = (
    PROJECT_DIR / "data" / "results" / "benchmark_results.json"
)

MODEL_NAME = "qwen2.5-coder:3b"

MAX_REPAIRS = 3


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Quantum Self-Repair Assistant",
    page_icon="⚛️",
    layout="wide"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "execution_history" not in st.session_state:
    st.session_state.execution_history = []

if "last_report" not in st.session_state:
    st.session_state.last_report = None


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def load_benchmark_results():

    if not RESULTS_FILE.exists():
        return []

    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def calculate_metrics(results):

    evaluated = [
        result for result in results
        if not result.get("environment_error", False)
    ]

    total = len(evaluated)

    baseline_passes = sum(
        result.get("baseline_success", False)
        for result in evaluated
    )

    repaired_passes = sum(
        result.get("repaired_success", False)
        for result in evaluated
    )

    initially_failed = sum(
        not result.get("baseline_success", False)
        for result in evaluated
    )

    successful_repairs = sum(
        not result.get("baseline_success", False)
        and result.get("repaired_success", False)
        for result in evaluated
    )

    return {
        "total": total,
        "skipped": len(results) - total,
        "baseline_passes": baseline_passes,
        "repaired_passes": repaired_passes,
        "baseline_rate": (
            baseline_passes / total * 100 if total else 0
        ),
        "repaired_rate": (
            repaired_passes / total * 100 if total else 0
        ),
        "successful_repairs": successful_repairs,
        "repair_rate": (
            successful_repairs / initially_failed * 100
            if initially_failed else 0
        )
    }


def display_report(report):

    st.subheader("Execution Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        if report["success"]:
            st.success("Execution Successful")
        else:
            st.error("Execution Failed")

    with col2:
        st.metric(
            "Repair Attempts",
            report["repair_attempts"]
        )

    with col3:
        st.metric(
            "Maximum Repairs",
            MAX_REPAIRS
        )

    st.markdown("### Generated Code")

    with st.expander("View initial generated code", expanded=False):
        st.code(report["initial_code"], language="python")

    if report["repair_attempts"] > 0:
        st.markdown("### Repaired Code")
        st.code(report["final_code"], language="python")

    else:
        st.markdown("### Final Code")
        st.code(report["final_code"], language="python")

    if report["stdout"]:
        st.markdown("### Program Output")
        st.code(report["stdout"], language="text")

    if not report["success"] and report["stderr"]:
        st.markdown("### Final Error")
        st.error(report["stderr"])

    st.markdown("### Repair History")

    for item in report["history"]:

        attempt = item["attempt"]

        if attempt == 0:
            title = "Initial Generation"
        else:
            title = f"Repair Attempt {attempt}"

        with st.expander(title):

            if item["success"]:
                st.success("Execution successful")
            else:
                st.error("Execution failed")

            st.code(item["code"], language="python")

            if item["stdout"]:
                st.text("Output:")
                st.code(item["stdout"], language="text")

            if item["stderr"]:
                st.text("Error:")
                st.code(item["stderr"], language="text")


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("⚛️ Quantum AI")

    st.caption("LLM-Based Qiskit Self-Repair Assistant")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Home",
            "Quantum Code Assistant",
            "Benchmark Results",
            "Execution History"
        ]
    )

    st.divider()

    st.markdown("### Model Information")

    st.write("**LLM:** Qwen 2.5 Coder")
    st.write("**Parameters:** 3 Billion")
    st.write("**Platform:** Ollama")
    st.write("**Quantum SDK:** Qiskit 2.6.2")
    st.write("**Simulator:** Qiskit Aer 0.18.2")

    st.divider()

    st.caption("Local Quantum Computing Project")


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

if page == "Home":

    st.title("Quantum Self-Repair Assistant")

    st.markdown(
        """
        ### An LLM-Based System for Generating and Self-Repairing Qiskit Code

        This project uses a locally hosted Large Language Model
        to generate Python code for quantum computing tasks.

        When generated code fails during execution, the system
        captures the error and sends it back to the LLM for correction.
        The corrected code is executed again until it succeeds
        or the maximum repair attempts are reached.
        """
    )

    st.divider()

    st.subheader("System Workflow")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**1. User Instruction**\n\nEnter a quantum computing task.")

    with col2:
        st.info("**2. Code Generation**\n\nLLM generates Qiskit code.")

    with col3:
        st.info("**3. Code Execution**\n\nExecute and test the generated code.")

    col1, col2 = st.columns(2)

    with col1:
        st.warning(
            "**4. Error Detection and Repair**\n\n"
            "If execution fails, the error is sent to the LLM "
            "to generate corrected code."
        )

    with col2:
        st.success(
            "**5. Final Output**\n\n"
            "Display the final code, execution output, "
            "and repair history."
        )

    st.divider()

    st.subheader("Benchmark Overview")

    results = load_benchmark_results()

    if results:

        metrics = calculate_metrics(results)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Evaluated Tasks", metrics["total"])
        c2.metric(
            "Baseline Pass Rate",
            f"{metrics['baseline_rate']:.2f}%"
        )
        c3.metric(
            "After Repair",
            f"{metrics['repaired_rate']:.2f}%"
        )
        c4.metric(
            "Successful Repairs",
            metrics["successful_repairs"]
        )

        st.caption(
            f"{metrics['skipped']} task(s) skipped because of "
            "environment dependencies."
        )

    else:
        st.info("Run the benchmark to display its results here.")

    st.divider()

    st.caption(
        "Developed using Python, Qiskit, Qiskit Aer, "
        "Ollama and Streamlit."
    )


# --------------------------------------------------
# QUANTUM CODE ASSISTANT
# --------------------------------------------------

elif page == "Quantum Code Assistant":

    st.title("Quantum Code Assistant")

    st.markdown(
        """
        Enter an instruction describing the quantum program
        you want to create.

        The local LLM will generate the code, execute it,
        and attempt to repair any execution errors.
        """
    )

    task = st.text_area(
        "Enter your quantum computing instruction",
        height=150,
        placeholder=(
            "Example: Create a 2-qubit Bell state circuit. "
            "Apply Hadamard and CNOT gates, measure both qubits, "
            "simulate using 1000 shots and print the counts."
        )
    )

    st.caption(
        f"Model: {MODEL_NAME} | Maximum repair attempts: {MAX_REPAIRS}"
    )

    run_button = st.button(
        "Generate and Execute Code",
        type="primary",
        use_container_width=True
    )

    if run_button:

        if not task.strip():
            st.warning("Please enter a quantum computing instruction.")

        else:

            try:

                with st.spinner(
                    "LLM is generating, executing and repairing code..."
                ):

                    report = run_self_repair(
                        task=task,
                        max_repairs=MAX_REPAIRS,
                        timeout=30
                    )

                st.session_state.last_report = {
                    "task": task,
                    "report": report
                }

                st.session_state.execution_history.insert(
                    0,
                    {
                        "task": task,
                        "report": report
                    }
                )

                st.success("Processing completed.")

            except Exception as error:

                st.error(f"An error occurred: {error}")

    if st.session_state.last_report:

        st.divider()

        display_report(
            st.session_state.last_report["report"]
        )


# --------------------------------------------------
# BENCHMARK RESULTS
# --------------------------------------------------

elif page == "Benchmark Results":

    st.title("Qiskit HumanEval Benchmark")

    st.markdown(
        """
        This section evaluates the LLM's ability to generate
        Qiskit functions using the official Qiskit HumanEval dataset.

        The initial generated functions are tested first.
        Failed functions are then passed through the self-repair loop.
        """
    )

    results = load_benchmark_results()

    if not results:

        st.warning(
            "No benchmark results found. "
            "Run the benchmark from the terminal first."
        )

    else:

        metrics = calculate_metrics(results)

        st.subheader("Performance Metrics")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Evaluated Tasks",
            metrics["total"]
        )

        c2.metric(
            "Baseline Pass Rate",
            f"{metrics['baseline_rate']:.2f}%"
        )

        c3.metric(
            "After Repair Pass Rate",
            f"{metrics['repaired_rate']:.2f}%"
        )

        c4.metric(
            "Repair Success Rate",
            f"{metrics['repair_rate']:.2f}%"
        )

        st.divider()

        st.subheader("Baseline vs After Repair")

        chart_data = {
            "Evaluation": ["Baseline", "After Repair"],
            "Pass Rate (%)": [
                metrics["baseline_rate"],
                metrics["repaired_rate"]
            ]
        }

        st.bar_chart(
            chart_data,
            x="Evaluation",
            y="Pass Rate (%)"
        )

        st.divider()

        st.subheader("Task-wise Results")

        table_data = []

        for result in results:

            table_data.append({
                "Task": result["task_id"],
                "Difficulty": result.get("difficulty", "unknown"),
                "Baseline": (
                    "Passed" if result["baseline_success"]
                    else "Failed"
                ),
                "After Repair": (
                    "Passed" if result["repaired_success"]
                    else "Failed"
                ),
                "Repair Attempts": result["repair_attempts"],
                "Environment Skip": result["environment_error"]
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Individual Task Details")

        for result in results:

            with st.expander(result["task_id"]):

                st.write(
                    "**Difficulty:**",
                    result.get("difficulty", "unknown")
                )

                st.write(
                    "**Baseline:**",
                    "Passed" if result["baseline_success"] else "Failed"
                )

                st.write(
                    "**After Repair:**",
                    "Passed" if result["repaired_success"] else "Failed"
                )

                st.write(
                    "**Repair Attempts:**",
                    result["repair_attempts"]
                )

                if result["environment_error"]:
                    st.warning(
                        "This task was skipped because of a missing "
                        "environment dependency."
                    )

                if result["generated_code"]:
                    st.markdown("**Initial Generated Code**")
                    st.code(
                        result["generated_code"],
                        language="python"
                    )

                if result["repaired_code"]:
                    st.markdown("**Final Code**")
                    st.code(
                        result["repaired_code"],
                        language="python"
                    )

                if result["baseline_error"]:
                    st.markdown("**Initial Error**")
                    st.code(
                        result["baseline_error"],
                        language="text"
                    )

                if result["repair_history"]:
                    st.markdown("**Repair Attempts**")

                    for attempt in result["repair_history"]:

                        st.write(
                            f"Attempt {attempt['attempt']}: "
                            f"{'Passed' if attempt['success'] else 'Failed'}"
                        )

                        if attempt["error"]:
                            st.code(
                                attempt["error"],
                                language="text"
                            )


# --------------------------------------------------
# EXECUTION HISTORY
# --------------------------------------------------

elif page == "Execution History":

    st.title("Execution History")

    history = st.session_state.execution_history

    if not history:

        st.info(
            "No execution history yet. "
            "Generate your first Qiskit program using the assistant."
        )

    else:

        st.write(
            f"Total executions in this session: {len(history)}"
        )

        if st.button("Clear Execution History"):

            st.session_state.execution_history = []
            st.session_state.last_report = None

            st.rerun()

        for index, item in enumerate(history):

            report = item["report"]

            with st.expander(
                f"Execution {len(history) - index}: "
                f"{item['task'][:70]}"
            ):

                st.markdown("**User Instruction**")
                st.write(item["task"])

                display_report(report)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.sidebar.divider()

st.sidebar.caption(
    "Quantum Self-Repair Assistant | Academic Project"
)
