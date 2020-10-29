import os
import json
import copy
from snakemake import load_configfile
from collections import defaultdict


class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)

    def __repr__(self):
        return repr(dict(self))

    def merge(self, *args):
        self = merge_dicts(self,*args)

    def rec_equip(self, ics ,key):
        if len(ics)==1:
            if not template[key]:
                self[ics[0]] =""
            else:
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

    def get_all_keys(self):
        for key, value in self.items():
            if isinstance(value, dict):
                yield key
                yield from value.get_all_keys()
            else:
                yield key

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
            clear(2)
            print("You used unallowed letters, try again")
            continue
        if proof is not None and proof != "only-numbers" and any(x not in proof for x in a.split(",")):
            clear(2)
            print(f"available are: {proof}")
            continue
        if proof=="only-numbers":
            try:
                float(a)
                return a
            except:
                clear(2)
                print("please enter integer or float")
                continue
        else:
            return a
def clear(number):
    os.system(f'echo -e "\e[{number}A\033[2K"')
    for i in range(number-1):
        os.system(f'echo -e "\e[-1A\033[2K"')
    os.system(f'echo -e "\e[{number}A\03\c"')
def depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0
def decouple(d):
    string = json.dumps(d)
    return json.loads(string)
def select_id_to_set(cdict,i,indent=6):
    text=json.dumps(cdict, indent=indent)
    d = depth(cdict)
    out=""
    path=[]
    setting_list=[]
    reminder=''
    counter=0
    for line in text.split('\n'):
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
                out+= f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}\n"
            else:
                out+= f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}\n"
            setting_list[-1].append(path)
        else:
            out+=line+'\n'
    return out,setting_list
def clear(number):
    os.system(f'echo -e "\e[{number}A\033[2K"')
    for i in range(number-1):
        os.system(f'echo -e "\e[-1A\033[2K"')
    os.system(f'echo -e "\e[{number}A\03\c"')
def title(text):
    global toclear
    clear(toclear)
    print(f"\n{' '*(50-int((len(text)+4)/2))}> {text} <\n\n")
    toclear = 1
    return
def get_doc(filename):
    path = os.path.join("docs/guide",f"{filename}.txt")
    out=""
    with open(path, 'r') as f:
        out = f.read()
    return out
def display(text,option=None,defaults=None,question=None,proof=None):
    global toclear
    clear(toclear)
    toclear=1
    print(f'╔{"═"*98}╗');toclear+=1
    print(f"║{' '*98}║");toclear+=1
    for line in text.split('\n'):
        print(f"║ {line}{' '*(97-len(line))}║");toclear+=1
    if option :
        print(f"║{' '*98}║");toclear+=1
        print(f"╠{'═'*98}╣");toclear+=1
        print(f"║{' '*98}║");toclear+=1
        for line in option.split('\n'):
            print(f"║ {line}{' '*(97-len(line))}║");toclear+=1
        print(f"║{' '*98}║");toclear+=1
    if defaults:
        if isinstance(defaults, str):
            print(f"║ \t>   {defaults}  {' '*(85-len(defaults))}║");toclear+=1
        if isinstance(defaults, dict):
            for element in defaults:
                print(f"║ \t>   {element} :{' '*(85-len(element))}║");toclear+=1
        print(f"║{' '*98}║");toclear+=1
    print(f'╚{"═"*98}╝');toclear+=1
    print('\n');toclear+=1
    if question:
        for line in question.split('\n'):
            print(f"{line}");toclear+=1
    a = proof_input(proof);toclear+=1
    if "y / N" in question:
        if a=='n' or a == 'N' or a == '' :
            return defaults
        if a=='y':
            clear(2);toclear-=2
            if isinstance(defaults,str):
                print("enter setting:");toclear+=1
                a = proof_input();toclear+=1
                return a
            if isinstance(defaults,dict):
                for element in defaults:
                    print("\t> ",element,": ");toclear+=1
                    print('\n');toclear+=2
                    print("enter setting:");toclear+=1
                    a = proof_input();toclear+=1
                    clear(5);toclear-=5
                    defaults[element]=a
                return defaults
    return a
