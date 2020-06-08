from collections import defaultdict
from collections import OrderedDict
import collections
import json
import sys
import copy
import pprint
from snakemake import load_configfile
import glob, os, sys, inspect, json, shutil
from collections import defaultdict, deque
import traceback as tb
from snakemake import load_configfile
from snakemake.utils import validate, min_version
import argparse
import subprocess
import re
import sys
import copy
import json
import random
import logging

def print_dict(dict, indent=4):
    print(json.dumps(dict, indent=indent))


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


    # def rec_walk(self, breaklevel=None,anno,opts):
    #     if breaklevel == None:
    #         for k,v in self.items():
    #             if isinstance(v, dict):
    #                 v.rec_walk(None,anno,opts)
    #             else:
    #                 self[k]=opts
    #         return
    #     if breaklevel == 0:
    #         print_dict(self)
    #         opts = input(">>> ")
    #         for k,v in self.items():
    #             if isinstance(v, dict):
    #                 v.rec_walk(None,anno,opts)
    #             else:
    #                 self[k]=opts
    #         return
    #     for k,v in self.items():
    #         if isinstance(v, dict):
    #             bl = breaklevel-1
    #             v.rec_walk(bl,anno,opts)
    #         if v==[]:
    #             opts = input(">>> ")
    #             self[k]=opts
    #     return
    #
    # def walk(self, breaklevel=0,template):
    #     for key,value in self.items():
    #         if isinstance(value, dict):
    #             # anno = copy.deepcopy(template[value]['ANNOTATION'])
    #             opts = copy.deepcopy(template[value]['OPTIONS'])
    #             value.rec_walk(breaklevel,anno,opts)




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

def equip_condition_dict(subtree,leafes,path=[],tree=None):
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


pp = pprint.PrettyPrinter(indent=4)


template = load_configfile('configs/template_3.json')
condition_dict = NestedDefaultDict()
config_dict = NestedDefaultDict()
WORKFLOWS=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING",""]
POSTPROCESSING=["DE","DEU","DAS",""]

explain("intro.txt")
start = conversation("Enter 'append' for expanding an existing configfile or 'new' for a new project",None)

while True:
    if 'append' in start:
        continue
    if 'new' in start:

        name = conversation("Now please type the name of your Project, it will be the name of the CONFIGFILE \nand possibly of your Project-folder", None)
        configfile = f"config_{name}.json"

        folder_content = os.listdir('../')
        if 'FASTQ' in folder_content or 'GENOMES' in folder_content:
            set_folder=conversation("It looks like you already set up your project-folder. We would therefor skip setting it up now. Enter 'n' if you want to do that anyway.", None)
        else:
            explain('projectfolder.txt')
            while True:
                path_to_project = conversation("So, where should the Project-folder be created? Enter the absolute path \nlike '/home/path/to/NextSnakesProjects' ",None)
                if os.path.isdir(path_to_project):
                    project = os.path.join(path_to_project,name)
                    if os.path.isdir(project):
                        print(f"In the directory you entered, a folder with the name {name} already exist. \nMaybe you should think about what you really want to do. If you want to work on \nan existing Project, use the 'append' function, otherwise use a different \nProject-name. Ciao!")
                        exit()
                    os.mkdir(project)
                    os.mkdir(os.path.join(project,"FASTQ"))
                    os.mkdir(os.path.join(project,"GENOMES"))
                    os.symlink(cwd, os.path.join(project,'snakes'))
                    break
                else:
                    print("Sry, couldn't find this directory ")

        explain("conditions.txt")
        equip_condition_dict(condition_dict,[name])
        conditions=[pattern for pattern in condition_dict.get_condition_list()]

        print("Now you may have to be patient. We go through all settings, and you have to \n"
        "assign the corresponding samples by their absolute directory path. The Guide will \n"
        "symlink it to your 'FASTQ'-Folder.\n\n"
        "For that, maybe it's helpful to open another termimal, navigate to the directory \n"
        "your samples are stored and list them with 'readlink -f *.fastq.gz'\n")

        for condition in conditions:
            while True:
                sample=conversation(f"Enter one Sample-path of {condition} or enter 'n' to go to the next condition",None)
                if sample=='n':
                    break
                if os.path.isfile(sample):
                    try:
                        os.symlink(sample, os.path.join(project,'FASTQ',condition.split(':')[0],condition.split(':')[1],condition.split(':')[2],os.path.basename(sample)))
                    except:
                        print("hmm, an error occured.. maybe this file is already linked. try again!")
                else:
                    print("Sry, couldn't find the file")

        explain("workflows.txt")
        workflows = conversation("Enter which WORKFLOWS you would like to run.", None, WORKFLOWS)
        postprocess = conversation("Which POSTPROCESS ANALYSIS would you like to run? Possible are DE, DEU, DAS", None, POSTPROCESSING)

        config_dict.equip(template,conditions)

        explain("genomes1.txt")
        organisms = conversation("enter all organisms you have in your analysis",None)
        for organism in organisms.split(","):
            os.mkdir(os.path.join(project,"GENOMES",organism))
            basename=conversation(f"enter the basename(!) of the fa.gz file appending to {organism}", None)})
            config_dict['GENOME'].update({organism:basename})
            print("Now you can add Genome reference files to your GENOMES folder\n")
            while True:
                file=conversation(f"Enter one file-path you want to symlink to {organism} or enter 'n' to go to the next ics",None)
                if file=='n':
                    break
                if os.path.isfile(file):
                    try:
                        os.symlink(file, os.path.join(project,'GENOMES',organism,os.path.basename(file)))
                    except:
                        print("hmm, an error occured.. maybe this file is already linked. try again!")
                else:
                    print("Sry, couldn't find the file")


        config_dict['MAXTHREADS'] =
        config_dict['BINS']=["FASTQ","GENOMES","snakes/scripts"]

        explain("workflows2.txt")

        for workflow in WORKFLWOS:
            breaklevel=conversation("which level?",None)
            config_dict[workflow].rec_walk(breaklevel,opts)

        for key,value in config_dict.items():
            if any(key == x for x in WORKFLOWS):
                if isinstance(value, dict):
                    # anno = copy.deepcopy(template[value]['ANNOTATION'])
                    opts = copy.deepcopy(template[value]['OPTIONS'])
                    value.rec_walk(breaklevel,anno,opts)

            if any(key == x for x in POSTPROCESSING):

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
