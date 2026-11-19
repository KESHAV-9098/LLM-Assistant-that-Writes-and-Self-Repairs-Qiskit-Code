
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Step 1: Create a circuit with 2 qubits
qc = QuantumCircuit(2, 2)

# Step 2: Apply Hadamard gate to qubit 0
qc.h(0)

# Step 3: Apply CNOT gate
qc.cx(0, 1)

# Step 4: Measure both qubits
qc.measure([0, 1], [0, 1])

# Step 5: Display the circuit
print("Bell State Quantum Circuit:")
print(qc.draw())

# Step 6: Simulate the circuit
simulator = AerSimulator()

job = simulator.run(qc, shots=1000)
result = job.result()

# Step 7: Display measurement results
counts = result.get_counts()

print("\nMeasurement Results:")
print(counts)
