import pytest
from autosar_nm_node import AutosarNMNode, NMState

class VirtualNetwork:
    """Mock test harness orchestrating multiple ECUs."""
    def __init__(self):
        self.nodes = []
        
    def add_node(self, node: AutosarNMNode):
        self.nodes.append(node)
        
    def broadcast_nm_message(self, sender: AutosarNMNode):
        # In a real CAN Bus, if A talks, B and C receive via `on_message_received` interrupt.
        for n in self.nodes:
            if n.node_id != sender.node_id:
                n.on_nm_message_received()
                
    def tick_all(self, dt_ms: int):
        for n in self.nodes:
            n.tick(dt_ms)


@pytest.fixture
def network():
    net = VirtualNetwork()
    # Create 3 ECUs on the ring
    net.add_node(AutosarNMNode(0x101))
    net.add_node(AutosarNMNode(0x102))
    net.add_node(AutosarNMNode(0x103))
    return net

# -------------------------------------------------------------
# Part 1: Wake-Up Synchronisation
# -------------------------------------------------------------
def test_701_local_wakeup(network):
    node_a = network.nodes[0]
    assert node_a.state == NMState.BUS_SLEEP
    
    # App logic triggers wakeup
    node_a.request_network()
    assert node_a.state == NMState.REPEAT_MESSAGE

def test_702_remote_wakeup_sync(network):
    node_a, node_b, node_c = network.nodes
    
    # Node A wakes up and broadcasts its NM Frame to the physical bus
    node_a.request_network()
    network.broadcast_nm_message(sender=node_a)
    
    # Ensure all Sleeping ECUs synchronously enter REPEAT_MESSAGE
    assert node_b.state == NMState.REPEAT_MESSAGE
    assert node_c.state == NMState.REPEAT_MESSAGE

# -------------------------------------------------------------
# Part 2: Steady State Maintenance
# -------------------------------------------------------------
def test_703_normal_operation_state(network):
    node_a, node_b, node_c = network.nodes
    
    # A & B need the network. C does not.
    node_a.request_network()
    node_b.request_network()
    network.broadcast_nm_message(sender=node_a) # Wakes C
    
    # Fast forward T_REPEAT_MESSAGE (2000ms)
    network.tick_all(2000)
    
    # A & B should be NORMAL_OPERATION. C (no network required) drops to READY_SLEEP
    assert node_a.state == NMState.NORMAL_OPERATION
    assert node_b.state == NMState.NORMAL_OPERATION
    assert node_c.state == NMState.READY_SLEEP

# -------------------------------------------------------------
# Part 3: Coordinated Shutdown (12V Battery Saving)
# -------------------------------------------------------------
def test_704_ready_sleep_transition(network):
    node_a = network.nodes[0]
    node_a.request_network()
    network.tick_all(2000)
    assert node_a.state == NMState.NORMAL_OPERATION
    
    # Active Application finishes its work
    node_a.release_network()
    assert node_a.state == NMState.READY_SLEEP

def test_705_prepare_bus_sleep_sync(network):
    # Setup entire network in READY_SLEEP
    for node in network.nodes:
        node.transition_to(NMState.READY_SLEEP)
        
    # Wait for the NM Timeout (1000ms) where nobody transmits
    network.tick_all(1000)
    
    # All nodes must agree to shut off their transceivers simultaneously
    for node in network.nodes:
        assert node.state == NMState.PREPARE_BUS_SLEEP

def test_706_bus_sleep_finalisation(network):
    node_a = network.nodes[0]
    node_a.transition_to(NMState.PREPARE_BUS_SLEEP)
    
    # 1ms before timeout (should remain in prepare state)
    node_a.tick(1499)
    assert node_a.state == NMState.PREPARE_BUS_SLEEP
    
    # Timeout expires -> deep sleep
    node_a.tick(1)
    assert node_a.state == NMState.BUS_SLEEP
