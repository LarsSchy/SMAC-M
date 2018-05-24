#!/usr/bin/python2


def ask_user(question, choices):
    while True:
        for item in enumerate(choices):
            print("    [%d] %s" % item)
        answer = input(question)
        if answer.isdigit() and 0 <= int(answer) < len(choices):
            return int(answer)
