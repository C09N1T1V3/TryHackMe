Walkthrough: Solving TryHackMe’s Traverse Challenge
====================================================
In this walkthrough, we examine Traverse, a security challenge centered on restoring a compromised web application. We cover the entire attack chain—from initial reconnaissance to code deobfuscation.

Phase 1: Reconnaissance & Directory Enumeration
-----------------------------------------------
```
http://TARGET_IP/
```
<img width="938" height="347" alt="traverse_0_index" src="https://github.com/user-attachments/assets/27a85faf-a352-4ce6-81b5-caa39e4037ff" />

The target web application appears compromised from the start.

To map out hidden assets, we run a directory brute-force scan using Gobuster:
```
gobuster dir -u http://TARGET_IP/ -w /usr/share/wordlists/dirb/common.txt -z
```
result:
```
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.130.131.231/
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/common.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/.hta                 (Status: 403) [Size: 279]
/.htpasswd            (Status: 403) [Size: 279]
/api                  (Status: 301) [Size: 314] [--> http://10.130.131.231/api/]
/.htaccess            (Status: 403) [Size: 279]
/client               (Status: 301) [Size: 317] [--> http://10.130.131.231/client/]
/img                  (Status: 301) [Size: 314] [--> http://10.130.131.231/img/]
/index.php            (Status: 200) [Size: 1491]
/javascript           (Status: 301) [Size: 321] [--> http://10.130.131.231/javascript/]
/logs                 (Status: 301) [Size: 315] [--> http://10.130.131.231/logs/]
/phpmyadmin           (Status: 301) [Size: 321] [--> http://10.130.131.231/phpmyadmin/]
/server-status        (Status: 403) [Size: 279]
===============================================================
Finished
===============================================================
```
Checking /logs/ reveals an internal communication email between two users (Bob and Mark): http://TARGET_IP/logs/
```
From: Bob <bob@tourism.mht>
To: Mark <mark@tourism.mht>
Subject: API Credentials

Hey Mark,

Sorry I had to rush earlier for the holidays, but I have created the directory for you with all the required information for the API.
You loved SSDLC so much, I named the API folder under the name of the first phase of SSDLC.
This page is password protected and can only be opened through the key. THM{redacted}

See ya after the holidays

Bob.
```
Key Takeaways:
- Directory Hint: The first phase of the Secure Software Development Life Cycle (SSDLC) is Requirements (or Planning / Requirement Analysis).
- Access Key: The flag/key retrieved from the log unlocks access to this protected API endpoint.

Phase 2: Exploiting Insecure Direct Object References (IDOR)
------------------------------------------------------------
- Navigating to the identified endpoint reveals an Insecure Direct Object Reference (IDOR) vulnerability:

<img width="927" height="342" alt="traverse_1_customer_api" src="https://github.com/user-attachments/assets/4b716b93-9be6-4848-973c-509a95edb81b" />

- Querying user/customer API endpoints exposes user credentials across the database.

<img width="762" height="277" alt="traverse_1_admin_api" src="https://github.com/user-attachments/assets/b6a2a62f-eb7e-42d2-9309-54dfd1fba09e" />

- Pivoting through endpoint parameters grants access to administrative credentials via the admin API.

Phase 3: Privilege Escalation & Command Injection
-------------------------------------------------
- Using the extracted administrative credentials, we log in to access the administrative dashboard (main.php).

<img width="945" height="380" alt="traverse_1_admin_dashboard" src="https://github.com/user-attachments/assets/4454a042-d281-4c74-a3e5-2af77a7fdc5b" />

Exploitation Steps:
- Identify a post-execution function available within the admin panel.
- Intercept the HTTP POST request using the browser's Developer Tools (Network tab) or Burp Suite.
- Edit and resend the payload appended to the HTTP request body to trigger Command Injection.
- Use shell execution commands to inspect local system files and discover the location of the internal file manager.

<img width="951" height="387" alt="traverse_1_command_inj" src="https://github.com/user-attachments/assets/f68854dd-ea21-426b-955e-bf2392a9c569" />

Phase 4: Web File Manager Analysis & Deobfuscation
-------------------------------------------------
Navigating to the web file manager uncovered during post-exploitation reveals key application scripts containing heavily obfuscated JavaScript.

<img width="902" height="325" alt="traverse_1_file_manager" src="https://github.com/user-attachments/assets/b2e2506a-e81c-47d5-ba2e-0f253be904a5" />

Web-File Manager
<img width="926" height="399" alt="traverse_1_web_manager" src="https://github.com/user-attachments/assets/d07cc02e-a1e5-4578-a15f-402e6329f588" />

Deobfuscation Flow:
- Extract the raw JavaScript snippet from the file manager interface.

<img width="603" height="315" alt="traverse_1_obfuscated_js" src="https://github.com/user-attachments/assets/8892c1ec-4968-4968-810b-8f57c5b6bd07" />

- Load the payload into CyberChef.
- Apply reverse hex clean the code.

<img width="955" height="364" alt="traverse_1_deobfuscated_js" src="https://github.com/user-attachments/assets/7745206c-e24c-4e79-b063-f039add6f1c4" />

- Analyze the deobfuscated source code to identify hardcoded flag.

Recommendations
---------------
- Fix Command Injection: Remove system execution functions (exec(), system()) in administrative tools. Use safe, built-in language APIs or enforce strict input allowlists.
- Remediate IDOR & Secure APIs: Enforce strict session-based, object-level authorization on all API endpoints. Replace sequential IDs with randomized UUIDs to prevent directory and resource enumeration.
- rotect Sensitive Logs & Assets: Disable directory listing and restrict public access to sensitive administrative folders like /logs/. Scrub credentials and tokens from all application logs.
- Harden Administrative Interfaces: Restrict admin dashboard access behind Multi-Factor Authentication (MFA) and IP allowlisting. Store secrets in environment variables rather than client-side JavaScript.
