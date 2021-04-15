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
        print('\n')
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

def setInDict(dataDict, maplist, value):
    first, rest = maplist[0], maplist[1:]
    if rest:
        try:
            if not isinstance(dataDict[first], dict):
                dataDict[first] = {}
        except KeyError:
            dataDict[first] = {}
        setInDict(dataDict[first], rest, value)
    else:
        try:
            if isinstance(dataDict[first], list):
                dataDict[first].append(value)
            else:
                dataDict[first] = value
        except:
            dataDict[first] = value

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
        self.cores = 1
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
        self.mode = ''
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

def optionsDictToString(d):
    return ','.join(map(' '.join, d.items()))

def stringToOptionsDict(s):
    optsDict = NestedDefaultDict()
    s = ' '.join(s.split())
    pairs = s.split(',')
    pairs = [p.strip() for p in pairs]
    for pair in pairs:
        key = pair.split(' ')[0]
        try:
            value = pair.split(' ')[1]
            optsDict[key] = value
        except:
            optsDict[key] = ""
    return optsDict

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
        guide.mode = 'new'
        return new()
    if guide.answer == 'expand':
        guide.mode = 'expand'
        return expand()

def new():
    print_rst("howitworks.rst")
    er = 0
    while True:
        if er == 0:
            ques = "Enter the absolute path where your project-folder should be created"
        if er == 1:
            ques = "couldn't find this directory"
        if er == 2:
            ques = f"In the directory you entered, a folder with the name '{project.name}' already exist."
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
            break
    return add_sample_dirs()

def add_sample_dirs():
    print_rst("samples.rst")
    print('\n')
    path_to_samples_dict= NestedDefaultDict()
    er = 0
    while True:
        if er == 0:
            ques="Enter an absolute path nor type 'select' to continue"
        if er == 1:
            ques=f"Sorry, couldn't find '{dir}'. Enter an absolute path where samples are stored"
        if er == 2:
            ques=f"Samples must be specified to continue. Enter an absolute path where samples are stored"
        guide.display(
        question = ques,
        options = path_to_samples_dict,
        spec = os.getcwd()
        )
        dir = guide.answer
        if os.path.isdir(dir):
            for dirpath, dirnames, filenames in os.walk(dir):
                for filename in [f for f in filenames if f.endswith(".fastq.gz")]:
                    project.samplesDict[os.path.join(dirpath,filename)]= {}
            path_to_samples_dict[dir] = f"{len(project.samplesDict[dir]) } Files found"
            guide.clear(len(path_to_samples_dict)+3)
            er = 0
            continue
        if guide.answer == 'select' and len(project.samplesDict) == 0 :
            er = 2
            guide.clear(3)
            continue
        if guide.answer == 'select' and len(project.samplesDict) != 0 :
            break
            switch = False
        if not os.path.isdir(dir):
            er = 1
            if path_to_samples_dict:
                guide.clear(len(path_to_samples_dict)+2)
            guide.clear(3)
            continue
    counter=1
    return assign_samples()

def assign_samples():
    conditions=[pattern for pattern in get_conditions_from_dict(project.conditionDict)]
    samples = NestedDefaultDict()
    project.settingsDict = decouple(project.conditionDict)
    while True:
        number = 1
        for samp in project.samplesDict.keys():
            samples[number] = samp
            number +=1
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
                s = os.path.basename(samples[int(num)]).replace('.fastq.gz','')
                set_by_path(project.samplesDict,[samples[int(num)]],condition)
                select.append(s)
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
            expand_config = load_configfile(guide.answer)
            project.path = os.path.dirname(guide.answer)
            project.name = list(expand_config['SETTINGS'].keys())[0]
            project.cores = expand_config["MAXTHREADS"]
        except:
            er = 2

        condition_pathes = getPathesFromDict(expand_config, "SAMPLES")
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
        active_workflows = expand_config['WORKFLOWS'].split(',')
        print(active_workflows)
        prRed("\ninactive WORKFLOWS:")
        inactive_workflows = list(expand_config.keys())
        for e in ["WORKFLOWS","BINS","MAXTHREADS","SETTINGS"]:
            inactive_workflows.remove(e)
        for wf in inactive_workflows:
            project.workflowsDict[wf] = decouple(expand_config[wf])
        for e in expand_config['WORKFLOWS'].split(','):
            inactive_workflows.remove(e)
        print(inactive_workflows)
        guide.display(
        question = "\npress enter to add worfklows to this config or type 'correct' to choose another file",
        proof = ['','correct']
        )
        if guide.answer == '':
            project.settingsDict = expand_config['SETTINGS']
            break
        if guide.answer == 'correct':
            project.conditionDict = NestedDefaultDict()
            continue
    return choose_workflows(inactive_workflows+active_workflows)

