import os
import json
import copy
import readline
import glob
from snakemake import load_configfile
from collections import defaultdict
import argparse
from lib.Logger import *
from functools import reduce
import operator

parser = argparse.ArgumentParser(description='Helper to create initial config file used for workflow processing')
parser.add_argument("-q", "--quickmode", action='store_true', default=False, help='choose quickmode to hide explanatory text')
args=parser.parse_args()

## PRINTERS
def prRed(skk): print("\033[91m{}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m{}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m{}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m{}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m{}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m{}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m{}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m{}\033[00m" .format(skk))

def print_rst(rst):
    if not args.quickmode:
        source = "./docs/source/"
        path = os.path.join(source,rst)
        with open(path, 'r') as f:
            for l in f.readlines():
                prGreen(l.replace('\n',''))
        print('\n')

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

## DICT MANIPULATORS
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
    else:
        del get_by_path(root, items[:-1])[items[-1]]

def get_conditions_from_dict(root, keylist=[]):
    for k,v in root.items():
        keylist.append(k,)
        if not v:
            yield ':'.join(keylist)
        else:
            yield from get_conditions_from_dict(v, keylist)
        keylist.pop()

def getPathesFromDict(d, value=None):
    def yield_func(d):
        q = [(d, [])]
        while q:
            n, p = q.pop(0)
            yield p
            if isinstance(n, dict):
                for k, v in n.items():
                    q.append((v, p+[k]))
            elif isinstance(n, list):
                for i, v in enumerate(n):
                    q.append((v, p+[i]))
    ret = [p for p in yield_func(d)]
    if value:
        sel = []
        for path in ret:
            if value in path:
                sel.append(path)
        return sel
    return ret

def decouple(d):
    string = json.dumps(d)
    return json.loads(string)



class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)

class PROJECT():
    def __init__(self):
        self.name = "moin"
        self.path = ""
        # self.configs = []
        self.baseDict =  NestedDefaultDict()
        self.conditionDict = NestedDefaultDict()
        self.samplesDict = NestedDefaultDict()
        self.settingsDict = NestedDefaultDict()
        self.settingsList = []
        self.workflowsDict =  NestedDefaultDict()
        self.commentsDict = NestedDefaultDict()
        # self.sampleDict = NestedDefaultDict()

class GUIDE():
    def __init__(self):
        self.text=""
        self.option=""
        self.default=""
        self.question=""
        self.answer=""
        self.toclear = 0

    def clear(self, number = None):
        if not number:
            number = self.toclear
        os.system(f'echo -e "\e[{number}A\033[2K"')
        for i in range(number-1):
            os.system(f'echo -e "\e[-1A\033[2K"')
        os.system(f'echo -e "\e[{number}A\03\c"')
        self.toclear = 0

    def proof_input(self, proof=None, spec=None):
        allowed_characters=['a','b','c','d','e','f','g','h','i','j','k','l','m','n',
        'o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G',
        'H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
        '1','2','3','4','5','6','7','8','9','0','(',')','_','-',',','.',':','/',' ']
        while True:
            if spec:
                a = rlinput(">>> ", spec)
            else:
                a = input(">>> ").strip().replace(" ","")
            if a == "outbreak":
                outbreak()
                return
            if any(x not in allowed_characters for x in a):
                self.clear(2)
                print("You used unallowed letters, try again")
                continue
            if proof is not None and proof != "only_numbers" and any(x not in proof for x in a.split(",")):
                safe = self.toclear
                self.clear(2)
                self.toclear = safe
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

    def display(self, options=None, question=None, proof=None, spec=None):
        if options:
            for k,v in options.items():
                prYellow(f"   {k}  >  {v}");
            print('\n')
        if question:
            print(question)
        self.proof_input(proof, spec);

def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

def print_dict_pointer(dict,path,copy,indent=6):
    text=json.dumps(dict, indent=indent)
    route=['step']+path.copy()
    out=f"\n{'='*60}\n\n"
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
                        option=f"enter ID's on condition level comma separated \n\nor copy {copy} with 'cp'"
                        guide.toclear += 2
                    else:
                        out+=f"{line}    <-\n"
                        option="enter ID's on conditions comma separated "
                else:
                    out+=f"{line}    <-\n"
                    option="enter ID's on conditions comma separated "

            else:
                out+=line+'\n'
        else:
            out+=line+'\n'
    out+=f"\n{'='*60}\n\n"
    return out, option

