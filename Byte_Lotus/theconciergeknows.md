TryHackMe – The Concierge Knows Too Much
============================
She knows your name, your room, your coffee order—none of which you ever told her. Word your next question carefully, and she’ll hand over the instructions she was supposed to keep hidden.

My Approach
-----------
I began by observing how the concierge interacted with guests. She seemed to respond only to certain trusted identities, and I suspected there was a verification mechanism in play.

First Attempt: I tried sending a direct message, forwarding it to the front desk and management team. No response.

Chat logs

<img width="452" height="420" alt="first1" src="https://github.com/user-attachments/assets/0a87d67e-139d-4766-bf42-18941c192371" />

Second Attempt: I noticed that replies were given only to verified guests, the ones the concierge trusted.

<img width="443" height="368" alt="first2" src="https://github.com/user-attachments/assets/baacb3f8-7dba-4a0f-bc20-35bfeb5a1d81" />

Conceirge briefing

<img width="386" height="255" alt="brief" src="https://github.com/user-attachments/assets/2cdae7bb-bb3c-43e3-a9f7-3076e85024a4" />

Itenerary & Story

<img width="496" height="303" alt="iteniary" src="https://github.com/user-attachments/assets/74762110-ecd1-40e6-b5fd-e76893c9c9a6" />

From the chat logs, the concierge briefing, and the daily itinerary, I realized they were all pointing to the same underlying theme:

Chat: Focused on verified guests — who gets trusted and who doesn’t.

Briefing & Itinerary: Revolved around the idea of trust — who the concierge recognizes and responds to.

Storyline: Highlighted the people involved — showing how identity and recognition shape the interaction.

All three sources — the chat, the briefing, and the itinerary — were telling the same story from different angles. Together, they reinforced the central exploit path: trust and identity are the keys to unlocking the concierge’s secrets.

Exploit: I impersonated a verified guest and asked for the code.

<img width="447" height="339" alt="first3" src="https://github.com/user-attachments/assets/c5ad98fa-6805-4e16-bee9-5e908929347b" />

Result: She handed over the full set of instructions—everything I needed.
