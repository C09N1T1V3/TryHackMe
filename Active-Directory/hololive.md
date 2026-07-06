
Hololive

How to enumerate, exploit misconfiguration and vul; Defend against Attack Chain
web exploitation -> initial access -> enumeration -> privilege escalation/lateral movement -> Bypass -> Persistance -> Goal

Some topics will be explore

.NET basics
Web application exploitation
AV evasion
Whitelist and container escapes
Pivoting
Operating with a C2 (Command and Control) Framework
Post-Exploitation
Situational Awareness
Active Directory attacks

Some attacks and misconfigurations
Misconfigured sub-domains
Local file Inclusion
Remote code execution
Docker containers
SUID binaries
Password resets
Client-side filters
AppLocker
Vulnerable DLLs
Net-NTLMv2 / SMB

Starting with nmap network mapper, reliable and fast for scanning the target ports and services

we have scope-of-engagement
nmap -sn 192.168.100.0/24

nmap -sn 10.200.65.0/24
scanning all the 254 hosts, 
-sn for live host discovery

Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-07-06 07:30 UTC
Nmap scan report for ip-10-200-65-33.eu-west-3.compute.internal (10.200.65.33)
Host is up (0.024s latency).
Nmap scan report for ip-10-200-65-250.eu-west-3.compute.internal (10.200.65.250)
Host is up (0.021s latency).
Nmap done: 256 IP addresses (2 hosts up) scanned in 6.46 seconds

found 2 live host

enumerating each host individually, this time port and service enumeration
nmap -sS -sC -sV -p- 10.200.65.33

sS Stealth scan
sV scans for service and version
sC runs a script scan against open ports.
-p- scans all ports 0 - 65535