def rec_tree_builder(subtree,leafes,path=[],tree=None):
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
        text, opt = print_dict_pointer(tree, path, copy)
        for line in text.split('\n'):
            if '<-' in line:
                prYellow("  "+line)
            else:
                prRed("  "+line)
        guide.toclear += len(text.split('\n'))+2
        guide.display(
        question = opt
        )
        guide.clear()
        if guide.answer:
            guide.answer = guide.answer.rstrip(',')
            leafes=[x for x in guide.answer.split(',')]
        else:
            leafes=['']
        if leafes==["cp"]:
            leafes=copy
        rec_tree_builder(subtree[k],leafes,path,tree)
        copy=leafes
        leafes=['']
    if len(path)>0:
        path.pop()
    return

def depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0

def select_id_to_set(cdict,i,indent=6):
    text=json.dumps(cdict, indent=indent)
    project.settingsList = []
    d = depth(cdict)
    path=[]
    reminder=''
    counter=0
    prRed(f"\n{'='*60}\n")
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
                project.settingsList.append([])
        elif level<i and '{}' in line:
            counter +=1
            project.settingsList.append([])
        if '{}' in line:
            if ',' in line:
                out = f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}"
                if counter % 2:
                    prPurple("  "+out)
                else:
                    prLightPurple("  "+out)
            else:
                out = f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}"
                if counter % 2:
                    prPurple("  "+out)
                else:
                    prLightPurple("  "+out)
            project.settingsList[-1].append(path)
        else:
            prRed("  "+line)
        guide.toclear +=1
    prRed(f"\n{'='*60}\n")
    guide.toclear += 6

def location(dictionary,setting,indent=6):
    prRed(f"\n{'='*60}\n")
    spots=copy.deepcopy(setting)
    d = depth(dictionary)
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
                            prYellow(f"  {line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-")
                        else:
                            prYellow(f"  {line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-")
                        switch=False
        if switch:
            prRed("  "+line)
        guide.toclear += 1
    prRed(f"\n{'='*60}\n")
    guide.toclear += 4

readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: menu-complete")
readline.set_completer(complete)

project = PROJECT()
guide = GUIDE()
############################
####    CONVERSATION    ####
############################

def prepare_project(template):
    # add template dict to project object
    project.baseDict = template
    # add comments to commentsdict and remove them from baseDict
    comment_pathes = getPathesFromDict(project.baseDict, "comment")
    for path in comment_pathes:
        if path[-1] != "comment":
            continue
        opt = get_by_path(project.baseDict, path)
        set_by_path(project.commentsDict, path, opt)
        del_by_path(project.baseDict, path)

    return intro()

def intro():
    print_rst("intro.rst"),
    guide.display(
    question = "Enter 'expand' for expanding an existing configfile or 'new' for a new project",
    proof = ["new", "expand"],
    )
    if guide.answer == 'new':
        return new()
    if guide.answer == 'expand':
        return expand()

def new():
    print_rst("howitworks.rst")
    er = 0
    while True:
        if er == 0:
            ques = "Enter the absolute path, where your project-folder should be created"
        if er == 1:
            ques = "couldn't find this directory"
        if er == 2:
            ques = f"In the directory you entered, a folder with the name '{project.name}' already exist."
        print("enter like  /path/to/MyNewProject")
        guide.display(
        question = ques,
        spec = os.getcwd()
        )
        project.name = os.path.basename(guide.answer)
        project.path = guide.answer
        if os.path.isdir(project.path):
            er = 2
            continue
        if os.path.isdir(os.path.dirname(project.path)):
            break
        else:
            er = 1
    return explain_condition_tree()

def explain_condition_tree():
    print_rst("ics.rst")
    guide.display(
    question = "enter to continue"
    )
    return create_condition_tree()

def create_condition_tree():
    while True:
        rec_tree_builder(project.conditionDict,[project.name])
        print("\nthis is your new condition tree:\n")
        print_dict(project.conditionDict)
        print('\n')
        guide.display(
        question = "press enter to continue or type 'correct' to cretae it again",
        proof = ['','correct'],
        )
        if guide.answer == 'correct':
            project.conditionDict = NestedDefaultDict()
        else:
            project.settingsDict = decouple(project.conditionDict)
            return add_sample_dirs()

