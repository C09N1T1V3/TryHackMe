TryHackMe – Room 404 Walkthrough
===============================
Introduction
Room 404 is not your typical room. It doesn’t appear on the floor plan, brochure, or even the doors. But port 8080 is wide open, and sometimes the rooms that aren’t listed are the ones worth exploring.

🌐 Web Access
-------------
Target URL:
```
http://TARGET_IP:8080
```
Initial exploration of the homepage revealed nothing useful.

<img width="842" height="335" alt="room404_1_web_home" src="https://github.com/user-attachments/assets/7906e7a2-7966-4161-97e3-1f3b12933c3e" />

📂 Directory Enumeration
------------------------
Using Gobuster to enumerate directories:
```
gobuster dir -u http://TARGET_IP:8080 -w /usr/share/wordlists/dirb/common.txt -z
```
Results:
```
===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://TARGET_IP:8080
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/common.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/.git/HEAD            (Status: 200) [Size: 21]
===============================================================
Finished
===============================================================
```
A hidden .git directory was discovered.

<img width="791" height="272" alt="room404_1_hidden_dir" src="https://github.com/user-attachments/assets/7719ff8d-f4da-43f1-896c-594ab7fa8fe1" />

🔎 Exploring the .git Directory
-------------------------------
Instead of manually clicking each link, I noted down all available paths:
```
http://TARGET_IP:8080/.git/COMMIT_EDITMSG
```
Files were downloaded one by one using their absolute paths.

<img width="571" height="355" alt="room404_1_file_download" src="https://github.com/user-attachments/assets/267ff757-f1ac-4c29-92c5-48e07e7aba4d" />

📑 File Enumeration
-------------------
After reviewing the files, most seemed unhelpful. One file stood out — a hash-like filename:
```
file 12caa4e52a965e89e5eccf5760924b21aacbf7
```
result
```
12caa4e52a965e89e5eccf5760924b21aacbf7: zlib compressed data
```

🗜️ Extracting Zlib Data
------------------------
To handle the compressed file, I installed qpdf:
```
apt install qpdf
```
Then extracted the contents using:
```
zlib-flate -uncompress < 12caa4e52a965e89e5eccf5760924b21aacbf7 > output.txt
```
Alternatively, Python’s zlib module works too:
```
python3 -c "import zlib,sys; sys.stdout.buffer.write(zlib.decompress(sys.stdin.buffer.read()))" < 12caa4e52a965e89e5eccf5760924b21aacbf7 > output.txt
````

🎯 Flag Found
-------------
Among the extracted files, one contained the flag — mission accomplished!

✨ Key Takeaways
----------------
- Always check for hidden directories like .git — they often contain sensitive information.
- Compressed files may hide critical data; tools like zlib-flate or Python’s zlib module are invaluable.
- Enumeration and persistence are the keys to uncovering hidden flags.
