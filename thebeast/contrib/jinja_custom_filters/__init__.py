import re

def regex_search(string, pattern):
    # Search for a pattern in the given string.
    
    match = re.search(pattern, string)
    return match.group(0) if match else None

def regex_match(string, pattern):
    #Check if the entire string matches the pattern.
    return bool(re.fullmatch(pattern, string))

def regex_replace(string, pattern, replacement):
    #Replace occurrences of the pattern with the replacement in the string.

    return re.sub(pattern, replacement, string)
