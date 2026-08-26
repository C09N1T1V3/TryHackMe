Network Protocol Analyzer Tool
==============================
- Network Troubleshooting: Diagnosing latency issues, broken handshakes, packet drops, or misconfigurations (e.g., DNS resolution failures).
- Security & Incident Response: Detecting data exfiltration, unauthorized protocol usage, malformed packets, and scanning activity.
- Application Debugging: Inspecting API payloads, verifying encryption behavior (TLS handshakes), and tracking HTTP status codes. 
- Protocol & Traffic Profiling: Mapping network bandwidth consumption, top talkers, and protocol distribution across a subnet.  

tcpdump
-------
- Opensource, lightweight, command line interface, flexible
- Low Overhead & Headless Operation: Runs natively in headless Linux/Unix environments and over SSH with minimal CPU/RAM footprint.
- Berkeley Packet Filter (BPF) Engine: Supports granular target capture (e.g., tcpdump -i eth0 'tcp port 80 and src host 192.168.1.50') to drop unwanted packets before writing to disk.
- Scriptability & Automation: Integrates into bash scripts, Cron jobs, or SIEM pipelines to trigger captures automatically on network alerts.
- Log Rotation & File Control: Built-in flags (-C, -W, -G) allow splitting capture files based on size or time intervals without stopping the process.


wireshark
--------
- Opensource, Graphical User interface, tshark cli version
- Deep Packet Inspection (DPI): Supports protocol dissectors capable of parsing thousands of application-layer protocols down to individual bit flags. 
- Stream Reassembly: Reconstructs full TCP sessions and HTTP/FTP file transfers directly from captured raw bytes.
- Display Filtering (Post-Capture): Offers non-destructive filter expressions (e.g., http.request.method == "POST" || ip.addr == 10.0.0.1) applied dynamically to rendered data.
- Traffic Statistics & Graphing: Generates I/O graphs, flow graphs (visual ladder diagrams), round-trip time (RTT) plots, and protocol hierarchy statistics.
- Decryption Capabilities: Decrypts encrypted payloads (TLS/SSL, IPsec, WPA2/WPA3) when provided with session keys or private RSA keys.  

