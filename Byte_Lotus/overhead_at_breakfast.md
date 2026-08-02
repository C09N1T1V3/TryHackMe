Overheard at Breakfast: OSINT Meets CTF
=======================================
Two strangers. One conversation. One profile they never meant to reveal. This challenge was a fascinating blend of OSINT techniques, AI prompts, and a bit of command-line decoding. Here’s how I approached it step by step.

Step 1: Conversion Analysis
--------------------------
Email extracted from the conversation "lambobytelotushotel@gmail.com"

Step 2: OSI Platform Exploration
-------------------------------
For the initial reconnaissance, I leveraged the OSI platform tool [holehe](https://github.com/megadose/holehe).

Holehe is a Python-based utility that checks if an email address is linked to accounts on various platforms — a perfect fit for this challenge.

Alternatively, I experimented with AI prompts to guide the search. The key clue was:
```
free tool started with G alphabet allow profile update and link other media accounts
```
<img width="266" height="241" alt="breakfast_0_AI_osi" src="https://github.com/user-attachments/assets/61f0a42f-ca40-4eab-8ced-65c6a7272be7" />

This pointed toward Gravatar, a free service that lets users update a profile and link it across multiple platforms.

Step 3: Email Finder
--------------------
With holehe installed, I ran the following commands:
```
pip3 install holehe
holehe lambobytelotushotel@gmail.com
```
<img width="557" height="252" alt="breakfast_0_osi_email_finder" src="https://github.com/user-attachments/assets/1201c433-e1b6-4f9a-b42b-b6195470bd22" />

The results confirmed the email was tied to a Gravatar profile.

Step 4: Verifying the Profile
-----------------------------
Next, I visited the Gravatar URL:
```
https://gravatar.com/[redacted]
```
This redirected to the user’s Gravatar profile.

<img width="847" height="354" alt="breakfast_1_gravatar_profile" src="https://github.com/user-attachments/assets/a3e46982-dd1f-4023-be16-aae66bd424ab" />

Step 5: Cracking the Base64
---------------------------
The final piece was decoding the Base64 string.

Using either CyberChef or the Linux CLI, I decoded it:
```
echo "redacted" | base64 -d
```
This revealed the hidden flag.

Recommendations
---------------
- Leverage OSINT utilities: Tools like holehe are invaluable for quickly mapping email addresses to platforms.
- Base64 encoding tool