def add_sample_dirs():
    print_rst("samples.rst")
    print('\n')
    path_to_samples_dict= NestedDefaultDict()
    er = 0
    while True:
        if er == 0:
            ques="Enter an absolute path \n\nor press enter to continue"
        if er == 1:
            ques=f"Sorry, couldn't find {dir}\n\nEnter an absolute path where samples are stored"
        if er == 2:
            ques=f"We need samples to continue, so please enter an path\n\nEnter an absolute path where samples are stored"
        guide.display(
        question = ques,
        options = path_to_samples_dict,
        spec = os.getcwd()
        )
        dir = guide.answer
        if os.path.isdir(dir):
            project.samplesDict[dir] = []
            for dirpath, dirnames, filenames in os.walk(dir):
                for filename in [f for f in filenames if f.endswith(".fastq.gz")]:
                    project.samplesDict[dir].append(filename)
            path_to_samples_dict[dir] = f"{len(project.samplesDict[dir]) } Files found"
            guide.clear(len(path_to_samples_dict)+5)
            er = 0
            continue
        if guide.answer == '' and len(project.samplesDict) == 0 :
            er = 2
            guide.clear(4)
            continue
        if guide.answer == '' and len(project.samplesDict) != 0 :
            break
            switch = False
        if not os.path.isdir(dir):
            er = 1
            if path_to_samples_dict:
                guide.clear(len(path_to_samples_dict)+2)
            guide.clear(4)
            continue
    counter=1
    return assign_samples()

def assign_samples():
    print("\nAssign")
    conditions=[pattern for pattern in get_conditions_from_dict(project.conditionDict)]
    samples = NestedDefaultDict()
    while True:
        number = 0
        for k,v in project.samplesDict.items():
            for samp in v:
                number +=1
                samples[number] = f"{samp.replace('.fastq.gz','')}"
        for condition in conditions:
            cond_as_list=[x for x in condition.split(':')]
            location(project.settingsDict,[cond_as_list])
            guide.display(
            question= f"enter all sample-numbers according to the displayed condition comma separated",
            options = samples,
            proof= [str(i) for i in samples.keys()]
            )
            select = []
            for num in guide.answer.split(','):
                select.append(samples[int(num)])
                samples.pop(int(num))
            set_by_path(project.settingsDict,cond_as_list,{"SAMPLES":select},)
            guide.toclear += len(samples)
            guide.toclear += len(select)
            guide.toclear += 6
            guide.clear(guide.toclear)
        print("\nthis is your sample assignment:\n")
        print_dict(project.settingsDict)
        guide.display(
        question = "\npress enter to continue or type 'correct' to assign samples again"
        )
        if guide.answer == 'correct':
            project.settingsDict = decouple(project.conditionDict)
        else:
            break
    return choose_workflows()

def expand():
    er = 0
    while True:
        if er == 0:
            ques = "Enter the absolut path of the config file to be expanded"
        if er == 1:
            ques = "couldn't find the file"
        if er == 2:
            ques = "can't read the file, check if it is the right file or if it is corrupted"
        print("\n")
        guide.display(
        question = ques,
        spec = os.getcwd()
        )
        if not os.path.isfile(guide.answer):
            er = 1
            continue
        try:
            config = load_configfile(guide.answer)
            project.path = os.path.dirname(guide.answer)
            project.name = list(config['SETTINGS'].keys())[0]
        except:
            er = 2

        condition_pathes = getPathesFromDict(config, "SAMPLES")
        for path in condition_pathes:
            if path[-1] == "SAMPLES":
                path = path[1:-1]
                set_by_path(project.conditionDict, path, {})
        #show conditiontree
        prRed("\nFollowing configuration was found :\n")
        prRed("Condition-Tree:")
        print_dict(project.conditionDict)
        # #show settings
        # prRed("\nSettings:")
        # print_dict(config["SETTINGS"])
        #show Workflows
        prRed("\nactive WORKFLOWS:")
        active_workflows = config['WORKFLOWS'].split(',')
        print(active_workflows)
        prRed("\ninactive WORKFLOWS:")
        inactive_workflows = list(config.keys())
        for e in ["WORKFLOWS","BINS","MAXTHREADS","SETTINGS"]:
            inactive_workflows.remove(e)
        for e in config['WORKFLOWS'].split(','):
            inactive_workflows.remove(e)
        print(inactive_workflows)
        guide.display(
        question = "\npress enter to add worfklow to this config or type 'correct' to choose another file",
        proof = ['','correct']
        )
        if guide.answer == '':
            return choose_workflows(inactive_workflows+active_workflows)
        if guide.answer == 'correct':
            project.conditionDict = NestedDefaultDict()
            continue

