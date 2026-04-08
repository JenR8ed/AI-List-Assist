import re

with open('services/listing_synthesis.py', 'r') as f:
    content = f.read()

# Fix the invalid escape sequence
content = content.replace(
    "re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)",
    "re.search(r'```(?:json)?\\s*(\\{.*?\\})\\s*```', response_text, re.DOTALL)"
)

with open('services/listing_synthesis.py', 'w') as f:
    f.write(content)
