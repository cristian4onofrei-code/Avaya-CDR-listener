import socket
import datetime
import os
import re
import time

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5144
LOG_DIR = '/var/log/avaya_cdr'

# Filter to ensure we only log when actual agents answer/rona, not hunt groups or external numbers
# '\d{4}' means exactly 4 digits (e.g., 1002, 1003). 
# AGENT_EXT_PATTERN = r'^\d{4}$' 
AGENT_EXT_PATTERN = r'^(75|10)\d{2}$'
# ---------------------

active_calls = {}
last_cleanup = time.time()

def clean_stale_calls():
    """Removes calls older than 1 hour to prevent memory leaks."""
    global last_cleanup
    current_time = time.time()
    if current_time - last_cleanup > 60:
        stale_keys = [k for k, v in active_calls.items() if current_time - v['last_update'] > 3600]
        for k in stale_keys:
            del active_calls[k]
        last_cleanup = current_time

def start_udp_listener():
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except PermissionError:
            print(f"[!] Error: No permission to create {LOG_DIR}. Run with sudo.")
            return

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        print(f"[*] Stateful Session Manager Listener started on port {PORT}...")
        print(f"[*] Filtering for {AGENT_EXT_PATTERN} agent lengths...")

        while True:
            data, addr = s.recvfrom(65535)
            message = data.decode('utf-8', errors='ignore')
            
            clean_stale_calls()

            # --- 1. EXTRACT GLOBAL SESSION ID ---
            session_match = re.search(r'Av-Global-Session-ID:\s*([a-zA-Z0-9-]+)', message, re.IGNORECASE)
            if not session_match:
                continue

            session_id = session_match.group(1).strip()

            if session_id not in active_calls:
                active_calls[session_id] = {
                    'caller': 'Unknown',
                    'targets': [], 
                    'logged_events': set(),
                    'last_update': time.time()
                }
            else:
                active_calls[session_id]['last_update'] = time.time()

            call = active_calls[session_id]

            # --- 2. EXTRACT CALLER ID ---
            if call['caller'] == 'Unknown':
                from_match = re.search(r'From:.*?[sS][iI][pP][sS]?:([^@;>:]+)', message)
                if from_match:
                    call['caller'] = from_match.group(1).strip()

            # --- 3. TRACK ROUTING TARGETS (HUNT GROUPS & VDNS) ---
            if message.startswith("INVITE sip:") or "CSeq: 1 INVITE" in message:
                req_uri_match = re.search(r'INVITE\s+sips?:([^@;> ]+)', message)
                if req_uri_match:
                    target = req_uri_match.group(1).strip()
                    if target not in call['targets']:
                        call['targets'].append(target)

            # --- 4. CHECK FOR CALL RESOLUTION (RONA OR ANSWER) ---
            event_type = None
            final_agent = None

            if message.startswith("CANCEL sip:") or "CSeq: 1 CANCEL" in message:
                cancel_match = re.search(r'CANCEL\s+sips?:([^@;> ]+)', message)
                if cancel_match:
                    final_agent = cancel_match.group(1).strip()
                    event_type = "RONA    "

            elif "SIP/2.0 200 OK" in message and "CSeq: 1 INVITE" in message:
                to_match = re.search(r'To:.*?[sS][iI][pP][sS]?:([^@;>:]+)', message)
                if to_match:
                    final_agent = to_match.group(1).strip()
                    event_type = "ANSWERED"

            # --- 5. LOG THE CONSOLIDATED RECORD ---
            if event_type and final_agent:
                
                # STRICT FILTER: Only proceed if the entity answering/RONAing is a 4-digit agent
                if not re.match(AGENT_EXT_PATTERN, final_agent):
                    continue
                
                event_signature = f"{final_agent}_{event_type}"
                if event_signature in call['logged_events']:
                    continue

                # The VDN is typically the very first target SM was asked to route to
                vdn = call['targets'][0] if call['targets'] else "Unknown_VDN"
                
                # If someone dialed the agent directly (no VDN), make it clear in the log
                if vdn == final_agent:
                    vdn = "Direct_Call"

                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.datetime.now().strftime("%H:%M:%S")

                csv_line = f"{date_str},{time_str},{call['caller']},{vdn},{final_agent},{event_type},{session_id}"
                
                log_file = os.path.join(LOG_DIR, f"sip_events_{date_str}.csv")
                
                try:
                    with open(log_file, "a") as f:
                        f.write(csv_line + "\n")
                    
                    print(f"Logged: {csv_line}")
                    call['logged_events'].add(event_signature)
                
                except Exception as e:
                    print(f"[!] FAILED TO WRITE TO FILE: {e}")

if __name__ == "__main__":
    try:
        start_udp_listener()
    except KeyboardInterrupt:
        print("\n[*] Listener stopped manually.")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")
