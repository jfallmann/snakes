import os
import json
import copy
import readline
import glob
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
    def equip(self, config, conditions, WORKFLOWS):
        for k,v in config.items():
            if k in WORKFLOWS:
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
    def get_nodes(self,path=[]):
        for key, value in self.items():
            path.append(key)
            if isinstance(value, dict):
                yield '-'.join(path)
                yield from value.get_nodes(path)
                path.pop()
            else:
                yield '-'.join(path)

class Operator():
    def __init__(self):
        self.text=""
        self.option=""
        self.default=""
        self.question=""
        self.answer=""
    def clear(self, number):
        os.system(f'echo -e "\e[{number}A\033[2K"')
        for i in range(number-1):
            os.system(f'echo -e "\e[-1A\033[2K"')
        os.system(f'echo -e "\e[{number}A\03\c"')
    def get_answer(self):
        return str(self.answer)
    def complete(text, state):
        return (glob.glob(text+'*')+[None])[state]

    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    
    def proof_input(self, proof=None):
        allowed_characters=['a','b','c','d','e','f','g','h','i','j','k','l','m','n',
        'o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G',
        'H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
        '1','2','3','4','5','6','7','8','9','0','(',')','_','-',',','.',':','/']
        while True:
            global toclear
            a = input(" >>> ").strip().replace(" ","")
            if a == "outbreak":
                toclear+=1
                outbreak()
                return
            if any(x not in allowed_characters for x in a):
                self.clear(2)
                print("You used unallowed letters, try again")
                continue
            if proof is not None and proof != "only_numbers" and any(x not in proof for x in a.split(",")):
                self.clear(2)
                print(f"available are: {proof}")
                continue
            if proof=="only_numbers":
                try:
                    [float(x) for x in a.split(',')]
                    self.answer = a
                    break
                except:
                    self.clear(2)
                    print("please enter integer or float")
                    continue
            else:
                self.answer = a
                break
    def title(self, text):
        global toclear
        self.clear(toclear)
        print(f"\n{' '*(50-int((len(text)+4)/2))}> {text} <\n\n")
        toclear = 1
    def display(self, text=None, option=None, default=None, question=None, proof=None):
        global toclear
        self.clear(toclear)
        toclear=1
        print(f' ╔{"═"*98}╗');toclear+=1
        print(f" ║{' '*98}║");toclear+=1
        for line in text.split('\n'):
            print(f" ║ {line}{' '*(97-len(line))}║");toclear+=1
        print(f" ║{' '*98}║");toclear+=1
        print(f" ╠{'═'*98}╣");toclear+=1
        if option :
            print(f" ║{' '*98}║");toclear+=1
            for line in option.split('\n'):
                print(f" ║ {line}{' '*(97-len(line))}║");toclear+=1
            print(f" ║{' '*98}║");toclear+=1
        if default:
            for line in default.split('\n'):
                print(f" ║     >   {line} {' '*(88-len(line))}║");toclear+=1
            print(f" ║{' '*98}║");toclear+=1
        print(f" ╚{'═'*67} enter 'outbreak' to correct ══╝");toclear+=1
        print('\n');toclear+=1
        if question:
            for line in question.split('\n'):
                print(f" {line}");toclear+=1
        self.proof_input(proof);toclear+=1

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

def create_sample_dirs(d,dir):
    for k,v in d.items():
        if isinstance(v, dict):
            dir.append(k)
            os.mkdir('/'+'/'.join(dir))
            create_sample_dirs(v,dir)
            dir.pop()
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

def get_doc(filename):
    path = os.path.join("docs/guide",f"{filename}.txt")
    out=""
    with open(path, 'r') as f:
        out = f.read()
    return out

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
        operator.display(
        text=text,
        option=opt
        )
        if operator.get_answer():
            leafes=[x for x in operator.get_answer().split(',')]
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
def print_json(paramdict,ofn):
    global project
    with open(os.path.join(project,ofn),'w') as jsonout:
        print(json.dumps(paramdict,indent=4),file=jsonout)





##########################
# conversation functions #
##########################

conversation_dict={
"1":"new or append",
"2":"create project-folder",
"3":"select samples",
"4":"choose workflows"
}

def outbreak():
    global conversation_dict
    operator.title("OUTBREAK")
    operator.display(
    text="choose one step",
    option=None,
    default='\n'.join("%s:  %r" % (key,val) for (key,val) in conversation_dict.items()),
    question="enter number'",
    proof="only_numbers"
    )
    step = operator.get_answer()
    if step == '1':
        start()
    if step == '2':
        create_project()
    if step == '3':
        add_samples()
    if step == '4':
        select_workflows()