def choose_workflows(existing_workflows = None):
    print_rst("workflows.rst")
    possible_workflows = list(project.baseDict.keys())
    for e in ["WORKFLOWS","BINS","MAXTHREADS","SETTINGS"]:
        possible_workflows.remove(e)
    if existing_workflows:
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
    print(f"\nSelected Workflows: {list(project.workflowsDict.keys())}")
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
                if guide.mode == "new":
                    return set_settings()
                if guide.mode == "expand":
                    return set_workflows()
            else:
                guide.clear()

def set_settings():
    print_rst("settings.rst")
    safety_dict = decouple(project.settingsDict)
    while True:
        for setting in project.settingsList:
            conditionnames = []
            opt_dict = NestedDefaultDict()
            for maplist in setting:
                condition = ":".join(maplist)
                conditionnames.append(condition)
                for key in ['TYPES',"GROUPS","BATCHES"]:
                    setInDict(project.settingsDict,maplist+[key],[])
                    opt_dict[key] = ''
                for key in ['SEQUENCING','REFERENCE','INDEX','PREFIX']:
                    setInDict(project.settingsDict,maplist+[key],"")
                    opt_dict[key] = ''
                setInDict(project.settingsDict,maplist+['ANNOTATION',"GTF"],"")
                setInDict(project.settingsDict,maplist+['ANNOTATION',"GFF"],"")
                opt_dict["GTF"] = ''
                opt_dict["GFF"] = ''

            for key in ['TYPES',"GROUPS","BATCHES",'SEQUENCING','REFERENCE','INDEX','PREFIX','GTF','GFF']:
                guide.toclear = 0
                if key == 'SEQUENCING':
                    p = ["single","paired"]
                else:
                    p = None
                if key in ['REFERENCE','GTF','GFF']:
                    s = os.getcwd()
                else:
                    s = None
                location(project.conditionDict,setting)
                guide.display(
                question=f"comment: {project.commentsDict['SETTINGS']['comment'][key]}",
                options = opt_dict,
                proof = p,
                spec = s
                )
                # print_dict(project.settingsDict)
                for maplist in setting:
                    samps_number = len(get_by_path(project.settingsDict,maplist+["SAMPLES"]))
                    if key in ['TYPES',"GROUPS","BATCHES"]:
                        for i in range(samps_number):
                            setInDict(project.settingsDict,maplist+[key],guide.answer)
                            opt_dict[key] = guide.answer
                    if key in ['GTF','GFF']:
                        setInDict(project.settingsDict,maplist+['ANNOTATION',key],guide.answer)
                        opt_dict[key] = guide.answer
                    else:
                        setInDict(project.settingsDict,maplist+[key],guide.answer)
                        opt_dict[key] = guide.answer
                guide.toclear += 15
                guide.clear(guide.toclear)
        print("\nSETTINGS key:")
        print_dict(project.settingsDict)
        guide.display(
        question = "\npress enter to accept these settings or type 'correct'",
        proof = ['','correct']
        )
        if guide.answer == '':
            break
        if guide.answer == 'correct':
            project.settingsDict = decouple(safety_dict)
            continue
    return set_workflows()

