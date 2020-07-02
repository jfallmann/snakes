import os
import json
import copy
from snakemake import load_configfile
from collections import defaultdict

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)

    def __repr__(self):
        return repr(dict(self))

    def merge(self, *args):
        self = merge_dicts(self,*args)

    def rec_equip(self, ics ,key):
        if len(ics)==1:
            self[ics[0]] = template[key]
            self[ics[0]].pop("valid", None)
            return
        self[ics[0]].rec_equip(ics[1:],key)

    def equip(self, config, conditions):
        for k,v in config.items():
            if isinstance(v, dict):
                if "valid" in config[k].keys():
                    self[k]["valid"]=config[k]["valid"]
                for c in conditions:
                    ics=c.split(':')
                    self[k].rec_equip(ics, k)
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


    def rec_walk(self,toset,opts,breaklevel,end=False):
        if breaklevel == 0:
            for k,v in self.items():
                if not v or isinstance(v.keys(), NestedDefaultDict):
                    self[k][toset]=opts
                else:
                    v.rec_walk(toset,opts,0)
            return

        for k,v in self.items():
            if isinstance(v, NestedDefaultDict):
                bl = int(breaklevel)-1
                v.rec_walk(toset,opts,bl)


    def walk(self,template,breaklevel=0):
        for key,value in self.items():
            if isinstance(value, dict):
                # anno = copy.deepcopy(template[value]['ANNOTATION'])
                opts = copy.deepcopy(template[value]['OPTIONS'])
                value.rec_walk(breaklevel,anno,opts)

