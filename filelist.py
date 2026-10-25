#!/usr/bin/env python3

import re
from pathlib import Path


def main(d="."):
  rx = re.compile(
      r"(?:^|[/\\])cache[/\\]itf_cooked[/\\][^/\\]+[/\\]", re.IGNORECASE
  )
  files = set()
  root = Path(d).resolve()

  for p in Path(d).rglob("*"):
    if p.is_file():
      name = p.name.lower()
      if any(name.endswith(e) for e in (".png", ".tga", ".png.ckd", ".tga.ckd")):
        s = str(p).replace("\\", "/")

        if s.lower().endswith(".ckd"):
          s = s[:-4]

        m = rx.search(s)
        if m:
          s = s[m.end :]
        else:
          try:
            rel = p.relative_to(root)
            s = str(rel).replace("\\", "/")
            if s.lower().endswith(".ckd"):
              s = s[:-4]
          except ValueError:
            s = p.name

        s = re.sub(r"^\.[/\\]+", "", s)
        files.add(s)

  for f in sorted(files):
    print(f)


if __name__ == "__main__":
  main()
