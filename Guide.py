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

class PROJECT():
    def __init__(self):
        self.name = ""
        self.path = ""
        self.cores = ""
        self.gitLink = ""
        self.configDict = NestedDefaultDict()
        self.workflowsDict =  NestedDefaultDict()
        self.conditionDict = NestedDefaultDict()
        self.sampleDict = NestedDefaultDict()
        self.settingsDict = NestedDefaultDict()
        self.settingsList = []

class OPERATOR():
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
    def proof_input(self, proof=None, spec=None):
        allowed_characters=['a','b','c','d','e','f','g','h','i','j','k','l','m','n',
        'o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G',
        'H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
        '1','2','3','4','5','6','7','8','9','0','(',')','_','-',',','.',':','/',' ']
        while True:
            global toclear
            if spec:
                a = rlinput(" >>> ", spec)
            else:
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
    def display(self, text=None, option=None, default=None, question=None, proof=None, spec=None):
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
        self.proof_input(proof, spec);toclear+=1

def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()

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

def print_dict(dict, indent=6):
    print(json.dumps(dict, indent=indent))

def getFromDict(dataDict, mapList):
    for k in mapList: dataDict = dataDict[k]
    return dataDict

def setInDict(dataDict, maplist, value, keylist=None):
    if keylist:
        maplist=maplist+keylist
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

def add_setting(setting_list,key_list,value):
    global project
    d = project.conditionDict
    print('setting:'+str(setting_list))
    for part in setting_list:
        part = part + key_list
        print('part: '+str(part))
        for path in part:
            d = d[path]
        d = value
    print_dict(project.conditionDict)

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
    global project
    text=json.dumps(cdict, indent=indent)
    d = depth(cdict)
    out=""
    path=[]
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
                project.settingsList.append([])
        elif level<i and '{}' in line:
            counter +=1
            project.settingsList.append([])
        if '{}' in line:
            if ',' in line:
                out+= f"{line}{' '*(14-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}\n"
            else:
                out+= f"{line}{' '*(15-len(key) + indent*(d-2)-indent*level)} <-{' '*((counter+1)%2)*2}  {counter}\n"
            project.settingsList[-1].append(path)
        else:
            out+=line+'\n'
    return out

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
                        option=f"enter ID's on condition level comma separated \n\nor copy {copy} with 'cp'"
                    else:
                        out+=f"{line}    <-\n"
                        option="enter ID's on conditions comma separated "
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



##########################
# conversation functions #
##########################

