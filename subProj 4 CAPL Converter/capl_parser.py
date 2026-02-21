import re
import os

class CAPLParser:
    """
    A transpiler that reads a proprietary CAPL (.can) file and compiles it into 
    an open-source python-can script utilizing threading and time.sleep()
    """
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.content = f.read()
            
        self.variables = {}
        self.timers = []
        self.on_start = []
        self.on_timer = {}
        self.on_message = {}

    def extract_blocks(self):
        """Uses Regex to strip comments and extract logical execution blocks."""
        # Remove C-style comments
        clean_content = re.sub(r'/\*.*?\*/', '', self.content, flags=re.DOTALL)
        
        # 1. Extract Variables block
        var_match = re.search(r'variables\s*\{([^}]*)\}', clean_content, re.DOTALL)
        if var_match:
            vars_block = var_match.group(1).strip()
            # Find messages: "message 0x100 msg_engine;" -> {'msg_engine': '0x100'}
            for msg_match in re.finditer(r'message\s+(0x[0-9A-Fa-f]+|\d+)\s+([a-zA-Z0-9_]+);', vars_block):
                self.variables[msg_match.group(2)] = msg_match.group(1)
            # Find timers: "msTimer myTimer;" -> ['myTimer']
            for timer_match in re.finditer(r'msTimer\s+([a-zA-Z0-9_]+);', vars_block):
                self.timers.append(timer_match.group(1))

        # 2. Extract on start block
        start_match = re.search(r'on start\s*\{([^}]*)\}', clean_content, re.DOTALL)
        if start_match:
            self.on_start = [line.strip() for line in start_match.group(1).strip().split(';') if line.strip()]

        # 3. Extract on timer blocks
        for timer in self.timers:
            timer_regex = rf'on timer\s+{timer}\s*\{{([^}}]*)\}}'
            timer_match = re.search(timer_regex, clean_content, re.DOTALL)
            if timer_match:
                self.on_timer[timer] = [line.strip() for line in timer_match.group(1).strip().split(';') if line.strip()]

        # 4. Extract on message blocks
        for msg_match in re.finditer(r'on message\s+(0x[0-9A-Fa-f]+|\d+)\s*\{([^}]*)\}', clean_content, re.DOTALL):
            msg_id_val = int(msg_match.group(1), 16) if '0x' in msg_match.group(1).lower() else int(msg_match.group(1))
            self.on_message[msg_id_val] = [line.strip() for line in msg_match.group(2).strip().split(';') if line.strip()]

    def translate_syntax(self, line):
        """Translates single CAPL C-like statements into Python syntax."""
        # Unsupported Proprietary Error Handling
        if "testWaitForMessage" in line:
            raise ValueError(f"Unsupported proprietary CAPL keyword found: {line}")
            
        # Translate CAPL writes -> Python prints (with logging capability)
        line = re.sub(r'write\("([^"]+)"\)', r'print("\1")', line)
        
        # Translate CAPL setTimer(timer_name, 20) -> self.running = True (Logic handled in thread loop)
        line = re.sub(r'setTimer\(([a-zA-Z0-9_]+),\s*(\d+)\)', r'# \1 period = \2ms', line)
        
        # Translate CAPL msg.byte(0) = 0xAA -> msg.data[0] = 0xAA
        line = re.sub(r'([a-zA-Z0-9_]+)\.byte\((\d+)\)\s*=\s*(0x[0-9A-Fa-f]+|\d+)', r'\1.data[\2] = \3', line)
        
        # Translate CAPL output(msg) -> self.bus.send(msg)
        line = re.sub(r'output\(([a-zA-Z0-9_.]+)\)', r'self.bus.send(\1)', line)
        
        return line

    def generate_python(self, output_file=None):
        self.extract_blocks()
        
        lines = [
            "import time",
            "import threading",
            "import can",
            "",
            "class CAPLNode(can.Listener):",
            "    def __init__(self, channel='vcan0'):",
            "        self.bus = can.interface.Bus(channel=channel, interface='virtual')",
            "        self.running = False",
            "        self.threads = []",
            ""
        ]
        
        # Initialize Variables (Messages)
        for msg_name, msg_id in self.variables.items():
            lines.append(f"        # Message Initialization from CAPL variable")
            lines.append(f"        self.{msg_name} = can.Message(arbitration_id={msg_id}, data=[0]*8, is_extended_id=False)")
        
        lines.append("")
        
        # Create start function mapping 'on start'
        lines.append("    def start(self):")
        lines.append("        self.running = True")
        lines.append("        self.notifier = can.Notifier(self.bus, [self])")
        for line in self.on_start:
            translated = self.translate_syntax(line)
            lines.append(f"        {translated}")
            
            # Catch setTimer statements in on_start to spawn threads
            timer_match = re.search(r'setTimer\(([a-zA-Z0-9_]+),\s*(\d+)\)', line)
            if timer_match:
                t_name, t_val = timer_match.groups()
                lines.append(f"        t = threading.Thread(target=self._{t_name}_loop, args=({int(t_val)/1000},))")
                lines.append(f"        self.threads.append(t)")
                lines.append(f"        t.start()")
                
        lines.append("")
        
        # Create daemon loops for 'on timer' blocks
        for timer_name, block in self.on_timer.items():
            lines.append(f"    def _{timer_name}_loop(self, period_sec):")
            lines.append(f"        while self.running:")
            lines.append(f"            time.sleep(period_sec)")
            for line in block:
                # Need to namespace message variables to self.msg_name
                for msg_name in self.variables.keys():
                    line = re.sub(rf'\b{msg_name}\b', f'self.{msg_name}', line)
                translated = self.translate_syntax(line)
                lines.append(f"            {translated}")
            lines.append("")
            
        # Map on message (Rx handlers)
        lines.append("    def on_message_received(self, msg):")
        if not self.on_message:
            lines.append("        pass")
        else:
            for msg_id, block in self.on_message.items():
                lines.append(f"        if msg.arbitration_id == {msg_id}:")
                for line in block:
                    for msg_name in self.variables.keys():
                        line = re.sub(rf'\b{msg_name}\b', f'self.{msg_name}', line)
                    translated = self.translate_syntax(line)
                    lines.append(f"            {translated}")
        
        lines.append("")

        lines.append("    def stop(self):")
        lines.append("        if not self.running: return")
        lines.append("        self.running = False")
        lines.append("        if hasattr(self, 'notifier'): self.notifier.stop()")
        lines.append("        for t in self.threads:")
        lines.append("            t.join()")
        lines.append("        self.bus.shutdown()")
        lines.append("")
        
        lines.append("if __name__ == '__main__':")
        lines.append("    node = CAPLNode()")
        lines.append("    node.start()")
        lines.append("    try:")
        lines.append("        while True: time.sleep(1)")
        lines.append("    except KeyboardInterrupt:")
        lines.append("        node.stop()")
        
        final_code = "\n".join(lines)
        if output_file:
            with open(output_file, 'w') as f:
                f.write(final_code)
        
        return final_code

if __name__ == "__main__":
    parser = CAPLParser('tests/engine_node.can')
    print("--- Transpiling engine_node.can ---")
    print(parser.generate_python())
