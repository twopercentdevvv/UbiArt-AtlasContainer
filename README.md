# UbiArt-AtlasContainer
this code messy af but it works so does it really matter?

Convert any `atlascontainer.ckd` file to JSON and back.


## Notes
- This was only tested on Just Dance (2014-2022).
- If you’re working with other UbiArt games and you have issues, you can open an issue in the repo.

## How to use

**Convert `.ckd` to `.json`:**
```bash
python main.py atlascontainer.ckd
```
Creates `atlascontainer.json`.

**You can also pass a file list as a second argument to generate paths instead of hashes (if they're found obviously):**
```bash
python main.py atlascontainer.ckd filelist.txt
```
Use `filelist.py` to generate this, running it in the root of your LUA data or extracted IPK.

**Convert `.json` to `.ckd`:**
```bash
python main.py atlascontainer.json
```
Creates `atlascontainer.ckd`.
