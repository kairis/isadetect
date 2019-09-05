Requirements:
- jigdo-lite
- fuseiso
- dpkg-deb

1. python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

2. By default files are downloaded under dataset_gen/output. To download the files elsewhere, point the environment value DATASET_GEN_ROOT_FOLDER to the desired folder.

3. Copy config.ini.example as config.ini and modify the architectures you want to download by changing "architectures" and "port_architecture".

4. To download the architectures defined in "architectures", run "python3 generator.py --all_deb". To download arhitectures defined in "port_architectures", run python3 "generator.py --all_ports".

If problems with jigdo, maybe try editing the file .jigdo_lite in your home folder with this content.
You can also change the mirrors (debianMirror, nonusMirror) by selecting ones from here: https://www.debian.org/mirror/list

jigdo=''
debianMirror='http://ftp.fi.debian.org/debian/'
nonusMirror='http://www.nic.funet.fi/debian/'
tmpDir='.'
jigdoOpts='--cache jigdo-file-cache.db'
wgetOpts='--passive-ftp --dot-style=mega --continue --timeout=30'
scanMenu=''