def location(dictionary,setting,indent=6):
    spots=copy.deepcopy(setting)
    d = depth(dictionary)
    out=""
    text = json.dumps(dictionary, indent=indent)
    for line in text.split('\n'):
        switch=True
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
                            out+=f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-\n"
                        else:
                            out+=f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-\n"
                        switch=False
        if switch:
            out+=line+'\n'
    return out
def print_dict_pointer(dict,path,copy,indent=6):
    text=json.dumps(dict, indent=indent)
    route=['step']+path.copy()
    out=""
    stepper=1
    for line in text.split('\n'):
        level = int(((len(line) - len(line.lstrip(' ')))-indent)/indent)
        key = line.replace('"','').replace('{','').replace('}','').replace(':','').replace(',','').strip()
        if level+1 >= len(route):
            out+=line+'\n'
        elif not key:
            out+=line+'\n'
        elif route[level+1] == key and route[level] == 'step':
            route[stepper] = 'step'
            stepper+=1
            if len(route) == level+2:
                if route[level-1] == 'step':
                    if copy and copy != ['']:
                        out+=f"{line}    <-\n"
                        option=f"enter new ID's \n\nor copy {copy} with 'cp'"
                    else:
                        out+=f"{line}    <-\n"
                        option="enter new ID's"
            else:
                out+=line+'\n'
        else:
            out+=line+'\n'
    return out, option
def create_condition_dict(subtree,leafes,path=[],tree=None):
    global toclear
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
        # if tree==subtree:
        #     print("\n")
        text, opt = print_dict_pointer(tree, path, copy)
        answer,toclear=display(
        cn=toclear,
        text=text,
        option=opt
        )
        if answer:
            leafes=[x for x in answer.split(',')]
        else:
            leafes=['']
        if leafes==["cp"]:
            leafes=copy
        create_condition_dict(subtree[k],leafes,path,tree)
        copy=leafes
        leafes=['']
    if len(path)>0:
        path.pop()
    return

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
options_dict['SEQUENCING'] = "paired or unpaired?"
options_dict['GENOME'] = "which organism?"

'''
╔═╦╗
╠═╬╣
╚═╩╝

answer, toclear = display(
cn=toclear,
text="",
option="",
defaults={},
question="",
proof=[]
)
'''

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cwd=os.getcwd()

print("\n\n\n")
print("*"*40," NextSnakes GUIDE ","*"* 40,)
print("*"*100,"\n")
print("\n")
global toclear
toclear=0


# toclear = title(toclear, "INTRO")
# explanation=get_doc("intro")
# answer, toclear = display(
# cn=0,
# text=explanation,
# option=None,
# defaults=None,
# question="Enter 'append' for expanding an existing configfile or 'new' for a new project",
# proof=['new','append']
# )
#
# toclear = title(toclear,"CREATE PROJECT-FOLDER")
# explanation=get_doc("projectfolder")
# answer, toclear = display(
# cn=toclear,
# text=explanation,
# option="",
# defaults=None,
# question="Enter the name of your Project",
# proof=None
# )
# name=answer
# configfile = f"config_{name}.json"

# if any(x in os.listdir('../') for x in ['FASTQ','GENOMES']):
#     set_folder=display(
#     cn=toclear,
#     text="It looks like you already set up your project-folder. \mWe would therefor skip setting it up now. \n\nEnter 'n' if you want to do that anyway.",
#     question="wanna skip the Guide? [ n / Y ]")
# else:
# switch=False
# while True:
#     if switch:
#         ques="Enter the absolute path \nlike '/home/path/to/NextSnakesProjects' \nsorry, couldn't find this directory"
#     else:
#         ques="Enter the absolute path \nlike '/home/path/to/NextSnakesProjects' "
#     answer, toclear = display(
#     cn=toclear,
#     text=explanation,
#     option="So, where should the Project-folder be created?",
#     defaults=None,
#     question=ques,
#     proof=None
#     )
#     path_to_project = answer
#     if os.path.isdir(path_to_project):
#         project = os.path.join(path_to_project,name)
#         if os.path.isdir(project):
#             answer, toclear = display(
#             cn=toclear,
#             text=f"In the directory you entered, a folder with the name {name} already exist. \nMaybe you should think about what you really want to do. If you want to work on \nan existing Project, use the 'append' function, otherwise use a different \nProject-name. Ciao!",
#             question="Enter to quit",
#             proof=None
#             )
#             exit()
#         os.mkdir(project)
#         os.mkdir(os.path.join(project,"FASTQ"))
#         os.mkdir(os.path.join(project,"GENOMES"))
#         os.symlink(cwd, os.path.join(project,'snakes'))
#         break
#     else:
#         switch=True



