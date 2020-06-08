
from nested_dict2 import NestedDefaultDict
import pprint
import json

def print_dict_pointer(dict,path,indent=6):
    out=json.dumps(dict, indent=indent)
    print(path)
    for line in out.split('\n'):
        if path[0] in line:
            if len(path)==1:
                print(line,"\t<== enter ID's here")
            else:
                path=path[1:]
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
    for k,v in subtree.items():
        path.append(k)
        print_dict_pointer(tree, path)
        leafes=input(">>> ").split(',')
        rec_ics_display(subtree[k],leafes,path,tree)
    if len(path)>0:
        path.pop()
    return

tree = NestedDefaultDict()
rec_ics_display(tree,["EXPERIMENT"])
# print(pattern for pattern in tree['EXPERIMENT'].get_condition_list())

condition_list= [path for path in tree.get_condition_list()]
print(condition_list)

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
