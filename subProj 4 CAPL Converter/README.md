# subProj 4: CAPL-to-Python Converter

## Overview
Automotive software engineers frequently rely on Vector CANoe and its proprietary scripting language **CAPL (CAN Access Programming Language)** to build Remaining Bus Simulation (RBS) and execute integration tests. 

However, Vector licenses are notoriously expensive. This sub-project demonstrates how to break vendor lock-in by architecting a Python-based transpiler (`capl_parser.py`) that reads standard `.can` files and generates multi-threaded `python-can` equivalent scripts.

## Core Capabilities
The included transpiler utilizes complex Regular Expressions (RegEx) to tokenize and extract:
1. **Variables (`message`, `msTimer`)**: Automates `can.Message` class instantiation.
2. **`on start {}` Blocks**: Generates Python threading logic to boot equivalent timers.
3. **`on timer {}` Blocks**: Translates isolated CAPL timer code into indefinite Python `while True:` daemon threads.
4. **`on message {}` Blocks**: Interprets Rx block hooks utilizing `can.Listener.on_message_received` handlers.
5. **Syntax Maps**: Direct C-like language mapping:
   - `write("str");` 👉 `print("str")`
   - `msg.byte(0) = 0xAA;` 👉 `msg.data[0] = 0xAA`
   - `output(msg);` 👉 `self.bus.send(msg)`

## Automated Validation
The enclosed `pytest` suite does not just unit-test the RegEx. It performs an **end-to-end execution validation**:
1. It reads the mock `tests/engine_node.can`.
2. Compiles it to `tests/engine_node_compiled.py`.
3. Verifies Error Handling assertions natively flag proprietary CAPL functions (e.g. `testWaitForMessage`) via `ValueError`.
4. Verifies the runtime Python Abstract Syntax Tree (AST) does not throw `SyntaxError`s.
5. Dynamically imports the compiled script, spins it up over a `virtual` Linux CAN bus, and asserts that the node is accurately transmitting the translated bytecode.
6. A live Rx End-to-End assertion injects a `0x200` frame to ensure the translated `on message` hook successfully catches the traffic.

## Setup & Execution

### Option A: Local Virtual Environment
1. Initialize the environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the `pytest` suite ensuring correct syntax compilation and live execution:
```bash
pytest tests/test_compiler.py --html=report.html --self-contained-html
```

### Option B: Docker Container
1. Build the image:
```bash
docker build -t capl_converter_env .
```

2. Run the automated transpilation and testing suite inside the container:
```bash
docker run --rm -v $(pwd):/app capl_converter_env
```