name="moin"
# title(toclear,"CREATE CONDITION-TREE")
# condition_dict = NestedDefaultDict()
# create_condition_dict(condition_dict,[name])


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

conditions=[pattern for pattern in condition_dict.get_condition_list()]

def create_sample_dirs(d,dir):
    for k,v in d.items():
        if isinstance(v, dict):
            dir.append(k)
            os.mkdir('/'+'/'.join(dir))
            create_sample_dirs(v,dir)
            dir.pop()

project='/home/roberto/testing/moin'
path_list=[x for x in project.split('/') if x]
# create_sample_dirs(condition_dict,path_list)



# switch=False
# while True:
#     if switch:
#         ques="Enter the absolute path \nlike '/home/path/to/Samples' \nsorry, couldn't find this directory"
#     else:
#         ques="Enter the absolute path \nlike '/home/path/to/Samples' "
#     switch=True
#     title(toclear,"ASSIGN SAMPLES")
#     explanation=get_doc("samples")
#     answer, toclear = display(
#     cn=toclear,
#     text=explanation,
#     option=None,
#     defaults=None,
#     question=ques,
#     proof=None
#     )
#     path_to_samples = answer
#     if os.path.isdir(path_to_samples):
#         break

# samples = [x for x in os.listdir(path_to_samples) if x.endswith(".fastq")]
# path_to_samples="/home/roberto/fakes"
# sample_dict={}
# counter=1
# for file in sorted(os.listdir(path_to_samples)):
#     if file.endswith('.fastq'):
#         sample_dict[counter]=[file, os.path.join(path_to_samples,file)]
#         counter+=1
#
# for condition in conditions:
#     samples_lines=''
#     for k,v in sample_dict.items():
#         samples_lines+=f"{' '*3}>  {k}  -  {v[0].replace('.fastq','')}\n"
#     cond_as_list=[x for x in condition.split(':')]
#     visual=location(condition_dict,[cond_as_list])
#     answer, toclear = display(
#     cn=toclear,
#     text=visual,
#     option=f"Samples found:\n\n{samples_lines}",
#     defaults=None,
#     question="enter all sample-numbers according to the displayed condition",
#     proof=None
#     )
#     toclear+=3
#     sample_numbers=[x for x in answer.split(',')]
#     for number in sample_numbers:
#         path='/'.join(cond_as_list)
#         cond_dir=os.path.join(project,path)
#         print(path)
#         print(cond_dir)
#         print(sample_dict[int(number)][1])
#         os.symlink(sample_dict[int(number)][1], os.path.join(cond_dir,sample_dict[int(number)][0]))
#         del sample_dict[int(number)]




title("SWITCH ON WORKFLOWS")
WORKFLOWS=['SEQUENCING','GENOME']
explanation=get_doc("workflows")
answer= display(
# cn=toclear,
text=explanation,
option="Enter which WORKFLOWS you would like to run",
defaults=None,
question="Enter MAPPING, TRIMMING, QC, ANNOTATE, UCSC, PEAKS, COUNTING, DE, DEU, DAS",
proof=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING","DE","DEU","DAS"]
)
for x in answer.split(','):
    WORKFLOWS.append(x)
# WORKFLOWS=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING",""]
# POSTPROCESSING=["DE","DEU","DAS",""]

template = load_configfile('configs/template_3.json')


config_dict.equip(template,conditions)
config_dict = decouple(config_dict)
# string = json.dumps(config_dict)
# config_dict = json.loads(string)
# print_dict(config_dict)

# setting_list=select_id_to_set(condition_dict)
WORKFLOWS=['DAS']

