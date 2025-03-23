import json
import random
import sys


def main():
    # Read all stdin
    data = sys.stdin.read()

    # Parse the JSON
    parsed = json.loads(data)

    # Modify some things
    parsed["processed"] = True
    parsed["data"] = {}
    parsed["data"]["random"] = random.randint(0, 100)

    # Dump the JSON
    print(json.dumps(parsed))


if __name__ == "__main__":
    main()