def start():
    operator.title("INTRO")
    operator.display(
    text=get_doc("intro"),
    option="Enter 'append' for expanding an existing configfile or 'new' for a new project",
    default=None,
    question="enter 'new' or 'append'",
    proof=['new','append']
    )
    if operator.get_answer() == 'new':
        # if any(x in os.listdir('../') for x in ['FASTQ','GENOMES']):
        #     return FOLDERERROR
        # else:
        #     return PNAME
        return create_project()
    if operator.get_answer() == 'append':
        return append()

def intro2():
    operator.title("ERROR")
    operator.display(
    text=f"In the directory you entered, a folder with the name '{project_name}' already exist. \nSo please say again: do you want to create a new project or append an existing?",
    option="Enter 'append' for expanding an existing configfile or 'new' for a new project",
    question="enter 'new' or 'append'",
    proof=['new','append']
    )
    if operator.get_answer() == 'new':
        return create_project()
    if operator.get_answer() == 'append':
        return append()

def folder_error():
    operator.title("ERROR")
    operator.display(
    text="It looks like you already set up your project-folder. \mWe would therefor skip setting it up now. \n\nEnter 'n' if you want to do that anyway.",
    option="wanna skip the Guide?",
    question="[ n / Y ]"
    )
    if operator.get_answer() == 'n':
        return project_name()
    if operator.get_answer() == 'y':
        return end()

def create_project():
    operator.title("CREATE PROJECT-FOLDER")
    operator.display(
    text=get_doc("projectfolder"),
    option="Enter the name of your Project",
    default=None,
    question="please don't use special characters",
    proof=None
    )
    global project_name
    project_name = operator.get_answer()
    return project_path()

def project_path():
    global project
    switch=False
    while True:
        if switch:
            ques="Enter the absolute path, where your project should be created\nsorry, couldn't find this directory"
        else:
            ques="Enter the absolute path, where your project-folder should be created  "
        operator.display(
        text=get_doc("projectfolder"),
        option=ques,
        question="enter it like  /home/path/to/NextSnakesProjects",
        default=None,
        proof=None
        )
        global project
        path_to_project = operator.get_answer()
        if os.path.isdir(path_to_project):
            project = os.path.join(path_to_project,project_name)
            if os.path.isdir(project):
                return intro2()
            os.mkdir(project)
            os.mkdir(os.path.join(project,"FASTQ"))
            os.mkdir(os.path.join(project,"GENOMES"))
            os.symlink(cwd, os.path.join(project,'snakes'))
            break
        else:
            switch=True
    return condition_structure()

def condition_structure():
    operator.title("CREATE CONDITION-TREE")
    operator.display(
    text=get_doc('conditiontree'),
    option="enter to continue",
    proof=None
    )
    return create_experiment()

def create_experiment():
    create_condition_dict(condition_dict,[project_name])
    global conditions
    conditions=[pattern for pattern in condition_dict.get_condition_list()]
    path_list=[x for x in project.split('/') if x]
    path_list.append('FASTQ')
    create_sample_dirs(condition_dict[project_name],path_list)
    return add_samples()

def add_samples():
    switch=False
    operator.title("ADD SAMPLES")
    while True:
        if switch:
            ques="Enter the absolute path where your samples are stored\nsorry, couldn't find this directory"
        else:
            ques="Enter the absolute path "
        switch=True
        operator.display(
        text=get_doc("samples"),
        option=ques,
        default=None,
        question="enter like  /home/path/to/Samples",
        proof=None
        )
        path_to_samples = operator.get_answer()
        if os.path.isdir(path_to_samples):
            break
    samples = [x for x in os.listdir(path_to_samples) if x.endswith(".fastq.gz")]
    global sample_dict
    sample_dict={}
    counter=1
    for file in sorted(os.listdir(path_to_samples)):
        if file.endswith('.fastq.gz'):
            sample_dict[counter]=[file, os.path.join(path_to_samples,file)]
            counter+=1
    return assign_samples()

def assign_samples():
    global sample_dict
    global conditions
    global toclear
    for condition in conditions:
        samples_lines=''
        for k,v in sample_dict.items():
            samples_lines+=f"{' '*3}>  {k}  -  {v[0].replace('.fastq.gz','')}\n"
        cond_as_list=[x for x in condition.split(':')]
        operator.display(
        text=location(condition_dict,[cond_as_list]),
        option=f"enter all sample-numbers according to the displayed condition:\n\n{samples_lines}",
        default=None,
        question="enter comma separated",
        proof='only_numbers'
        )
        sample_numbers=[x for x in operator.get_answer().split(',')]
        for number in sample_numbers:
            path='/'.join(cond_as_list[1:])
            cond_dir=os.path.join(project,'FASTQ',path)
            os.symlink(sample_dict[int(number)][1], os.path.join(cond_dir,sample_dict[int(number)][0]))
            del sample_dict[int(number)]
    return select_workflows()

