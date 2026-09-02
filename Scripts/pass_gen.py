import sys
# Define character sets
digits = "0123456789"
specials = "!@#$%^&*"
years = [str(y) for y in range(2000, 2100)]

# Read input file from terminal argument
input_file = sys.argv[1]

with open(input_file, "r") as f:
    for line in f:
        word = line.strip()
        if not word:
            continue

        # 1. word + digit + special (e.g., word0!)
        for d in digits:
            for s in specials:
                print(f"{word}{d}{s}")

        # 2. word + special (e.g., word!)
        for s in specials:
            print(f"{word}{s}")

        # 3. word + year (e.g., word2000)
        for y in years:
            print(f"{word}{y}")

        # 4. word + year + special (e.g., word2000!)
        for y in years:
            for s in specials:
                print(f"{word}{y}{s}")

        # 5. word + 123 + special (e.g., word123!)
        for s in specials:
            print(f"{word}123{s}")
