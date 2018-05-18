wiretap
=======

Python module for managing Flame/Flare/FlameAssist Wiretap database.

## Setup

```
sudo pip install git+https://github.com/predat/wiretap
```

If you want to install the module locally:
```
pip install git+https://github.com/predat/wiretap --user
```


## Usage

By default, wiretap python module use version 2018.3. If you want to use an other version,
you can set an environmnet variable `WIRETAP_VERSION`. Ex:
```
export WIRETAP_VERSION=2019
wiretap -h
```
or
```
WIRETAP_VERSION=2019 wiretap -h
```

### From the command line:

pip install a script call `wiretap`:

```
wiretap -h

usage: wiretap [-h] [--server SERVER] <command> ...

Wiretap command line tool.

optional arguments:
  -h, --help            show this help message and exit
  --server SERVER, -s SERVER
                        Wiretap server to connect (default: localhost)

commands:
  Command to execute

  <command>
    create-project      Create a Wiretap project.
    create-user         Create a Wiretap user.
    delete-user         Delete a Wiretap user.
```

Example: create a local project with a resolution of 2048x1024 at 25 fps in 10-bit:
```
wiretap create-project MY_AWESONE_PROJECT_ON_FLAME --depth '10-bit' --fps 25 --width 2048 --height 1024
```
