import re

with open('roadmap_v2.md', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('- [ ] **Turn-Based Multiplayer Combat**', '- [x] **Turn-Based Multiplayer Combat**')

with open('roadmap_v2.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated roadmap_v2.md")
