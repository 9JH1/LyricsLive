import re

def replace_caps_with_letter(string):
    return re.sub(r'[A-Z]', 'letter\n', string)

# Example usage
original_string = "ThisIsATestString"
result = replace_caps_with_letter(original_string)
print(result)
