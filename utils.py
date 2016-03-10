import json


def output_event(event):
    s = json.dumps(event, separators=',:')
    assert '\n' not in s
    print(s)