def set_workflows():
    for workflow in project.workflowsDict.keys():
        # k = list(project.conditionDict.keys())[0]
        if not project.workflowsDict[workflow]:
            prGreen(f"\nMake Settings for {workflow}\n")
            opt_dict=NestedDefaultDict()
            if 'TOOLS' in project.baseDict[workflow].keys():
                number = 1
                for k in project.baseDict[workflow]['TOOLS'].keys():
                    opt_dict[number] = k
                    number +=1
                guide.display(
                question='Select from these available Tools comma separated:',
                options = opt_dict,
                proof=[str(i) for i in opt_dict.keys()]
                )
                for number in guide.answer.split(','):
                    project.workflowsDict[workflow]['TOOLS'][opt_dict[int(number)]] = project.baseDict[workflow]["TOOLS"][opt_dict[int(number)]]

            if 'CUTOFFS' in project.baseDict[workflow].keys():
                project.workflowsDict[workflow].update({'CUTOFFS':{}})
                project.workflowsDict[workflow]["CUTOFFS"].update(project.baseDict[workflow]["CUTOFFS"])
                for key,value in project.baseDict[workflow]['CUTOFFS'].items():
                    print('\n')
                    guide.display(
                    question=f'Set {key}',
                    proof="only_numbers",
                    spec = value
                    )
                    set_by_path(project.workflowsDict,[workflow,"CUTOFFS",key],str(guide.answer))

            if 'COMPARABLE' in project.baseDict[workflow].keys():
                print_rst("comparable.rst")
                while True:
                    guide.display(
                    question="\nenter the naming to add a comparison group or enter to continue",
                    )
                    if guide.answer == '':
                        break
                    comp_name=guide.answer
                    project.workflowsDict[workflow]['COMPARABLE'][comp_name]=[[],[]]
                    allp = getPathesFromDict(project.conditionDict)
                    number = 1
                    opt_dict = NestedDefaultDict()
                    for p in allp:
                        if p !=[]:
                            opt_dict[number] = ':'.join(p)
                            number+=1
                    for i in [0,1]:
                        print('\n')
                        guide.display(
                        question=f'select all keys for comparison group {i+1}',
                        options= opt_dict,
                        proof=[str(i) for i in opt_dict]
                        )
                        for num in guide.answer.split(','):
                            project.workflowsDict[workflow]['COMPARABLE'][comp_name][int(i)].append(opt_dict[int(num)])
                            opt_dict.pop(int(num))

            for setting in project.settingsList:
                for tool in project.workflowsDict[workflow]['TOOLS'].keys():
                    for maplist in setting:
                        setInDict(project.workflowsDict,[workflow]+maplist+[tool,"OPTIONS"],[])
                    for i in range(len(project.baseDict[workflow][tool]['OPTIONS'])):
                        if project.baseDict[workflow][tool]['OPTIONS'][i]:
                            call =  optionsDictToString(project.baseDict[workflow][tool]['OPTIONS'][i])
                            guide.toclear = 0
                            location(project.conditionDict,setting)
                            print(f"Tool: {tool}\n")
                            guide.display(
                            question=f"comment: {project.commentsDict[workflow][tool]['comment'][i]}",
                            spec= call
                            )
                            optsDict = stringToOptionsDict(guide.answer)
                            for maplist in setting:
                                setInDict(project.workflowsDict,[workflow]+maplist+[tool,"OPTIONS"],optsDict)
                            guide.toclear += 6
                            guide.clear()
                        else:
                            for maplist in setting:
                                setInDict(project.workflowsDict,[workflow]+maplist+[tool,"OPTIONS"],{})

    if guide.mode == "new":
        return set_cores()
    if guide.mode == "expand":
        return finalize()

def set_cores():
    print('\n')
    guide.display(
    question="Several workflows use multithreading, set the maximum number of cores that can be used",
    proof='only_numbers'
    )
    project.cores = str(guide.answer)
    return finalize()

def finalize():
    # print(project.name)
    # print(project.path)
    # print(project.cores)
    # print_dict(project.conditionDict)
    # print(project.settingsList)
    # print_dict(project.settingsDict)
    # print_dict(project.workflowsDict)
    # print_dict(project.samplesDict)
    # print_dict(project.commentsDict)
    final_dict = NestedDefaultDict()

    final_dict["WORKFLOWS"] = ','.join(project.workflowsDict.keys())
    final_dict["BINS"] = project.baseDict["BINS"]
    final_dict["MAXTHREADS"] = project.cores
    final_dict["SETTINGS"] = project.settingsDict
    final_dict.update(project.workflowsDict)

    configfile = f"config_{project.name}.json"
    print_dict(final_dict)
    print('\n')

    if guide.mode == "new":
        space = len(configfile)
        print("Above is your final configuration of NextSnakes. The Guide will create this directory as new project:\n")
        prGreen(f"  {os.path.dirname(project.path)}")
        prGreen(f"  └─{os.path.basename(project.path)}")
        prGreen(f"     ├─nextsnakes{' '*(space-10)}   >  symlink to {os.getcwd()}")
        prGreen(f"     ├─FASTQ{' '*(space-5)}   >  contains symlinks of your samplefiles")
        prGreen(f"     ├─GENOMES{' '*(space-7)}   >  contains symlinks of your reference files")
        prGreen(f"     └─{configfile}   >  your brand new configuration file")

        guide.display(
        question="\npress enter to create your project or type 'abort' before it gets serious",
        proof = ['','abort']
        )
    if guide.mode == "expand":
        print("Above is your updated configuration of NextSnakes\n")
        guide.display(
        question=f"\npress enter to update {configfile} or type 'abort' before it gets serious",
        proof = ['','abort']
        )

    if guide.answer == 'abort':
        quit()
    else:
        return create_project(final_dict)

