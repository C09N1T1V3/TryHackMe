Kaboom TryHackMe CTF Walkthrough
===============================

<img width="250" height="250" alt="kaboom" src="https://github.com/user-attachments/assets/a4796868-d42c-4750-b03b-f975e3d1ab2a" />

**1. Initial Scenario**
----------------------
- You've been called in to assess an Operational Technology (OT) environment - these are industrial control systems (ICS) like PLCs (Programmable Logic Controllers) that run factories, plants, and critical infrastructure. The challenge simulates a vulnerable OT setup.

**2. 🔍 Network Reconnaissance**
--------------------------------
- First, we need to discover what services are running on the target machine.
```
nmap -sS -p- TARGET_IP
```
<img width="507" height="244" alt="kaboom_0_nmap_port" src="https://github.com/user-attachments/assets/f4973ea2-c5bf-482f-9cce-5c2776da1a71" />

- -sS → Stealth SYN scan (quieter than a full connect scan).
- -p- → Scan all 65,535 ports.

- Always start with a full port scan. OT environments often use uncommon ports (like 502 for Modbus, 44818 for Ethernet/IP).

**3. 📑 Service Enumeration**
-----------------------------
- Once we know which ports are open, we probe deeper:
```
nmap -sS -sC -sV -p 22,80,102,502,1880,8080,44818 TARGET_IP -oN service.txt
```
- -sC → Run default scripts.
- -sV → Detect service versions.
- -oN service.txt → Save results to a file.

- Document everything. Saving results helps you track findings and share them later.

**4. 🌐 Web Access**
--------------------
- Checking the web interface:
- Port 80 → Default web service.
```
Found PLC CCTV interface at: http://TARGET_IP/
```
<img width="920" height="335" alt="kaboom_0_web1_home" src="https://github.com/user-attachments/assets/9393de0f-a9a6-4de6-bf6c-bff8d2fded79" />

- Always explore web services. OT devices often expose management panels with weak or default credentials.

**5. ⚙️ Modbus Interaction**
----------------------------
- Modbus is a common ICS protocol (port 502). You can interact with registers and coils (binary values controlling devices).
- Reading registers and coil values: [Recon script](kaboom/recon.py)

<img width="509" height="154" alt="kaboom_1_modbus_recon" src="https://github.com/user-attachments/assets/42448eda-edec-40e4-90a0-3b25794bcc70" />

- Updating registers and coil values: [Update script](kaboom/update.py)

<img width="496" height="127" alt="kaboom_1_modbus_update" src="https://github.com/user-attachments/assets/515f6ed6-569b-481b-b220-8b6dd61eb74d" />

- Understand the difference:
- Holding registers → store values (like temperature).
- Coils → binary switches (on/off).

- Always test read operations before attempting writes - writing can disrupt processes in real OT systems.

**6. 💥 Exploitation**
-----------------------
- By manipulating registers and coils, you can simulate unsafe changes in the plant environment - leading to the "Exploded Plant" scenario.

<img width="884" height="332" alt="kaboom_1_modbus_explosion" src="https://github.com/user-attachments/assets/3ae78e5e-11c5-4482-a3fd-065250cab40c" />

---

For More Details Room about Modbus
TryHackMe | [ICS/Modbus](https://tryhackme.com/room/ICS-modbus-aoc2025-g3m6n9b1v4) - Claus for Concern
