🏖️ Towel on the Sunbed: Exploiting Race Conditions in Reward Systems
=======================
Introduction
In this challenge, we explore how a seemingly simple reward mechanism can be abused through race conditions. The scenario is framed as “placing a towel on a sunbed” — once per day, a user can claim a reward. But what happens when multiple requests hit the system at the same time? Let’s break it down.

The Setup: Web Access and Reward Rules
-------------------------------------
- Registration: Users must register before participating.
- Reward Claim: Each user can claim 50 points once every 24 hours.
- Whale Vault Requirement: To access the whale vault, a user needs 150 Ponzi points.

Dashboard Views:
- Before clicking:

  <img width="926" height="370" alt="sunbed_1_user_dashboard" src="https://github.com/user-attachments/assets/a53be975-b2fc-4e8e-b127-68f13e8a28f0" />

- After clicking:

  <img width="920" height="364" alt="sunbed_1_user_after" src="https://github.com/user-attachments/assets/7938ea11-4c9e-4614-aa06-e20c2eed1ac6" />

- At first glance, the system seems straightforward — one claim per day, per user. But the implementation leaves room for exploitation.

The Exploit: Race Condition in Action
-----------------------------------------
- Registered new Account: Created additional users to test the system.
- Intercept Requests: Used a proxy tool like Burp Suite to capture the reward claim request.

  <img width="929" height="185" alt="sunbed_1_intercept" src="https://github.com/user-attachments/assets/5195d662-1573-48a7-84ba-00e70dabfa29" />

- Duplicate Requests: Added the intercepted request to a repeater group and duplicate the tab.

  <img width="847" height="318" alt="sunbed_1_repeater" src="https://github.com/user-attachments/assets/d971928a-6e95-4d2d-af7b-039f74d50cca" />

- Send Parallel Requests: Fired off multiple claim requests simultaneously

  <img width="892" height="346" alt="sunbed_1_parallel_request" src="https://github.com/user-attachments/assets/8d7d13c4-0a4d-4283-aa9e-45579ef85b68" />

- Observe Results: The system processes overlapping claims, allowing multiple rewards within the same 24‑hour window 

  <img width="509" height="178" alt="sunbed_1_result" src="https://github.com/user-attachments/assets/b205f9a9-0e91-4b80-95d2-c94695170e6b" />


Lessons Learned
--------------
- Atomic Operations Matter: Reward systems must ensure that only one claim is processed per user per time window.
- Concurrency Controls: Implement database locks or transaction isolation to prevent duplicate claims.
- Testing Beyond the UI: Security testing should include scenarios where requests are manipulated outside the normal user interface.