def choose_workflows(existing_workflows = None):
    print_rst("worflows.rst")
    possible_workflows = list(project.baseDict.keys())
    for e in ["WORKFLOWS","BINS","MAXTHREADS","SETTINGS"]:
        possible_workflows.remove(e)
    for e in existing_workflows:
        possible_workflows.remove(e)
    posWorkDict = NestedDefaultDict()
    counter = 1
    for w in possible_workflows:
        posWorkDict[counter]=w
        counter += 1
    guide.display(
    question = "Enter which WORKFLOWS you would like to add",
    options = posWorkDict,
    proof = list(str(i) for i in posWorkDict.keys())
    )
    for number in guide.answer.split(','):
        wf = posWorkDict[int(number)]
        project.workflowsDict[wf]
    print_dict(project.workflowsDict)
    input()
    return select_conditioning()

def select_conditioning():
    while True:
        d=depth(project.conditionDict)
        for i in range(d-1):
            select_id_to_set(project.conditionDict, i)
            guide.display(
            question = "enter to loop through the possible condition-settings\nyou will set all conditions with the same number at once afterwards \n\nenter 'select' for your setting",
            proof=["select",""]
            )
            guide.toclear += 5
            if guide.answer == 'select':
                return set_settings()
            else:
                guide.clear()

def set_settings():
    print_rst("settings.rst")

    for setting in project.settingsList:
        conditionnames = []
        for maplist in setting:
            condition = ":".join(maplist)
            conditionnames.append(condition)
            for key in ["SAMPLES","TYPES","GROUPS","BATCHES"]:
                setInDict(project.settingsDict,maplist+[key],[])
            for key in ['SEQUENCING','REFERENCE','INDEX','PREFIX']:
                setInDict(project.settingsDict,maplist+[key],"")
            setInDict(project.settingsDict,maplist+['ANNOTATION',"GTF"],"")
            setInDict(project.settingsDict,maplist+['ANNOTATION',"GFF"],"")
            samplecount=0
            for k,v in project.sampleDict.items():
                if len(v) == 3: # sampleDict got 3 values if sample is assignet to a condition, else its only path and name as values available
                    samplename = v[0]
                    if v[2] == condition:
                        samplecount+=1
                        setInDict(project.settingsDict,maplist+["SAMPLES"],samplename)
        for key in ['TYPES',"GROUPS","BATCHES"]:
            operator.display(
            text=location(getFromDict(project.settingsDict,setting[0]),setting),
            option=f"Make settings for conditions: \n\n {' '.join(conditionnames)}.\nOr press enter to skip\n\n"+options_dict[key],
            default='\n'.join(project.configDict["SETTINGS"][key]),
            )
            for maplist in setting:
                for i in range(samplecount):
                    setInDict(project.settingsDict,maplist+[key],operator.get_answer())

        for key in ['SEQUENCING','REFERENCE','INDEX','PREFIX']:
            if key == 'SEQUENCING':
                p = ["single","paired"]
            else:
                p = None
            cs = '\n  > '.join(conditionnames)
            operator.display(
            text=location(getFromDict(project.settingsDict,setting[0]),setting),
            option=f"Make settings for conditions: \n\n  > '{cs}'.\n\nOr press enter to skip\n\n"+options_dict[key],
            default='\n'.join(project.configDict["SETTINGS"][key]),
            proof = p
            )
            for maplist in setting:
                setInDict(project.settingsDict,maplist+[key],operator.get_answer())
        for key in ['GTF', 'GFF']:
            operator.display(
            text=location(getFromDict(project.settingsDict,setting[0]),setting),
            option=f"Make settings for conditions:   '{', '.join(conditionnames)}'.\nOr press enter to skip\n\n"+options_dict['ANNOTATION'][key],
            default='\n'.join(project.configDict["SETTINGS"]['ANNOTATION'][key]),
            proof = p
            )
            for maplist in setting:
                setInDict(project.settingsDict,maplist+['ANNOTATION',key],operator.get_answer())
    return set_workflows()

# def set_workflows():
#     return finalize()
#
# def finalize():
#     return create_project()
#
# def create_project():
#     return


####################
####    MAIN    ####
####################

# os.chdir(os.path.realpath(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
if __name__ == '__main__':


    template = load_configfile("configs/template_base_commented.json")

    # prGreen("\n/// WELCOME TO THE NEXTSNAKES CONFIGURATOR GUIDE")
    if args.quickmode:
        prRed("\nrunning in quickmode\n")
    else:
        prRed("\nrunning in explanation mode\n")


    # prepare_project(template)
    project.name = "moininger"

    project.conditionDict = {
      "practical": {
            "normal": {},
            "tumor": {},
            "allin": {},
            "allout": {}
      }
      }
    project.settingsDict = decouple(project.conditionDict)
    add_sample_dirs()
    # test()
