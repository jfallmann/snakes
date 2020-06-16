import os
import json
import copy
from snakemake import load_configfile
from collections import defaultdict

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

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

    def rec_walk(self,anno,opts,breaklevel=None):
        if breaklevel == None:
            for k,v in self.items():
                if isinstance(v, dict):
                    v.rec_walk(anno,opts,None)
                else:
                    self[k]=opts
            return
        if breaklevel == 0:
            print_dict(self)
            opts = input(">>> ")
            for k,v in self.items():
                if isinstance(v, dict):
                    v.rec_walk(None,anno,opts)
                else:
                    self[k]=opts
            return
        for k,v in self.items():
            if isinstance(v, dict):
                bl = breaklevel-1
                v.rec_walk(bl,anno,opts)
            if v==[]:
                opts = input(">>> ")
                self[k]=opts
        return

    def walk(self,template,breaklevel=0):
        for key,value in self.items():
            if isinstance(value, dict):
                # anno = copy.deepcopy(template[value]['ANNOTATION'])
                opts = copy.deepcopy(template[value]['OPTIONS'])
                value.rec_walk(breaklevel,anno,opts)

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


WORKFLOWS=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING",""]
POSTPROCESSING=["DE","DEU","DAS",""]
template = load_configfile('configs/template_3.json')

config_dict=NestedDefaultDict()
condition_dict=NestedDefaultDict()
condition_dict['a']
condition_dict['b']
condition_dict['a']['1']
condition_dict['a']['2']
condition_dict['a']['3']
condition_dict['b']['1']
condition_dict['b']['2']
condition_dict['b']['3']


conditions=[pattern for pattern in condition_dict.get_condition_list()]
config_dict.equip(template,conditions)

config_dict['MAXTHREADS'] = "10"
config_dict['BINS']=["FASTQ","GENOMES","snakes/scripts"]
print_dict(config_dict)

for workflow in WORKFLOWS:
    breaklevel=conversation("which level?",None)
    config_dict[workflow].rec_walk(breaklevel,opts)

for key,value in config_dict.items():
    if any(key == x for x in WORKFLOWS):
        if isinstance(value, dict):
            # anno = copy.deepcopy(template[value]['ANNOTATION'])
            opts = copy.deepcopy(template[value]['OPTIONS'])
            value.rec_walk(breaklevel,anno,opts)

    if any(key == x for x in POSTPROCESSING):
        print()
