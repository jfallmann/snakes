from collections import OrderedDict
from collections import defaultdict, deque
import collections
import pprint
import glob, os, sys, inspect, json, shutil
import traceback as tb
from snakemake import load_configfile
from snakemake.utils import validate, min_version
import argparse
import subprocess
import re
import copy
import random
import logging
from itertools import cycle
from testing import display


def decouple(d):
    string = json.dumps(d)
    return json.loads(string)

def depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0


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

def explain(filename):
    path = os.path.join("docs/guide",filename)
    print("\n")
    with open(path, 'r') as f:
        text = f.read().splitlines()
        counter=1
        for line in text:
            print(line)
            if counter == 30:
                input(f"{' '*50}> press enter to continue <")
                counter=0
            counter+=1
    print("\n")

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
                print("wanna change?  [ y / N ] ")
            a = proof_input(proof)
            print("\n")
            if a=='n' or a == '' or a == 'N':
                return default
            if a=='y':
                print("okay, tell me your setting:")
                a = proof_input()
                print('\n')
                return a

        if isinstance(default, dict):
            if default:
                for element in default:
                    print("\t> ",element,": ",default[element])
            else:
                print("\t> no entrys so far")
            print("\n")
            while True:
                print("wanna change?  [ y / N ] ")
                a = input(">>> ")
                print("\n")
                if a=='n' or a == '' or a == 'N':
                    return default
                if a=='y':
                    if default:
                        for element in default:
                            print("\t> ",element,": ")
                            print('\n')
                            print("okay, tell me your setting:")
                            a = proof_input()
                            print('\n')
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

def create_condition_dict(subtree,leafes,path=[],tree=None):
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
        create_condition_dict(subtree[k],leafes,path,tree)
        copy=leafes
        leafes=['']
    if len(path)>0:
        path.pop()
    return

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


steps=[
"add samples",
"create Project-folder",
"select Workflows",
"set workflow options",
""
]