def select_workflows():
    global WORKFLOWS
    global template
    global config_dict
    operator.title("SWITCH ON WORKFLOWS")
    operator.display(
    text=get_doc("workflows"),
    option="Enter which WORKFLOWS you would like to run\nchoose from: MAPPING, TRIMMING, QC, ANNOTATE, UCSC, PEAKS, COUNTING, DE, DEU, DAS ",
    default=None,
    question="Enter comma separated",
    proof=["MAPPING", "TRIMMING", "QC","ANNOTATE","UCSC","PEAKS","COUNTING","DE","DEU","DAS"]
    )
    for x in operator.get_answer().split(','):
        WORKFLOWS.append(x)
    template = load_configfile('configs/template_4.json')
    config_dict.equip(template,conditions,WORKFLOWS)
    config_dict = decouple(config_dict)
    config_dict['WORKFLOWS']=','.join(WORKFLOWS)
    return set_workflows()

def select_setting_level():
    global setting_list
    while True:
        d=depth(condition_dict)
        for i in range(d-1):
            visual, setting_list = select_id_to_set(condition_dict,i)
            operator.display(
            text=visual,
            option="enter for next Level or 'select' for set selected",
            default=None,
            question="enter to loop through condition-level",
            proof=["select",""]
            )
            if operator.get_answer() =='select':
                return

def select_tools(workflow):
    operator.display(
    text=json.dumps(condition_dict,indent=6),
    option='select from these available Tools:',
    default='\n'.join(config_dict[workflow]['valid']['TOOLS'].keys()),
    question="enter comma separated",
    proof=config_dict[workflow]['valid']['TOOLS'].keys()
    )
    dtools=config_dict[workflow]['valid']['TOOLS']
    for i in range(len(dtools.keys())):
        for tool in operator.get_answer().split(','):
            if tool not in dtools.keys():
                del config_dict[workflow]['valid']['TOOLS'][tool]

def create_comparables(workflow):
    while True:
        operator.display(
        text=json.dumps(condition_dict,indent=6),
        option="enter the name of a comparison group\n\nor enter to continue",
        default=None,
        question="please do not use special characters",
        proof=None
        )
        if operator.get_answer() == '':
            break
        comp_name=operator.get_answer()
        config_dict[workflow]['valid']['COMPARABLE'][comp_name]=[[],[]]
        operator.display(
        text=json.dumps(condition_dict,indent=6),
        option='select all keys for first comparison group',
        default='\n'.join(condition_dict.get_nodes()),
        question="enter comma separated",
        proof=[x for x in condition_dict.get_nodes()]
        )
        config_dict[workflow]['valid']['COMPARABLE'][comp_name][0]=operator.get_answer()
        operator.display(
        text=json.dumps(condition_dict,indent=6),
        option='select all keys for second comparison group',
        default='\n'.join(condition_dict.get_nodes()),
        question="enter comma separated",
        proof=[x for x in condition_dict.get_nodes()]
        )
        config_dict[workflow]['valid']['COMPARABLE'][comp_name][1]=operator.get_answer()

# def set_relations(cdict):
#     cdict['REALTIONS'].append()