def create_project(final_dict):
    if guide.mode == "new":

        # create Project Folder
        cwd=os.getcwd()
        os.mkdir(project.path)
        fastq = os.path.join(project.path,"FASTQ")
        gen = os.path.join(project.path,"GENOMES")
        os.mkdir(fastq)
        os.mkdir(gen)
        os.symlink(cwd, os.path.join(project.path,'nextsnakes'))

        # LINK samples into FASTQ and insert samplenames in dict
        for sample,condition in project.samplesDict.items():
            if condition:
                cond_as_list=[x for x in condition.split(':')]
                os.chdir(fastq)
                for dir in cond_as_list:
                    if not os.path.exists(os.path.join(dir)):
                        os.mkdir(os.path.join(dir))
                    os.chdir(os.path.join(dir))
                path='/'.join(cond_as_list)
                cond_dir=os.path.join(fastq,path)
                os.symlink(sample, os.path.join(cond_dir,os.path.basename(sample)))

        # link reference and annotation
        for setting in project.settingsList:
            for condition in setting:
                ref = get_by_path(project.settingsDict,condition + ['REFERENCE'])
                if os.path.isfile(ref):
                    if not os.path.exists(os.path.join(gen,os.path.basename(ref))):
                        os.symlink(ref, os.path.join(gen,os.path.basename(ref)))
                    f = os.path.join(gen,os.path.basename(ref))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(project.settingsDict,condition+ ['REFERENCE'],rel)
                else:
                    prRed(f"WARNING: reference path at {condition} is not correct, could not symlink, please do by hand")
                    setInDict(project.settingsDict,condition+ ['REFERENCE'],"EMPTY")

                gtf = get_by_path(project.settingsDict,condition + ['ANNOTATION','GTF'])
                if os.path.isfile(gtf):
                    if not os.path.exists(os.path.join(gen,os.path.basename(gtf))):
                        os.symlink(ref, os.path.join(gen,os.path.basename(gtf)))
                    f = os.path.join(gen,os.path.basename(gtf))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(project.settingsDict,condition+['ANNOTATION','GTF'],rel)
                else:
                    prRed(f"WARNING: GTF path at {condition} is not correct, could not symlink, please do by hand")
                    setInDict(project.settingsDict,condition+['ANNOTATION','GTF'],"EMPTY")

                gff = get_by_path(project.settingsDict,condition + ['ANNOTATION','GFF'])
                if os.path.isfile(gff):
                    if not os.path.exists(os.path.join(gen,os.path.basename(gff))):
                        os.symlink(ref, os.path.join(gen,os.path.basename(gff)))
                    f = os.path.join(gen,os.path.basename(gff))
                    rel = os.path.os.path.relpath(f, start=project.path)
                    setInDict(project.settingsDict,condition+['ANNOTATION','GFF'], rel)
                else:
                    prRed(f"WARNING: GFF path at {condition} is not correct, could not symlink, please do by hand")
                    setInDict(project.settingsDict,condition+['ANNOTATION','GFF'], "EMPTY")

    with open(os.path.join(project.path,f"config_{project.name}.json"),'w') as jsonout:
        print(json.dumps(final_dict,indent=4),file=jsonout)

    configfile = f"config_{project.name}.json"
    print(f"\nStart RunSnakemake with")
    prGreen(f"\n  python3 nextsnakes/RunSnakemake.py -c {configfile} --directory ${{PWD}}\n\n")

####################
####    TEST    ####
####################

