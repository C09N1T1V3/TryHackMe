Uncovering the Intrusion: Digital Forensics & Incident Response for "The Vantara Leak"
======================================================================================
When THM Security Services was called in to perform a Digital Forensics & Incident Response (DFIR) investigation for Vantara Financial Group, the initial alert pointed to anomalous authentications that quickly escalated into potential data exfiltration.

By analyzing the forensic artifacts from a compromised endpoint, we mapped out the complete attack lifecycle—from initial access through lateral movement, persistence, and exfiltration.

**1. Initial Access & Pivoting: The Breach Point**
-----------------------------
- The attack chain began with compromised credentials leading to lateral movement across the internal domain.
- Initial Access: The adversary initially gained access using a compromised domain service account: vfg/svc.backup.
- Pivoting: With this service account, the threat actor pivoted deeper into the internal network and established a hold on the target machine.

**2. Unauthorized Account Creation & Activity**
----------------------------------------------
- Once inside, the adversary attempted to establish backup access channels by creating new local accounts.

Identified Unauthorized Accounts
- daniel.avery – Used as the primary context for payload execution and staging.
- helpdesk$ – A domain/local account disguised as a legitimate administrative account to blend into normal enterprise traffic.

Identified Unauthorized Activity
- user discovery cmd
- compressed achieve found
- file accessed
- domain trust reconnaissance check

Forensic Verification: Account creation was verified via Windows Event Logs (Event ID 4720: A user account was created) and by parsing the SAM Registry Hive using EZ Tools' Registry Explorer.

**3. Execution & LOLBin Payload Retrieval**
-----------------------------------------
- After gaining control, the attacker dropped an initial executable disguised as an installer (vpnsetup.exe) to retrieve the secondary payload.

vpnsetup.exe (Downloaded to User Profile)
       │
       ▼
Living-off-the-Land Binary (certutil.exe)
       │
       ▼
Secondary Payload (Disguised as svchosts.exe)

Forensic Analysis: Prefetch & Amcache
- To trace the execution history of vpnsetup.exe, Eric Zimmerman’s PECmd and AmcacheParser were utilized to parse prefetch files and application compatibility caches:

Prefetch Analysis:
```
"DFIR Tools\EZ Tools\PECmd.exe" -d C:\Users\DFIRUser\Vantara-Artefacts\TSS-CASE-001\C\Windows\prefetch\ --csvf parse-pre.csv --csv c:\Users\DFIRUser\
```
Key Finding: Confirmed the execution of vpnsetup.exe originating directly from the Downloads directory of user daniel.avery.

Amcache Analysis:
```
"DFIR Tools\EZ Tools\amcacheparser.exe" -f c:\Users\DFIRUser\Vantara-Artefacts\TSS-CASE-001\c\windows\appcompat\programs\amcache.hve --csvf parse-amcomp.csv --csv c:\Users\DFIRUser\
```
<img width="953" height="364" alt="vantara_0_amcache_hash" src="https://github.com/user-attachments/assets/c413889b-c7da-48a6-a6f1-84a2dbf88022" />

Key Finding: Extracted the file hash (SHA-1) of the executed binary, linking vpnsetup.exe to a Living-off-the-Land Binary (LOLBin) execution via certutil.exe.

Impersonation Technique:
- The downloaded payload was saved as svchosts.exe inside C:\Users\daniel.avery\AppData\Local\Tmp\svchosts.exe, intentionally impersonating the standard Windows service process (svchost.exe).

<img width="922" height="329" alt="vantara_0_lolb_fetch_payload" src="https://github.com/user-attachments/assets/050ad7bd-0668-4426-bf54-5465f22a151c" />

**4. Establishing Persistence**
------------------------------
To ensure continuous access across system reboots, the attacker created a malicious scheduled task masquerading as a routine system update.
- Task Name NameMicrosoftEdgeupdatecore 
- Payload Path C:\Users\daniel.avery\AppData\Local\Tmp\svchosts.exe
- Detection Source $MFT File System Parsing & Registry Hive

<img width="956" height="376" alt="vantara_0_prefetch_exe_download" src="https://github.com/user-attachments/assets/be0535ed-0a3b-4d4b-be4a-df4346941542" />

Forensic Verification
MFT Analysis with MFTECmd:
```
"DFIR Tools\EZ Tools\MFTECmd.exe" -f c:\Users\DFIRUser\Vantara-Artefacts\TSS-CASE-001\C\$MFT --csvf parse-mft.csv --csv c:\Users\DFIRUser\
```
Cross-referencing timestamps in the parsed $MFT CSV revealed file creation events in the System32\Tasks directory matching the timeframe of the payload execution.

<img width="922" height="356" alt="vantara_0_schtask" src="https://github.com/user-attachments/assets/3d01d472-1be1-4189-a1f4-fe40d2f3a88b" />

Registry Analysis with Registry Explorer:
- Parsing the SOFTWARE registry hive confirmed the scheduled task registration:
```
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree\MicrosoftEdgeupdatecore
```


**Remediation & Mitigation Recommendations**
-----------------------------------------
- Service Account Restrictions: Restrict administrative access on service accounts like svc.backup to prevent network pivoting.
- Block LOLBins Execution: Implement AppLocker or Windows Defender Application Control (WDAC) to restrict binaries like certutil.exe from initiating outbound HTTP/FTP connections.
- Monitor Persistence Pathways: Enable auditing for Scheduled Task creation (Event ID 4698) and regularly inspect AppData\Local\Tmp\ for unauthorized binary executions.
