class NMState:
    BUS_SLEEP = "Bus-Sleep"
    PREPARE_BUS_SLEEP = "Prepare-Bus-Sleep"
    REPEAT_MESSAGE = "Repeat-Message"
    NORMAL_OPERATION = "Normal-Operation"
    READY_SLEEP = "Ready-Sleep"

class AutosarNMNode:
    """
    Mock AUTOSAR Network Management Node.
    Manages complex state transitions based on local application requirements and remote CAN callbacks.
    """
    def __init__(self, node_id: int, pn_cluster: int = 1):
        self.node_id = node_id
        self.pn_cluster = pn_cluster  # Partial Networking Identifier
        self.state = NMState.BUS_SLEEP
        
        self.network_requested_locally = False
        self.active_wakeup = False  # CBV Flag: Did I wake the bus, or was I woken?
        
        # Simulated Timers in milliseconds
        self.timer_repeat_message = 0
        self.timer_nm_timeout = 0
        self.timer_wait_bus_sleep = 0
        
        # Configuration constants
        self.T_REPEAT_MESSAGE = 2000
        self.T_NM_TIMEOUT = 1000
        self.T_WAIT_BUS_SLEEP = 1500

    def request_network(self):
        """Active Application requests the network to wake up (Local WakeUp)."""
        self.network_requested_locally = True
        if self.state in [NMState.BUS_SLEEP, NMState.PREPARE_BUS_SLEEP]:
            self.active_wakeup = True  # We initiated the wakeup
            self.transition_to(NMState.REPEAT_MESSAGE)
        elif self.state == NMState.READY_SLEEP:
            self.transition_to(NMState.NORMAL_OPERATION)

    def release_network(self):
        """Active Application no longer needs the network (allows sleep)."""
        self.network_requested_locally = False
        if self.state == NMState.NORMAL_OPERATION:
            self.transition_to(NMState.READY_SLEEP)

    def on_nm_message_received(self, target_pn_cluster: int, cbv_active_wakeup_bit: bool):
        """Callback: A remote NM PDU was received over the CAN bus."""
        # Partial Networking Check
        if target_pn_cluster != self.pn_cluster:
            return  # Ignore messages not targeted at our cluster
            
        if self.state in [NMState.BUS_SLEEP, NMState.PREPARE_BUS_SLEEP]:
            # Remote wakeup triggers us to wake up synchronously
            self.active_wakeup = False  # We were woken passively by someone else
            self.transition_to(NMState.REPEAT_MESSAGE)
        else:
            # If we are awake, this just resets the shutdown timeout
            self.restart_nm_timeout()

    def transition_to(self, new_state: str):
        """Handles entry actions for states."""
        self.state = new_state
        
        if self.state == NMState.REPEAT_MESSAGE:
            self.timer_repeat_message = self.T_REPEAT_MESSAGE
            self.restart_nm_timeout()
        elif self.state == NMState.NORMAL_OPERATION:
            self.restart_nm_timeout()
        elif self.state == NMState.READY_SLEEP:
            self.restart_nm_timeout()
        elif self.state == NMState.PREPARE_BUS_SLEEP:
            self.timer_wait_bus_sleep = self.T_WAIT_BUS_SLEEP
            
    def restart_nm_timeout(self):
        """Resets the timer that will force a shutdown if no one talks."""
        self.timer_nm_timeout = self.T_NM_TIMEOUT

    def tick(self, dt_ms: int):
        """Main loop executed by the OS task scheduler."""
        if self.state == NMState.REPEAT_MESSAGE:
            self.timer_repeat_message -= dt_ms
            if self.timer_repeat_message <= 0:
                if self.network_requested_locally:
                    self.transition_to(NMState.NORMAL_OPERATION)
                else:
                    self.transition_to(NMState.READY_SLEEP)
                    
        elif self.state in [NMState.NORMAL_OPERATION, NMState.READY_SLEEP]:
            self.timer_nm_timeout -= dt_ms
            if self.timer_nm_timeout <= 0:
                # Nobody has talked in a while, network is silent. Shut down.
                self.transition_to(NMState.PREPARE_BUS_SLEEP)
                
        elif self.state == NMState.PREPARE_BUS_SLEEP:
            self.timer_wait_bus_sleep -= dt_ms
            if self.timer_wait_bus_sleep <= 0:
                self.transition_to(NMState.BUS_SLEEP)