for workflow in WORKFLOWS:
    title(f"Make Settings for {workflow}")
    while True:
        d=depth(condition_dict)
        for i in range(d-1):
            visual, setting_list = select_id_to_set(condition_dict,i)
            answer= display(
            text=visual,
            option="select setting-level",
            defaults=None,
            question="enter for next Level or 'select' for set selected",
            proof=["select",""]
            )
            if answer =='select':
                break
        if answer =='select':
            break
    if 'valid' in config_dict[workflow].keys():
        if 'TOOLS' in config_dict[workflow]['valid'].keys():
            tools = display(
            text=json.dumps(condition_dict,indent=6),
            option='available Tools',
            defaults=config_dict[workflow]['valid']['TOOLS'],
            question="enter comma separated",
            proof=config_dict[workflow]['valid']['TOOLS'].keys()
            )
            dtools=config_dict[workflow]['valid']['TOOLS']
            for i in range(len(dtools.keys())):
                if not list(dtools.keys())[i] in tools:
                    del dtools[list(dtools.keys())[i]]
        if 'COMPARABLE' in config_dict[workflow]['valid'].keys():
            while True:
                comp_name = display(
                text=json.dumps(condition_dict,indent=6),
                option='enter name for comparison',
                defaults=None,
                question="enter the name of a comparison group\n\nor enter quit to continue",
                proof=None
                )
                if comp_name == 'quit':
                    break
                config_dict[workflow]['valid']['COMPARABLE'][comp_name]=[[],[]]
                answer = display(
                text=json.dumps(condition_dict,indent=6),
                option='select all keys for FIRST comparison group',
                defaults=None,
                question="enter comma separated",
                proof=[x for x in condition_dict.get_all_keys()]
                )
                config_dict[workflow]['valid']['COMPARABLE'][comp_name][0]=answer
                answer = display(
                text=json.dumps(condition_dict,indent=6),
                option='select all keys for SECOND comparison group',
                defaults=None,
                question="enter comma separated",
                proof=conditions
                )
                config_dict[workflow]['valid']['COMPARABLE'][comp_name][1]=answer


    #     for opts in options_dict[workflow]['valid'].keys():
    #         config_dict[workflow]['valid'][opts] = conversation(options_dict[workflow]['valid'][[opts]], config_dict[workflow]['valid'][opts])
    # for setting in setting_list:
    #     switch=True
    #     for set in setting:
    #         cdict=config_dict[workflow]
    #         for i in range(len(set)-1):
    #             last=set[i+1]
    #             cdict=cdict[set[i]]
    #
    #         if switch:
    #             if workflow == 'SEQUENCING':
    #                 cdict[last] = display(
    #                 text=location(condition_dict,setting),
    #                 option=options_dict[workflow],
    #                 defaults=None,
    #                 question="enter",
    #                 proof=["unpaired","paired"]
    #                 )
    #                 singles = cdict[last]
    #             elif workflow == 'GENOME':
    #                 cdict[last]= display(
    #                 text=location(condition_dict,setting),
    #                 option=options_dict[workflow],
    #                 defaults=None,
    #                 question="enter",
    #                 proof=None
    #                 )
    #                 singles = cdict[last]
    #             else:
    #                 # set_relations(cdict,workflow)
    #                 cdict[last]['ANNOTATION']= display(
    #                 text=location(condition_dict,setting),
    #                 option="set annotation for marked conditions",
    #                 defaults=cdict[last]['ANNOTATION'],
    #                 question="enter",
    #                 proof=None
    #                 )
    #                 annotation=cdict[last]['ANNOTATION']
    #                 for i in range(len(cdict[last]['OPTIONS'])):
    #                     cdict[last]['OPTIONS'][i]= display(
    #                     text=location(condition_dict,setting),
    #                     option=options_dict[workflow]['OPTIONS'][i],
    #                     defaults=cdict[last]['OPTIONS'][i],
    #                     question="wanna change? [ y / N ]",
    #                     proof=["","y","Y","N","n"]
    #                     )
    #                 options=cdict[last]['OPTIONS']
    #             switch=False
    #         else:
    #             if any(x == workflow for x in ['SEQUENCING','GENOME']):
    #                 cdict[last] = singles
    #             else:
    #                 cdict[last]['OPTIONS']=options
    #                 cdict[last]['ANNOTATION']=annotation

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
