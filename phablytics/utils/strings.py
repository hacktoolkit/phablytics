def pluralize(s):
    last_char = s[-1]

    if last_char == 'y':
        pluralized = s[:-1] + 'ies'
    elif last_char == 's':
        pluralized = s
    else:
        pluralized = s + 's'
    return pluralized