def set_workflows():
    global setting_list
    global WORKFLOWS
    # setting_list=select_id_to_set(condition_dict)
    for workflow in WORKFLOWS:
        operator.title(f"Make Settings for {workflow}")
        select_setting_level()
        if 'valid' in config_dict[workflow].keys():
            if 'TOOLS' in config_dict[workflow]['valid'].keys():
                select_tools(workflow)
            if 'FEATURES' in config_dict[workflow]['valid'].keys():
                set_features(workflow)
            if 'COMPARABLE' in config_dict[workflow]['valid'].keys():
                create_comparables(workflow)

        for setting in setting_list:
            switch=True
            for set in setting:
                cdict=config_dict[workflow]
                for i in range(len(set)-1):
                    last=set[i+1]
                    cdict=cdict[set[i]]

                if switch:
                    if workflow == 'SEQUENCING':
                        operator.display(
                        text=location(condition_dict,setting),
                        option=options_dict[workflow],
                        default=None,
                        question="enter",
                        proof=["unpaired","paired"]
                        )
                        singles = cdict[last] = operator.get_answer()
                    elif workflow == 'GENOME':
                        operator.display(
                        text=location(condition_dict,setting),
                        option=options_dict[workflow],
                        default=None,
                        question="enter",
                        proof=None
                        )
                        singles = cdict[last] = operator.get_answer()
                    else:
                        if 'ANNOTATION' in cdict[last].keys():
                            # set_relations(cdict)
                            operator. display(
                            text=location(condition_dict,setting),
                            option="set annotation for marked conditions",
                            default=cdict[last]['ANNOTATION'],
                            question="enter",
                            proof=None
                            )
                            annotation = cdict[last]['ANNOTATION'] = operator.get_answer()
                        if 'OPTIONS' in cdict[last].keys():
                            for i in range(len(cdict[last]['OPTIONS'])):
                                operator.display(
                                text=location(condition_dict,setting),
                                option=options_dict[workflow]['OPTIONS'][i],
                                default='\n'.join(cdict[last]['OPTIONS'][i]),
                                question="wanna change? [ y / N ]",
                                proof=["","y","Y","N","n"]
                                )
                                if operator.get_answer().lower() == 'y':
                                    for opt in cdict[last]['OPTIONS'][i]:
                                        operator.display(
                                        text=location(condition_dict,setting),
                                        option=opt,
                                        default=None,
                                        question="enter",
                                        proof=None
                                        )
                                        opt = operator.get_answer()
                                if operator.get_answer().lower() == 'n' or operator.get_answer() == '':
                                    continue
                                cdict[last]['OPTIONS'][i]=operator.get_answer()
                        options=cdict[last]['OPTIONS']
                    switch=False
                else:
                    if any(x == workflow for x in ['SEQUENCING','GENOME']):
                        cdict[last] = singles
                    else:
                        cdict[last]['OPTIONS']=options
                        cdict[last]['ANNOTATION']=annotation
    return set_cores()

def set_cores():
    operator.title("Number of Cores")
    operator.display(
    text=get_doc('processes'),
    option="set number of cores",
    default=None,
    question="enter number",
    proof='only_numbers'
    )
    config_dict['MAXTHREADS'] = operator.get_answer()
    return end()

def end():
    global configfile
    operator.title(f"{'*'*30}")
    configfile = f"config_{project_name}.json"
    operator.display(
    text=get_doc('runsnakemake'),
    option=f"You created \n\n    > {configfile}\n\nstart RunSnakemake with:\n\n    > python3 snakes/RunSnakemake.py -c {configfile} --directory ${{PWD}}",
    question='press enter to quit the Guide'
    )


#####################
# global variables: #
#####################

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cwd=os.getcwd()

operator=Operator()
toclear=0
project_name=""
conditions=[]
WORKFLOWS=['GENOME','SEQUENCING']

template=NestedDefaultDict()
sample_dict=NestedDefaultDict()
config_dict=NestedDefaultDict()
condition_dict=NestedDefaultDict()

options_dict=NestedDefaultDict()
options_dict['COUNTING']['valid']['FEATURES'] = "set feature setting"
options_dict['COUNTING']['OPTIONS'][0] = "set feature setting"
options_dict['TRIMMING']['OPTIONS'][0] = "trimming options"
options_dict['UCSC']['OPTIONS'][0] = "ucsc options"
options_dict['PEAKS']['OPTIONS'][0] = "peaks options"
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

# # to start at set_workflows()
# WORKFLOWS=['DE']
# project_name='tacheles'
# project='/homes/brauerei/robin/test/getit'
# condition_dict['tacheles']['a']
# condition_dict['tacheles']['a']['1']
# condition_dict['tacheles']['a']['2']
# condition_dict['tacheles']['a']['3']
# condition_dict['tacheles']['b']['1']
# condition_dict['tacheles']['b']['2']
# # condition_dict['tacheles']['b']['2']['x']
# # condition_dict['tacheles']['b']['2']['y']
# condition_dict['tacheles']['b']['3']
# condition_dict['tacheles']['c']['1']
# condition_dict['tacheles']['c']['2']
# condition_dict['tacheles']['c']['3']
# conditions=[pattern for pattern in condition_dict.get_condition_list()]
# template = load_configfile('configs/template_4.json')
# config_dict.equip(template,conditions,WORKFLOWS)

########
# main #
########
def main():

    header='  _  _                     _       ___                     _\n'\
    ' | \| |    ___    __ __   | |_    / __|   _ _     __ _    | |__    ___     ___\n'\
    ' | .` |   / -_)   \ \ /   |  _|   \__ \  | ` \   / _` |   | / /   / -_)   (_-<\n'\
    ' |_|\_|   \___|   /_\_\   _\__|   |___/  |_||_|  \__,_|   |_\_\   \___|   /__/_\n'\
    '_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|_|"""""|\n'\
    ' `-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`"`-0-0-`\n'

    print("\n\n\n\n")
    for line in header.split('\n'):
        print(f"{' '*10}{line}")

    # set_workflows()
    start()
    # print_dict(config_dict)
    print_json(config_dict,configfile)

if __name__ == '__main__':
    main()