def test_settings(template,sl=[]):
    project.baseDict = template
    project.name = "GGG"
    project.path = "/home/pit/NextSnakes/GGG"
    project.cores = 20
    project.conditionDict = {
          "GGG": {
                "A": {
                      "1": {},
                      "2": {}
                },
                "B": {
                      "1": {},
                      "2": {}
                },
                "C": {
                      "1": {},
                      "2": {}
                }
          }
    }
    project.settingsList = [[['GGG', 'A', '1'], ['GGG', 'A', '2'], ['GGG', 'B', '1'], ['GGG', 'B', '2'], ['GGG', 'C', '1'], ['GGG', 'C', '2']]]
    project.settingsDict = {
          "GGG": {
                "A": {
                      "1": {
                            "SAMPLES": [
                                  "hcc1395_tumor_rep1_R1",
                                  "hcc1395_tumor_rep1_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff.gz"
                            }
                      },
                      "2": {
                            "SAMPLES": [
                                  "hcc1395_tumor_rep2_R1",
                                  "hcc1395_tumor_rep2_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff3.gz"
                            }
                      }
                },
                "B": {
                      "1": {
                            "SAMPLES": [
                                  "hcc1395_tumor_rep3_R1",
                                  "hcc1395_tumor_rep3_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff3.gz"
                            }
                      },
                      "2": {
                            "SAMPLES": [
                                  "hcc1395_normal_rep1_R1",
                                  "hcc1395_normal_rep1_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff3.gz"
                            }
                      }
                },
                "C": {
                      "1": {
                            "SAMPLES": [
                                  "hcc1395_normal_rep2_R1",
                                  "hcc1395_normal_rep2_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff3.gz"
                            }
                      },
                      "2": {
                            "SAMPLES": [
                                  "hcc1395_normal_rep3_R1",
                                  "hcc1395_normal_rep3_R2"
                            ],
                            "TYPES": [
                                  "normal",
                                  "normal",
                                  "normal"
                            ],
                            "GROUPS": [
                                  "tachauch",
                                  "tachauch",
                                  "tachauch"
                            ],
                            "BATCHES": [
                                  "1",
                                  "1",
                                  "1"
                            ],
                            "SEQUENCING": "single",
                            "REFERENCE": "/home/pit/NextSnakes/practical/GENOMES/hg38/hg38.extended.fa.gz",
                            "INDEX": "",
                            "PREFIX": "",
                            "ANNOTATION": {
                                  "GTF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gtf.gz",
                                  "GFF": "/home/pit/NextSnakes/practical/GENOMES/hg38/gencode.v35.annotation.gff3.gz"
                            }
                      }
                }
          }
    }
    if "workflows" in sl:
        project.workflowsDict = {
              "DTU": {
                    "GGG": {
                          "A": {
                                "1": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                },
                                "2": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                }
                          },
                          "B": {
                                "1": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                },
                                "2": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                }
                          },
                          "C": {
                                "1": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                },
                                "2": {
                                      "dexseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      },
                                      "drimseq": {
                                            "OPTIONS": [
                                                  {
                                                        "--gencode": ""
                                                  },
                                                  {
                                                        "-l": "A",
                                                        "--gcBias": ""
                                                  }
                                            ]
                                      }
                                }
                          }
                    },
                    "TOOLS": {
                          "dexseq": "Analysis/DTU/DEXSEQ.R",
                          "drimseq": "Analysis/DTU/DRIMSEQ.R"
                    },
                    "COMPARABLE": {
                          "moininger": [
                                [
                                      "GGG:A"
                                ],
                                [
                                      "GGG:B",
                                      "GGG:C"
                                ]
                          ]
                    }
              }
        }
    project.samplesDict ={
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep1_R1.fastq.gz": "GGG:A:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep1_R2.fastq.gz": "GGG:A:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep2_R1.fastq.gz": "GGG:A:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep2_R2.fastq.gz": "GGG:A:2",
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep3_R1.fastq.gz": "GGG:B:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/tumor/hcc1395_tumor_rep3_R2.fastq.gz": "GGG:B:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep1_R1.fastq.gz": "GGG:B:2",
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep1_R2.fastq.gz": "GGG:C:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep2_R1.fastq.gz": "GGG:C:1",
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep2_R2.fastq.gz": {},
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep3_R1.fastq.gz": {},
      "/home/pit/NextSnakes/practical/FASTQ/practical/normal/hcc1395_normal_rep3_R2.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/tumor/hcc1395_tumor_rep3_R1_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/tumor/hcc1395_tumor_rep3_R2_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/tumor/hcc1395_tumor_rep1_R1_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/tumor/hcc1395_tumor_rep1_R2_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/normal/hcc1395_normal_rep3_R1_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/normal/hcc1395_normal_rep1_R1_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/normal/hcc1395_normal_rep3_R2_trimmed.fastq.gz": {},
      "/home/pit/NextSnakes/practical/TRIMMED_FASTQ/hisat2-trimgalore-fastqc/practical/normal/hcc1395_normal_rep1_R2_trimmed.fastq.gz": "GGG:C:2"
}


    project.commentsDict = {
          "SETTINGS": {
                "comment": {
                      "GROUPS": "set groups",
                      "TYPES": "set types",
                      "BATCHES": "set batches",
                      "SEQUENCING": "paired or single",
                      "REFERENCE": "set path to reference",
                      "INDEX": "set index",
                      "PREFIX": "set prefix",
                      "GTF": "set path to gtf",
                      "GFF": "set path to gff"
                }
          },
          "DTU": {
                "drimseq": {
                      "comment": [
                            "set Salmon INDEXing options",
                            "set Salmon MAPPING options"
                      ]
                },
                "dexseq": {
                      "comment": [
                            "set Salmon INDEXing options",
                            "set Salmon MAPPING options"
                      ]
                }
          }
    }







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


    # test_settings(template,"workflows")

    # add_sample_dirs()
    # assign_samples()
    # set_workflows()
    prepare_project(template)
