import os, re

search_patterns = [
    r'meet\s+our\s+team',
    r'our\s+team',
    r'our\s+library\s+team',
    r'team_heading',
    r'team_members',
    r'team-members',
    r'about_experts_heading',
    r'linkedin_url',
    r'/admin/manage/team',
    r'MODELS\[(?:\'|")team(?:\'|")\]',
    r'\bteam\b',
    r'bb24-',
    r'expert'
]

combined_re = re.compile('|'.join(f'(?:{p})' for p in search_patterns), re.IGNORECASE)

ignore_dirs = {'.git', 'backups', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules', '.system_generated'}

results = []

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        if file.endswith(('.py', '.html', '.css', '.js', '.sql', '.json', '.md')):
            fp = os.path.join(root, file)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if combined_re.search(line):
                            results.append((fp, i, line.strip()))
            except Exception as e:
                pass

print(f"Total matching lines found: {len(results)}")
for fp, i, line in results[:100]:
    print(f"{fp}:{i}: {line[:120]}")

with open('backups/team_search_results.txt', 'w', encoding='utf-8') as out:
    for fp, i, line in results:
        out.write(f"{fp}:{i}: {line}\n")
print("Full results written to backups/team_search_results.txt")