if __name__ == '__main__':

    # makelogdir('LOGS')
    # logid = scriptname+'.main: '
    # log = setup_logger(name=scriptname, log_file='LOGS/'+scriptname+'.log', logformat='%(asctime)s %(levelname)-8s %(name)-12s %(message)s', datefmt='%m-%d %H:%M', level=knownargs.loglevel)
    # log.addHandler(logging.StreamHandler(sys.stderr))  # streamlog

    MIN_PYTHON = (3,7)
    if sys.version_info < MIN_PYTHON:
        log.error("This script requires Python version >= 3.7")
        sys.exit("This script requires Python version >= 3.7")
    # log.info(logid+'Running '+scriptname+' on '+str(knownargs.procs)+' cores')

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cwd=os.getcwd()

    print("\n\n\n","*"*33," NextSnakes GUIDE ","*"* 33,)
    print("","*"*86,"\n")

    # try:
        # args=parseargs()
        # if args.quickmode:
        #     quick=True
        #     print("  > starting in quick-mode <\n")
        # else:
        #     quick=False
        #     print("  > starting in explanation-mode <\n")

        # pp = pprint.PrettyPrinter(indent=4)

    template = load_configfile('configs/template_3.json')
    config_dict = NestedDefaultDict()
    condition_dict = NestedDefaultDict()

    # create_condition_dict(condition_dict,[name])
    # condition_dict=condition_dict.pop(name)

    condition_dict['a']
    condition_dict['b']
    condition_dict['a']['1']['x']
    condition_dict['a']['1']['y']
    condition_dict['a']['1']['y']['m']
    condition_dict['a']['1']['y']['numbers']
    condition_dict['a']['1']
    condition_dict['a']['2']
    condition_dict['a']['3']
    condition_dict['b']['1']
    condition_dict['b']['2']
    condition_dict['b']['2']['x']
    condition_dict['b']['2']['y']
    condition_dict['b']['3']
    condition_dict['c']['1']
    condition_dict['c']['2']
    condition_dict['c']['3']

    # WORKFLOWS=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING",""]
    name = 'testdict'
    WORKFLOWS=["MAPPING", "DAS"]
    conditions=[pattern for pattern in condition_dict.get_condition_list()]
    config_dict.equip(template,conditions)
    config_dict = decouple(config_dict)
    config_dict['MAXTHREADS'] = "10"
    config_dict['BINS']=["FASTQ","GENOMES","snakes/scripts"]

        # POSTPROCESSING=["DE","DEU","DAS",""]

        # explain("intro.txt")
        # start = conversation("Enter 'append' for expanding an existing configfile or 'new' for a new project",None)

        # while True:
        #     if 'append' in start:
        #         continue
        #     if 'new' in start:

                # name = conversation("Now please type the name of your Project, it will be the name of the CONFIGFILE \nand possibly of your Project-folder", None)
                # configfile = f"config_{name}.json"

                # folder_content = os.listdir('../')
                # if 'FASTQ' in folder_content or 'GENOMES' in folder_content:
                #     set_folder=conversation("It looks like you already set up your project-folder. We would therefor skip setting it up now. Enter 'n' if you want to do that anyway.", None)
                # else:
                #     explain('projectfolder.txt')
                #     while True:
                #         path_to_project = conversation("So, where should the Project-folder be created? Enter the absolute path \nlike '/home/path/to/NextSnakesProjects' ",None)
                #         if os.path.isdir(path_to_project):
                #             project = os.path.join(path_to_project,name)
                #             if os.path.isdir(project):
                #                 print(f"In the directory you entered, a folder with the name {name} already exist. \nMaybe you should think about what you really want to do. If you want to work on \nan existing Project, use the 'append' function, otherwise use a different \nProject-name. Ciao!")
                #                 exit()
                #             os.mkdir(project)
                #             os.mkdir(os.path.join(project,"FASTQ"))
                #             os.mkdir(os.path.join(project,"GENOMES"))
                #             os.symlink(cwd, os.path.join(project,'snakes'))
                #             break
                #         else:
                #             print("Sry, couldn't find this directory ")

                # explain("conditions.txt")
                # create_condition_dict(condition_dict,[name])
                # condition_dict=condition_dict.pop(name)
                # conditions=[pattern for pattern in condition_dict.get_condition_list()]

                # print("Now you may have to be patient. We go through all settings, and you have to \n"
                # "assign the corresponding samples by their absolute directory path. The Guide will \n"
                # "symlink it to your 'FASTQ'-Folder.\n\n"
                # "For that, maybe it's helpful to open another termimal, navigate to the directory \n"
                # "your samples are stored and list them with 'readlink -f *.fastq.gz'\n")
                #
                # for condition in conditions:
                #     while True:
                #         sample=conversation(f"Enter one Sample-path of {condition} or enter 'n' to go to the next condition",None)
                #         if sample=='n':
                #             break
                #         if os.path.isfile(sample):
                #             try:
                #                 os.symlink(sample, os.path.join(project,'FASTQ',condition.split(':')[0],condition.split(':')[1],condition.split(':')[2],os.path.basename(sample)))
                #             except:
                #                 print("hmm, an error occured.. maybe this file is already linked. try again!")
                #         else:
                #             print("Sry, couldn't find the file")

                # explain("workflows.txt")
                # workflows = conversation("Enter which WORKFLOWS you would like to run.", None, WORKFLOWS)
                # postprocess = conversation("Which POSTPROCESS ANALYSIS would you like to run? Possible are DE, DEU, DAS", None, POSTPROCESSING)

    # config_dict.equip(template,conditions)
    # config_dict = decouple(config_dict)

                # explain("genomes1.txt")
                # organisms = conversation("enter all organisms you have in your analysis",None)
                # for organism in organisms.split(","):
                #     os.mkdir(os.path.join(project,"GENOMES",organism))
                #     basename=conversation(f"enter the basename(!) of the fa.gz file appending to {organism}", None)
                #     config_dict['GENOME'].update({organism:basename})
                #     print("Now you can add Genome reference files to your GENOMES folder\n")
                #     while True:
                #         file=conversation(f"Enter one file-path you want to symlink to {organism} or enter 'n' to go to the next ics",None)
                #         if file=='n':
                #             break
                #         if os.path.isfile(file):
                #             try:
                #                 os.symlink(file, os.path.join(project,'GENOMES',organism,os.path.basename(file)))
                #             except:
                #                 print("hmm, an error occured.. maybe this file is already linked. try again!")
                #         else:
                #             print("Sry, couldn't find the file")



    print_dict(config_dict)
            # explain("workflows2.txt")


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

    for workflow in WORKFLOWS:
        print(f"Make Settings for {workflow}\n")
        # print("select ID's to set")
        # setting_list=select_id_to_set(condition_dict)
        setting_list=[
        [['a', '1', 'x'], ['a', '1', 'y', 'm'], ['a', '1', 'y', 'numbers'], ['a', '2'], ['a', '3']],
        [['b', '1'], ['b', '2', 'x'], ['b', '2', 'y'], ['b', '3']],
        [['c', '1'], ['c', '2'], ['c', '3']]
        ]
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
                    cdict['ANNOTATION'] = conversation("set annotation",cdict['ANNOTATION'])
                    for i in range(len(cdict['OPTIONS'])):
                        cdict['OPTIONS'][i] = conversation(options_dict[workflow]['OPTIONS'][i],cdict['OPTIONS'][i])
                    options=cdict['OPTIONS']
                    annotation=cdict['ANNOTATION']
                    switch=False
                else:
                    cdict['OPTIONS']=options
                    cdict['ANNOTATION']=annotation


    print_dict(config_dict)


    # except Exception as err:
    #     exc_type, exc_value, exc_tb = sys.exc_info()
    #     tbe = tb.TracebackException(
    #     exc_type, exc_value, exc_tb,
    #     )
    #     log.error(logid+''.join(tbe.format()))

#
#
# conditions = [
# 'm:a:1',
# 'm:a:2',
# 'm:b:1',
# 'm:b:2',
# 'm:x',
# 'w:a:1',
# 'w:a:2',
# 'w:b:1',
# 'w:b:2',
# ]
#
#
# nested.equip(config,conditions)
#
# for key,value in nested.items():
#     if isinstance(value, dict):
#         # anno = copy.deepcopy(template[value]['ANNOTATION'])
#         opts = copy.deepcopy(template[value]['OPTIONS'])
#         value.rec_walk(breaklevel,anno,opts)
#
# # nested.walk(0)
#
# print_dict(nested)
#
#
#









# class NestedDict(OrderedDict):
#     def __missing__(self, key):
#         val = self[key] = NestedDict()
#         return val

# def deepupdate(target, src):
#     for k, v in src.items():
#         if type(v) == list:
#             if not k in target:
#                 target[k] = copy.deepcopy(v)
#             else:
#                 target[k].extend(v)
#         elif type(v) == set:
#             if not k in target:
#                 target[k] = v.copy()
#             else:
#                 target[k].update(v.copy())
#         elif type(v) == dict:
#             if not k in target:
#                 target[k] = copy.deepcopy(v)
#             else:
#                 deepupdate(target[k], v)
#         else:
#             target[k] = copy.copy(v)
