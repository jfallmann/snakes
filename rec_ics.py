
# from nested_dict2 import NestedDefaultDict
from collections import defaultdict
import pprint
import json
import copy
import sys
import os


class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)

    def __repr__(self):
        return repr(dict(self))

    def merge(self, *args):
        self = merge_dicts(self,*args)

    def rec_equip(self, ics):
        if len(ics)==1:
            self[ics[0]] = []
            return
        self[ics[0]].rec_equip(ics[1:])

    def equip(self, config, conditions):
        for k,v in config.items():
            if isinstance(v, dict):
                for c in conditions:
                    ics=c.split(':')
                    self[k].rec_equip(ics)
            else:
                self[k]=""

    def get_condition_list(self, keylist=[]):
        for k,v in self.items():
            keylist.append(k,)
            if not v:
                yield ':'.join(keylist)
            else:
                yield from v.get_condition_list(keylist)
            keylist.pop()

def clear(number):
    os.system(f'echo -e "\e[{number}A\033[2K"')
    for i in range(number-1):
        os.system(f'echo -e "\e[-1A\033[2K"')
    os.system(f'echo -e "\e[{number}A\03\c"')

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

def print_dict_pointer(dict,path,copy,more,indent=6):
    out=json.dumps(dict, indent=indent)
    clear(len(out.split('\n'))-more)
    # print('path: ',path)
    route=['step']+path.copy()
    stepper=1
    for line in out.split('\n'):
        level = int(((len(line) - len(line.lstrip(' ')))-indent)/indent)
        key = line.replace('"','').replace('{','').replace('}','').replace(':','').replace(',','').strip()
        if level+1 >= len(route):
            print(line)
        elif not key:
            print(line)
        elif route[level+1] == key and route[level] == 'step':
            route[stepper] = 'step'
            stepper+=1
            if len(route) == level+2:
                if route[level-1] == 'step':
                    if copy and copy != ['']:
                        print(line, f"\t>> enter new ID's here <<   or copy {copy} with 'cp' ")
                    else:
                        print(line, f"\t>> enter new ID's here <<")
            else:
                print(line)
        else:
            print(line)

def rec_ics_display(subtree,leafes,path=[],tree=None):
    if tree==None:
        tree=subtree
    if not leafes[0]:
        path.pop()
        return
    for leaf in leafes:
        subtree[leaf]
    copy=[]
    for k,v in subtree.items():
        path.append(k)
        if tree==subtree:
            print("\n")
        if not leafes[0]:
            print_dict_pointer(tree, path, copy,-1)
        else:
            print_dict_pointer(tree, path, copy,len(leafes))
        leafes=input(">>> ").split(',')
        if leafes==["cp"]:
            leafes=copy
        rec_ics_display(subtree[k],leafes,path,tree)
        copy=leafes
        leafes=['']
    if len(path)>0:
        path.pop()
    return



tree = NestedDefaultDict()
rec_ics_display(tree,["EXPERIMENT"])

condition_list= [path for path in tree.get_condition_list()]
for condition in condition_list:
    print(condition)

# def pick(d,l):
#     if len(l)==1:
#         return d[l[0]]
#     return pick(d[l[0]],l[1:])



# def append(tree, c):
#     if not c:
#         return
#     append(tree[c[0]],c[1:])
#
# conditions=[]
# while True:
#     print("enter ID's")
#     i = input(">>> ")
#     if i == 'n':
#         break
#     conditions.append(i)
#     append(tree, i.split(':'))
#     print_dict(tree,"a")

# for condition in conditions:
#     c = condition.split(':')
#     append(tree, c)
