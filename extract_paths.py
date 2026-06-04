import os, re
urls = set()
paths = set()

for r, d, fs in os.walk('src'):
    for f in fs:
        if f.endswith('.py'):
            with open(os.path.join(r, f), 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                urls.update(re.findall(r'https?://[^\s\"\'\>]+', content))
                paths.update(re.findall(r'[A-Za-z]:\\[\w\\]+', content))

print("=== URLS ENCONTRADAS ===")
for u in sorted(urls):
    print(u)
    
print("\n=== CAMINHOS DO WINDOWS ENCONTRADOS ===")
for p in sorted(paths):
    print(p)
