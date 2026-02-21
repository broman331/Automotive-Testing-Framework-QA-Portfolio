import pytest
import os
import sys
import time
import can

# Add parent directory to sys.path to import capl_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from capl_parser import CAPLParser

# Constants
CAN_FILE = os.path.join(os.path.dirname(__file__), 'engine_node.can')
PY_OUT_FILE = os.path.join(os.path.dirname(__file__), 'engine_node_compiled.py')

@pytest.fixture(scope="module")
def transpiler():
    parser = CAPLParser(CAN_FILE)
    yield parser

class TestCAPLCompiler:

    # ----------------------------------------------------
    # PART 1: Lexical Scope & Regex Parsing Validation
    # ----------------------------------------------------

    def test_variable_extraction(self, transpiler):
        """TC-401 - Validate regex extracts variables and message definitions."""
        transpiler.extract_blocks()
        assert 'msg_engine' in transpiler.variables
        assert transpiler.variables['msg_engine'] == '0x100'
        assert 'myTimer' in transpiler.timers

    def test_event_block_extraction(self, transpiler):
        """TC-402 - Validate regex correctly segregates CAPL event blocks."""
        transpiler.extract_blocks()
        # Ensure block lines are found correctly
        assert len(transpiler.on_start) > 0
        assert any("setTimer" in s for s in transpiler.on_start)
        assert 'myTimer' in transpiler.on_timer
        assert any("output" in s for s in transpiler.on_timer['myTimer'])

    def test_syntax_substitution(self, transpiler):
        """TC-403 - Validate C-like syntax mapping to Python equivalents."""
        res = transpiler.translate_syntax('msg_engine.byte(0) = 0xAA')
        assert res == 'msg_engine.data[0] = 0xAA'
        
        res = transpiler.translate_syntax('output(msg_engine)')
        assert res == 'self.bus.send(msg_engine)'

    # ----------------------------------------------------
    # PART 2: End-to-End Compilation and Live Execution
    # ----------------------------------------------------

    def test_end_to_end_compilation(self, transpiler):
        """TC-404 - Write compiled script to disk and ensure it builds."""
        if os.path.exists(PY_OUT_FILE):
            os.remove(PY_OUT_FILE)
            
        transpiler.generate_python(PY_OUT_FILE)
        assert os.path.exists(PY_OUT_FILE)
        
        # Test if the generated Python file contains syntax errors
        with open(PY_OUT_FILE, 'r') as f:
            code = f.read()
            # This throws SyntaxError if the compiled code is invalid python
            compile(code, PY_OUT_FILE, 'exec') 

    def test_live_bus_simulation(self):
        """TC-405 - Spin up the compiled node and assert it transmits on vca0."""
        # Note: In a true CI environment this might require root or mock interfaces
        # Our compiled code targets 'virtual' interface which python-can supports natively
        
        # 1. Dynamically import the compiled code!
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine_node_compiled", PY_OUT_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 2. Start the node
        node = module.CAPLNode(channel='test_capl_bus')
        node.start()
        
        # 3. Assert functionality using python-can listener
        monitor_bus = can.Bus(channel='test_capl_bus', interface='virtual')
        
        msgs_received = 0
        end_time = time.time() + 0.1 # Run for 100ms
        
        try:
            while time.time() < end_time:
                msg = monitor_bus.recv(timeout=0.01)
                if msg and msg.arbitration_id == 0x100:
                    assert msg.data[0] == 0xAA
                    assert msg.data[1] == 0xBB
                    msgs_received += 1
        finally:
            node.stop()
            monitor_bus.shutdown()
            
        # At 20ms polling over 100ms, we expect roughly ~4-5 messages
        assert msgs_received >= 3