def proof_input(proof=None):
    allowed_characters=['a','b','c','d','e','f','g','h','i','j','k','l','m','n',
    'o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G',
    'H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    '1','2','3','4','5','6','7','8','9','0','(',')','_','-',',','.',':','/']
    while True:
        a = input(">>> ").strip().replace(" ","")
        # print("\n")
        if any(x not in allowed_characters for x in a):
            print("You used unallowed letters, try again")
            continue
        if proof is not None and proof != "only-numbers" and any(x not in proof for x in a.split(",")):
            print(f"available are only: {proof}")
            continue
        if proof=="only-numbers":
            try:
                float(a)
                return a
            except:
                print("please enter integer or float")
                continue
        else:
            return a

def conversation(question, origin, proof=None):
    print(question)
    default = copy.deepcopy(origin)
    if default is None:
        a = proof_input(proof)
        print("\n")
        return a
    else:
        print("\n")

        if isinstance(default, str):
            print("\t> ",default)
            print("\n")
            if proof:
                print("enter what should be added ")
            else:
                print("enter what should be added or enter 'n' to continue ")
            a = proof_input(proof)
            print("\n")
            if a == 'n':
                print("fine, everything the same!")
                return default
            else:
                return a

        if isinstance(default, dict):
            if default:
                for element in default:
                    print("\t> ",element,": ",default[element])
            else:
                print("\t> no entrys so far")
            print("\n")
            while True:
                print("enter 'y' for yes or 'n' for no")
                a = input(">>> ")
                if a=='n':
                    return default
                if a=='y':
                    print("okay, tell me your setting:")
                    if default:
                        for element in default:
                            print(element+":")
                            a = proof_input()
                            default[element]=a
                        return default
                    else:
                        while True:
                            print("enter the name of the argument or enter 'n' to quit")
                            name = proof_input()
                            if name=='n':
                                break
                            print("enter the value")
                            value = proof_input()
                            print("\n")
                            default.update({name:value})
                    return default

def clear(number):
    os.system(f'echo -e "\e[{number}A\033[2K"')
    for i in range(number-1):
        os.system(f'echo -e "\e[-1A\033[2K"')
    os.system(f'echo -e "\e[{number}A\03\c"')

def depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0

def select_id_to_set(cdict,indent=6):
    out=json.dumps(cdict, indent=indent)
    d = depth(cdict)
    switch = False
    while True:
        for i in range(d-2):
            path=[]
            setting_list=[]
            if switch:
                clear(len(out.split('\n'))+4)
            switch=True
            reminder=''
            counter=0
            for line in out.split('\n'):
                level = int(((len(line) - len(line.lstrip(' ')))-indent)/indent)
                key = line.replace('"','').replace('{','').replace('}','').replace(':','').replace(',','').strip()
                if key:
                    if len(path) > level:
                        path=path[:-(len(path)-level)]
                    path.append(key)
                if level == i and ':' in line:
                    if reminder != key:
                        counter+=1
                        reminder = key
                        setting_list.append([])
                elif level<i and '{}' in line:
                    counter +=1
                    setting_list.append([])
                if '{}' in line:
                    if ',' in line:
                        print(line, f"{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}")
                    else:
                        print(line, f"{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}")
                    setting_list[-1].append(path)
                else:
                    print(line)
            a = conversation("enter for next Level or 'select' for set selected",None)
            if a =='select':
                return setting_list





WORKFLOWS=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING",""]
POSTPROCESSING=["DE","DEU","DAS",""]

template = load_configfile('configs/template_3.json')

config_dict=NestedDefaultDict()
condition_dict=NestedDefaultDict()
condition_dict['moin']['a']
condition_dict['moin']['a']['1']
condition_dict['moin']['a']['2']
condition_dict['moin']['a']['3']
condition_dict['moin']['b']['1']
condition_dict['moin']['b']['2']
condition_dict['moin']['b']['2']['x']
condition_dict['moin']['b']['2']['y']
condition_dict['moin']['b']['3']
condition_dict['moin']['c']['1']
condition_dict['moin']['c']['2']
condition_dict['moin']['c']['3']


def decouple(d):
    string = json.dumps(d)
    return json.loads(string)


conditions=[pattern for pattern in condition_dict.get_condition_list()]
config_dict.equip(template,conditions)
config_dict = decouple(config_dict)
# string = json.dumps(config_dict)
# config_dict = json.loads(string)
# print_dict(config_dict)

# setting_list=select_id_to_set(condition_dict)


'''
╔═╦╗

╠═╬╣
╚═╩╝
'''
def clear(number):
    os.system(f'echo -e "\e[{number}A\033[2K"')
    for i in range(number-1):
        os.system(f'echo -e "\e[-1A\033[2K"')
    os.system(f'echo -e "\e[{number}A\03\c"')

def display(cn,text,option=None,defaults=None,question,proof=None):
    clear(cn)
    print(f'╔{"═"*98}╗');n+=1
    print(f"║{' '*98}║");n+=1
    for line in out.split('\n'):
        print(f"║ {line}{' '*(98-len(line))}║");n+=1

    if option not None:
        print(f"║{' '*98}║");n+=1
        print(f"╠{'═'*98}╣");n+=1
        print(f"║{' '*98}║");n+=1
        print(f"║ {option}{' '*(97-len(option))}║");n+=1
        print(f"║{' '*98}║");n+=1

        if default not None:
            if isinstance(default, str):
                print(f"║ \t>   {default}  {' '*(85-len(default))}║");n+=1
            if isinstance(default, dict):
                for element in default:
                    print(f"║ \t>   {element} :{' '*(85-len(element))}║");n+=1

    print(f"║{' '*98}║");n+=1
    print(f'╚{"═"*98}╝');n+=1
    print('\n');n+=1

    print(f"{question}");n+=1
    a = proof_input(proof);n+=1
    if default not None:
        if a=='n' or a == 'N' or a == '' :
            return default,n+1
        if a=='y':
            clear(2);n-=2
            if isinstance(default,str):
                print("enter setting:");n+=1
                a = proof_input();n+=1
                return a,n+1
            if isinstance(default,dict):
                for element in default:
                    print("\t> ",element,": ");n+=1
                    print('\n');n+=2
                    print("enter setting:");n+=1
                    a = proof_input();n+=1
                    clear(5);n-=5
                    default[element]=a
                return default,n+1
    return a, n+1

def location(dictionary,setting,indent=6):
    clear(c)
    spots=copy.deepcopy(setting)
    d = depth(dictionary)
    # n=0
    out = json.dumps(dictionary, indent=indent)
    for line in out.split('\n'):
        level = int(((len(line) - len(line.lstrip(' ')))-indent)/indent)
        key = line.replace('"','').replace('{','').replace('}','').replace(':','').replace(',','').strip()
        if key:
            for path in spots:
                if not path:
                    continue
                if path[0] == key:
                    path.pop(0)
                    if not path:
                        if ',' in line:
                            line=f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-"
                        else:
                            line=(f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-"
                        break
    return out


def display(c,dictionary,setting,opts,default):
    clear(c)
    spots=copy.deepcopy(setting)
    d = depth(dictionary)
    n=0
    indent=6
    out = json.dumps(dictionary, indent=indent)
    # print('\n');n+=1
    print(f'╔{"═"*98}╗');n+=1
    print(f"║{' '*98}║");n+=1
    for line in out.split('\n'):
        level = int(((len(line) - len(line.lstrip(' ')))-indent)/indent)
        key = line.replace('"','').replace('{','').replace('}','').replace(':','').replace(',','').strip()
        if key:
            for path in spots:
                if not path:
                    continue
                if path[0] == key:
                    path.pop(0)
                    if not path:
                        if ',' in line:
                            print(f"║ {line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*(94-(14-len(key) + indent*(d-2)-indent*level)-len(line))}║");n+=1
                        else:
                            print(f"║ {line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*(93-(14-len(key) + indent*(d-2)-indent*level)-len(line))}║");n+=1
                        break
            else:
                print(f"║ {line}{' '*(97-len(line))}║");n+=1
        else:
            print(f"║ {line}{' '*(97-len(line))}║");n+=1
    print(f"║{' '*98}║");n+=1
    print(f"╠{'═'*98}╣");n+=1
    print(f"║{' '*98}║");n+=1
    print(f"║ {opts}{' '*(97-len(opts))}║");n+=1
    print(f"║{' '*98}║");n+=1

    if default is None:
        print(f"║{' '*98}║");n+=1
        print(f'╚{"═"*98}╝');n+=1
        print('\n');n+=1
        print("wanna change? [ y / N ]");n+=1
        print('\n');n+=1
        a = proof_input(proof);n+=1
        return a, n+1

    else:
        if isinstance(default, str):
            print(f"║ \t>   {default}  {' '*(85-len(default))}║");n+=1
        if isinstance(default, dict):
            for element in default:
                print(f"║ \t>   {element} :{' '*(85-len(element))}║");n+=1
    print(f"║{' '*98}║");n+=1
    print(f'╚{"═"*98}╝');n+=1
    print('\n');n+=1

    print("wanna change? [ y / N ]");n+=1
    a = proof_input();n+=1
    if a=='n' or a == 'N' or a == '' :
        return default,n+1
    if a=='y':
        clear(2);n-=2
        if isinstance(default,str):
            print("enter setting:");n+=1
            a = proof_input();n+=1
            return a,n+1
        if isinstance(default,dict):
            for element in default:
                print("\t> ",element,": ");n+=1
                print('\n');n+=2
                print("enter setting:");n+=1
                a = proof_input();n+=1
                clear(5);n-=5
                default[element]=a
            return default,n+1

options_dict=NestedDefaultDict()
options_dict['COUNTING']['valid']['FEATURES'] = "set feature setting"
options_dict['TRIMMING']['OPTIONS'][0] = ""
options_dict['MAPPING']['OPTIONS'][0] = "set indexing options"
options_dict['MAPPING']['OPTIONS'][1] = "set mapping options"
options_dict['MAPPING']['OPTIONS'][2] = "set name extension for index"
options_dict['DAS']['OPTIONS'][0] = "set counting options"
options_dict['DAS']['OPTIONS'][1] = "set diego options"
options_dict['DEU']['OPTIONS'][0] = "set counting options"
options_dict['DEU']['OPTIONS'][1] = "set x options"
options_dict['DE']['OPTIONS'][0] = "set counting options"
options_dict['DE']['OPTIONS'][1] = "set x options"



WORKFLOWS=['DAS','MAPPING']

toclear=0
for workflow in WORKFLOWS:
    clear(toclear)
    header=f"> Make Settings for {workflow} <"
    print(f"\n{' '*(50-int(len(header)/2))}{header}\n\n")
    toclear=0
    print("select ID's to set")
    setting_list=select_id_to_set(condition_dict)
    # setting_list=[
    # [['a', '1'], ['a', '2'], ['a', '3']],
    # [['b', '1'], ['b', '2', 'x'], ['b', '2', 'y'], ['b', '3']],
    # [['c', '1'], ['c', '2'], ['c', '3']]
    # ]
    if 'valid' in options_dict[workflow].keys():
        for opts in options_dict[workflow]['valid'].keys():
            config_dict[workflow]['valid'][opts] = conversation(options_dict[workflow]['valid'][[opts]], config_dict[workflow]['valid'][opts])
    for setting in setting_list:
        switch=True
        for set in setting:
            cdict=config_dict[workflow]
            for key in set:
                last=key
                cdict=cdict[key]

            if switch:
                # set_relations(cdict,workflow)
                cdict['ANNOTATION'],toclear = display(toclear,condition_dict,setting,
                default=cdict['ANNOTATION'],
                opts="set annotation")
                for i in range(len(cdict['OPTIONS'])):
                    cdict['OPTIONS'][i], toclear = display(toclear,condition_dict,setting,
                    default=cdict['OPTIONS'][i],
                    opts=options_dict[workflow]['OPTIONS'][i])
                options=cdict['OPTIONS']
                annotation=cdict['ANNOTATION']
                switch=False
            else:
                cdict['OPTIONS']=options
                cdict['ANNOTATION']=annotation


print_dict(config_dict)





# def set_annotation (cdict):
#     conversation("set annotation",cdict['ANNOTATION'])


# WORKFLOWS=["DAS"]
# for workflow in WORKFLOWS:
#     if 'valid' in config_dict[workflow].keys():
#         for opts in config_dict[workflow]['valid'].keys():
#             config_dict[workflow]['valid'][opts] = conversation("set valid", config_dict[workflow]['valid'][opts])
#     for setting in setting_list:
#         switch=True
#         for set in setting:
#             cdict=config_dict[workflow]
#             for key in set:
#                 last=key
#                 cdict=cdict[key]
#
#             if switch:
#                 set_relations(cdict,workflow)
#                 cdict['ANNOTATION'] = conversation("set annotation",cdict['ANNOTATION'])
#                 for opts in cdict['OPTIONS']:
#                     cdict['OPTIONS'] = conversation("set options",opts)
#                 options=cdict['OPTIONS']
#                 annotation=cdict['ANNOTATION']
#                 switch=False
#             else:
#                 cdict['OPTIONS']=options
#                 cdict['ANNOTATION']=annotation
#
#
# print_dict(config_dict)


# print_dict(setting_dict)



#
# config_dict['MAXTHREADS'] = "10"
# config_dict['BINS']=["FASTQ","GENOMES","snakes/scripts"]
# print_dict(config_dict)
# print_dict(template)


# for key,value in config_dict.items():
#     if any(key == x for x in WORKFLOWS):
#         for toset in ['OPTIONS', 'ANNOTATION']:
#             if toset in template[key].keys():
#                 breaklevel=conversation("which level?",None)
#                 opts = copy.deepcopy(template[key][toset])
#                 value.rec_walk(toset,opts,breaklevel)

    # if any(key == x for x in POSTPROCESSING):
    #     print()