conversation_dict={
    "0":"expand the existing project",
    "1":"create a new project",
    "2":"set project-folder (name and path)",
    "3":"set conditions",
    "4":"set samples",
    "5":"set workflows",
    "6":"set settings of specific workflows",
    "7":"set number of cores",
    "8":"print config file"
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
    if step == '0':
        start()
    if step == '1':
        start()
    if step == '2':
        create_project()
    if step == '3':
        create_experiment()
    if step == '4':
        add_samples()
    if step == '5':
        select_workflows()
    if step == '6':
        set_workflows()
    if step == '7':
        set_cores()
    if step == '8':
        end()

def start():
    operator.title("INTRO")
    operator.display(
    text=get_doc("intro"),
    option="Enter 'expand' for expanding an existing configfile or 'new' for a new project",
    default=None,
    question="enter 'new' or 'expand'",
    proof=['new','expand']
    )
    if operator.get_answer() == 'new':
        return create_project()
    if operator.get_answer() == 'expand':
        return expand()

def project_error():
    global project
    operator.title("ERROR")
    operator.display(
    text=f"In the directory you entered, a folder with the name '{project.name}' already exist. \nSo please say again: do you want to create a new project or expand an existing?",
    option="Enter 'expand' for expanding an existing configfile or 'new' for a new project",
    question="enter 'new' or 'expand'",
    proof=['new','expand']
    )
    if operator.get_answer() == 'new':
        return create_project()
    if operator.get_answer() == 'expand':
        return expand()

def folder_error():
    operator.title("ERROR")
    operator.display(
    text="It looks like you already set up your project-folder. \mWe would therefor skip setting it up now. \n\nEnter 'n' if you want to do that anyway.",
    option="wanna skip the Guide?",
    question="[ n / Y ]"
    )
    if operator.get_answer() == 'n':
        return project.name()
    if operator.get_answer() == 'y':
        return end()

def create_project():
    global project
    operator.title("CREATE PROJECT-FOLDER")
    switch=False
    while True:
        if switch:
            ques="Enter the absolute path, where your project should be created\nsorry, couldn't find this directory"
        else:
            ques="Enter the absolute path, where your project-folder should be created  "
        operator.display(
        text=get_doc("projectfolder"),
        option=ques,
        question="enter it like  /path/to/MyNewProject",
        default=None,
        proof=None
        )
        project.name = os.path.basename(operator.get_answer())
        project.path = operator.get_answer()
        if os.path.isdir(project.path):
            return project_error()
        if os.path.isdir(os.path.dirname(project.path)):
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
    global project
    create_condition_dict(project.conditionDict,[project.name])
    project.settingsDict = json.loads(json.dumps(project.conditionDict))
    return add_samples()

def add_samples():
    global project
    switch=False
    path_to_samples= []
    operator.title("ADD SAMPLES")
    while True:
        if switch:
            ques=f"Sorry, couldn't find {path_to_samples}\n\nEnter an absolute path where samples are stored"
        else:
            ques="Enter an absolute path \n\nor press enter to continue"
        operator.display(
        text=get_doc("samples"),
        option=ques,
        default=None,
        question="enter like  /home/path/to/Samples",
        proof=None
        )
        if operator.get_answer() == '' and path_to_samples :
            break
        switch=True
        if os.path.isdir(operator.get_answer()):
            path_to_samples.append(operator.get_answer())
            switch = False
    counter=1
    for p in path_to_samples:
        for dirpath, dirnames, filenames in os.walk(p):
            for filename in [f for f in filenames if f.endswith(".fastq.gz")]:
                project.sampleDict[str(counter)]=[filename, os.path.join(p,filename)]
                counter+=1
    return assign_samples()

def assign_samples():
    global project
    global toclear
    conditions=[pattern for pattern in project.conditionDict.get_condition_list()]
    for condition in conditions:
        samples_lines=''
        for k,v in project.sampleDict.items():
            samples_lines+=f"{' '*3}>  {k}  -  {v[0].replace('.fastq.gz','')}\n"
        cond_as_list=[x for x in condition.split(':')]
        operator.display(
        text=location(project.conditionDict,[cond_as_list]),
        option=f"enter all sample-numbers according to the displayed condition:\n\n{samples_lines}",
        default=None,
        question="enter comma separated",
        proof='only_numbers'
        )
        for s in project.sampleDict.keys():
            if s in operator.get_answer():
                project.sampleDict[s].append(condition)
    return select_workflows()

def select_workflows():
    global project
    possible_workflows = list(project.configDict.keys())
    for e in ["WORKFLOWS","BINS","MAXTHREADS","SETTINGS"]:
        possible_workflows.remove(e)
    operator.title("SELECT WORKFLOWS")
    operator.display(
    text=get_doc("workflows")+'\n'+'\n'.join(possible_workflows),
    option="Enter which WORKFLOWS you would like to run",
    default=None,
    question="Enter comma separated",
    proof=possible_workflows
    )
    for work in operator.get_answer().split(','):
        project.workflowsDict[work]
    return set_settings()

def select_setting_level():
    global project
    while True:
        d=depth(project.conditionDict)
        for i in range(d-1):
            project.settingsList = []
            operator.display(
            text= select_id_to_set(project.conditionDict,i),
            option="enter to loop through the possible condition-settings\nyou will set all conditions with the same number at once afterwards \n\nenter 'select' for your setting",
            default=None,
            question="",
            proof=["select",""]
            )
            if operator.get_answer() =='select':
                return

def set_settings():
    operator.title("MAKE GENERAL SETTINGS")
    operator.display(
    text=get_doc("settings"),
    option='enter to continue',
    )
    return set_settings2()

def set_settings2():
    global project
    select_setting_level()
    counter=1
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
        counter+=1
    return set_workflows()

def select_tools(workflow):
    operator.title("SELECT TOOLS")
    operator.display(
    text=get_doc("postprocessing"),
    question="enter to continue"
    )
    return select_tools2(workflow)

def select_tools2(workflow):
    global project
    operator.display(
    text=json.dumps(project.conditionDict,indent=6),
    option='Select from these available Tools:',
    default='\n'.join(project.configDict[workflow]['TOOLS'].keys()),
    question="enter comma separated",
    proof=project.configDict[workflow]['TOOLS'].keys()
    )
    for tool in operator.get_answer().split(','):
        project.workflowsDict[workflow]['TOOLS'][tool] = project.configDict[workflow]["TOOLS"][tool]


def create_comparables(workflow):
    operator.display(
    text=get_doc("comparables"),
    option='enter to continue',
    )
    return create_comparables2(workflow)

def create_comparables2(workflow):
    global project
    while True:
        operator.display(
        text=json.dumps(project.conditionDict,indent=6),
        option="enter the name of a comparison group\n\nor enter to continue",
        default=None,
        question="please do not use special characters",
        proof=None
        )
        if operator.get_answer() == '':
            break
        comp_name=operator.get_answer()
        project.workflowsDict[workflow]['COMPARABLE'][comp_name]=[[],[]]
        for i in [0,1]:
            operator.display(
            text=json.dumps(project.conditionDict,indent=6),
            option=f'select all keys for comparison group {i+1}',
            default='\n'.join(project.conditionDict.get_nodes()),
            question="enter comma separated",
            proof=[x for x in project.conditionDict.get_nodes()]
            )
            project.workflowsDict[workflow]['COMPARABLE'][comp_name][i]=operator.get_answer()

def set_workflows():
    global options_dict
    global project
    WORKFLOWS = project.workflowsDict.keys()
    # project.settingsList=select_id_to_set(project.conditionDict)
    for workflow in WORKFLOWS:
        k = list(project.conditionDict.keys())[0]
        project.workflowsDict[workflow][k] = json.loads(json.dumps(project.conditionDict[k]))
        operator.title(f"Make Settings for {workflow}")
        if 'TOOLS' in project.configDict[workflow].keys():
            select_tools(workflow)

        for setting in project.settingsList:
            for tool in project.workflowsDict[workflow]['TOOLS'].keys():
                for maplist in setting:
                    setInDict(project.workflowsDict,[workflow]+maplist+[tool,"OPTIONS"],[])
                for i in range(len(project.configDict[workflow][tool]['OPTIONS'])):
                    call =  optionsDictToString(project.configDict[workflow][tool]['OPTIONS'][i])
                    operator.display(
                    text=location(project.conditionDict,setting),
                    option=options_dict[workflow]['OPTIONS'][i] +"\n\n!! please separate flag value pairs with comma !!",
                    question="edit or confirm with enter",
                    spec= call
                    )
                    optsDict = stringToOptionsDict(operator.get_answer())
                    setInDict(project.workflowsDict,[workflow]+maplist+[tool,"OPTIONS"],optsDict)
        if 'COMPARABLE' in project.configDict[workflow].keys():
            create_comparables(workflow)
    return set_cores()

def set_cores():
    global projects
    operator.title("NUMBER OF CORES")
    operator.display(
    text=get_doc('processes'),
    option="set number of cores",
    default=None,
    question="enter number",
    proof='only_numbers'
    )
    project.cores = str(operator.get_answer())
    return end()

def end():
    global project
    global configfile

    # print(project.path)
    # print_dict(project.conditionDict)
    # print_dict(project.workflowsDict)
    # print_dict(project.settingsDict)
    # print_dict(project.sampleDict)
    # print(str(project.settingsList))
    # input()

    final_dict = NestedDefaultDict()
    # create Project Folder
    os.mkdir(project.path)
    fastq = os.path.join(project.path,"FASTQ")
    gen = os.path.join(project.path,"GENOMES")
    os.mkdir(fastq)
    os.mkdir(gen)
    os.symlink(cwd, os.path.join(project.path,'nextsnakes'))

    # LINK samples into FASTQ and insert samplenames in dict
    for k,v in project.sampleDict.items():
        if len(v) == 3:
            samplename = v[0]
            origin = v[1]
            condition = v[2]
            cond_as_list=[x for x in condition.split(':')]
            os.chdir(fastq)

            for dir in cond_as_list:
                if not os.path.exists(os.path.join(dir)):
                    os.mkdir(os.path.join(dir))
                os.chdir(os.path.join(dir))
            path='/'.join(cond_as_list)
            cond_dir=os.path.join(fastq,path)
            os.symlink(origin, os.path.join(cond_dir,samplename))
            setInDict(project.settingsDict,cond_as_list+["SAMPLES"],samplename)

    # link reference and annotation and insert in dict
    for setting in project.settingsList:
        for condition in setting:

            ref = getFromDict(project.settingsDict,condition + ['REFERENCE'])
            if os.path.isfile(ref):
                if not os.path.exists(os.path.join(gen,os.path.basename(ref))):
                    os.symlink(ref, os.path.join(gen,os.path.basename(ref)))
                f = os.path.join(gen,os.path.basename(ref))
                rel = os.path.os.path.relpath(f, start=project.path)
                setInDict(project.settingsDict,condition+ ['REFERENCE'],rel)
            else:
                print("reference path is not correct, could not symlink, please do by hand")
                setInDict(project.settingsDict,condition+ ['REFERENCE'],"EMPTY")

            gtf = getFromDict(project.settingsDict,condition + ['ANNOTATION','GTF'])
            if os.path.isfile(gtf):
                if not os.path.exists(os.path.join(gen,os.path.basename(gtf))):
                    os.symlink(ref, os.path.join(gen,os.path.basename(gtf)))
                f = os.path.join(gen,os.path.basename(gtf))
                rel = os.path.os.path.relpath(f, start=project.path)
                setInDict(project.settingsDict,condition+['ANNOTATION','GTF'],rel)
            else:
                print("GTF path is not correct, could not symlink, please do by hand")
                setInDict(project.settingsDict,condition+['ANNOTATION','GTF'],"EMPTY")

            gff = getFromDict(project.settingsDict,condition + ['ANNOTATION','GFF'])
            if os.path.isfile(gff):
                if not os.path.exists(os.path.join(gen,os.path.basename(gff))):
                    os.symlink(ref, os.path.join(gen,os.path.basename(gff)))
                f = os.path.join(gen,os.path.basename(gff))
                rel = os.path.os.path.relpath(f, start=project.path)
                setInDict(project.settingsDict,condition+['ANNOTATION','GFF'], rel)
            else:
                print("GFF path is not correct, could not symlink, please do by hand")
                setInDict(project.settingsDict,condition+['ANNOTATION','GFF'], "EMPTY")


    final_dict["WORKFLOWS"] = ','.join(project.workflowsDict.keys())
    final_dict["BINS"] = project.configDict["BINS"]
    final_dict["MAXTHREADS"] = project.cores
    final_dict["SETTINGS"] = project.settingsDict
    final_dict.update(project.workflowsDict)

    print_dict(final_dict)
    print(20*'\n')

    os.chdir(cwd)
    operator.title(f"{'*'*10}")
    configfile = f"config_{project.name}.json"
    operator.display(
    text=get_doc('runsnakemake'),
    option=f"You created \n\n    > {configfile}\n\nstart RunSnakemake with:\n\n    > python3 nextsnakes/RunSnakemake.py -c {configfile} --directory ${{PWD}}",
    question='press enter to quit the Guide'
    )
    return finalize_project(final_dict)

def finalize_project(final_dict):
    with open(os.path.join(project.path,f"config_{project.name}.json"),'w') as jsonout:
        print(json.dumps(final_dict,indent=4),file=jsonout)

#####################
# global variables: #
#####################

options_dict=NestedDefaultDict()
options_dict['TYPES'] = 'set types'
options_dict['BATCHES'] = 'set batches'
options_dict['GROUPS'] = 'set groups'
options_dict['SEQUENCING'] = 'set seq'
options_dict['REFERENCE'] = 'set the path to the Reference'
options_dict['INDEX'] = 'set index'
options_dict['PREFIX'] = "set prefix"
options_dict['ANNOTATION']['GTF'] = "set path to GTF"
options_dict['ANNOTATION']['GFF'] = "set path to GFF"
options_dict['COUNTING']['FEATURES'] = "set feature setting"
options_dict['COUNTING']['OPTIONS'][0] = "set feature setting"
options_dict['TRIMMING']['OPTIONS'][0] = "trimming options"
options_dict['UCSC']['OPTIONS'][0] = "ucsc options"
options_dict['PEAKS']['OPTIONS'][0] = "peaks options"
options_dict['MAPPING']['OPTIONS'][0] = "set indexing options"
options_dict['MAPPING']['OPTIONS'][1] = "set mapping options"
options_dict['MAPPING']['OPTIONS'][2] = "set name extension for index"
options_dict['DTU']['OPTIONS'][0] = "set Salmon index options"
options_dict['DTU']['OPTIONS'][1] = "set Salmon quant options"
options_dict['DAS']['OPTIONS'][0] = "set counting options "
options_dict['DAS']['OPTIONS'][1] = "set diego options"
options_dict['DEU']['OPTIONS'][0] = "set counting options  for featureCounts"
options_dict['DEU']['OPTIONS'][1] = "set x options"
options_dict['DE']['OPTIONS'][0] = "set counting options for featureCounts"
options_dict['DE']['OPTIONS'][1] = "set x options"
options_dict['SEQUENCING'] = "paired or single?"
options_dict['GENOME'] = "which organism?"

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cwd=os.getcwd()
toclear=0
operator = OPERATOR()
project = PROJECT()
project.configDict = load_configfile("configs/template_base.json")
project.gitLink = "git@github.com:jfallmann/NextSnakes.git"

########
# main #
########
def main():
    global project

    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: menu-complete")
    readline.set_completer(complete)

    header='  _  _                     _       ___                     _\n'\
    ' | \| |    ___    __ __   | |_    / __|   _ _     __ _    | |__    ___     ___\n'\
    ' | .` |   / -_)   \ \ /   |  _|   \__ \  | ` \   / _` |   | / /   / -_)   (_-<\n'\
    ' |_|\_|   \___|   /_\_\    \__|   |___/  |_||_|  \__,_|   |_\_\   \___|   /__/ \n'

    print("\n\n")
    for line in header.split('\n'):
        print(f"{' '*10}{line}")

    start()

if __name__ == '__main__':
    main()
