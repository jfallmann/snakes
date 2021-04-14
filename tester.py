from snakemake import load_configfile
import json

from functools import reduce  # forward compatibility for Python 3
import operator

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))


def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)

def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    if isinstance(get_by_path(root, items[:-1])[items[-1]], list):
        gp = get_by_path(root, items[:-1])[items[-1]]
        gp.append(value)
    else:
        get_by_path(root, items[:-1])[items[-1]] = value

def del_by_path(root, items):
    """Delete a key-value in a nested object in root by item sequence."""
    if isinstance(get_by_path(root, items[:-1])[items[-1]], str):
        get_by_path(root, items[:-1])[items[-1]] = ""
    del get_by_path(root, items[:-1])[items[-1]]


template_file = ("./configs/template_base_commented.json")
template= load_configfile(template_file)


toprint = get_by_path(template, ["DTU"])
print_dict(toprint)

# set_by_path(template, ["DTU", "dexseq", "OPTIONS"], {"MOININGER":"TACHAUCH"})
# toprint = get_by_path(template, ["DTU", "dexseq", "OPTIONS"])

del_by_path(template, ["DTU", "dexseq", "OPTIONS"])

toprint = get_by_path(template, ["DTU"])
print_dict(toprint)


path = "./docs/source/intro.rst"
with open(path, 'r') as f:
    for l in f.readlines():
        print(l.replace('\n', ''))
