#!/usr/bin/env python3
import os
import re
import yaml

authors = set()
base_dir = "plugins/modules"

for root, _, files in os.walk(base_dir):
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        with open(path) as fh:
            content = fh.read()

        # Extract DOCUMENTATION block
        match = re.search(r'DOCUMENTATION\s*=\s*r?"""(.*?)"""', content, re.S)
        if not match:
            continue
        doc = match.group(1)

        # Try parsing as YAML fragment
        try:
            data = yaml.safe_load(doc)
            auths = data.get("author")
            if isinstance(auths, str):
                authors.add(auths.strip())
            elif isinstance(auths, list):
                for a in auths:
                    if isinstance(a, str):
                        authors.add(a.strip())
        except Exception:
            # Fallback: regex extraction
            for a in re.findall(r'- *"?([^"\n]+)"?', doc):
                authors.add(a.strip())

for name in sorted(authors):
    print(name)

