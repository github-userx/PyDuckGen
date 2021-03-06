# *
# *
# * Generates Rubber Ducky Payloads with a metasploit like interface
# *
# *

from colorama import init, Fore, Back, Style
from tabulate import tabulate
import json, os, output, subprocess, shutil, time, sys
from AutoCompleter import AutoCompleter

autocomplete = True

try:
  import readline
  if os.name == 'nt':
      autocomplete = False
except ImportError:
  import pyreadline as readline
  if os.name == 'nt':
      autocomplete = False

modules = []
loadedModule = []
moduleAttributes = []

def main():
    "Initialize system, search for modules and encoder"
    init(autoreset=True) # Colorama init
    javaCheck()
    output.cls()
    output.banner()
    loadModules()
    startShell()

def main_quick():
    "Fast payload generation using command line arguments"
    init(autoreset=True)
    javaCheck()
    output.cls()
    output.banner()
    loadModules()
    #
    #   format: ./PyDuck.py <module> <duck_drive> [list of attributes in format]
    #   format of attributes: attribute=value
    #
    global loadedModule
    global moduleAttributes
    modulename = sys.argv[1]
    if modulename in modules:
        if os.path.isfile('modules/' + modulename + '/module.json'):
            with open('modules/' + modulename + '/module.json', 'r') as module:
                module_content = module.read().replace('\n', '')
            loadedModule = json.loads(module_content)

            moduleAttributes = loadedModule['attributes']
            # add default attributes: lang,drive
            moduleAttributes['language'] = 'us'
            moduleAttributes['sdcard_mount'] = sys.argv[2]
            attr_args = []
            if len(sys.argv) > 3:
                for i in range(3, len(sys.argv)):
                    attr_args.append(sys.argv[i])
            # check for uac bypass and add attribute
            if loadedModule['requirements']['has_uac_bypass'].lower() == "true":
                moduleAttributes['uac_bypass_key'] = 'y'


            for a in attr_args:
                sep = a.split('=')
                if sep[0] in moduleAttributes:
                    output.success("Setting " + sep[0] + " to " + sep[1])
                    moduleAttributes[sep[0]] = sep[1]
                else:
                    output.error("Attribute " + sep[0] + " not found..exiting")
                    sys.exit(1)

            cmdUseGenerate(modulename)

        else:
            output.error("Module '" + modulename + "' does not exist")
    else:
        output.error("Module '" + modulename + "' does not exist")

def javaCheck():
    ret = os.system("java -version")
    if ret > 0:
        output.error("Java not installed or Java not in PATH Variable")
        sys.exit(1)


def loadModules():
    output.info("Loading Modules...")
    global modules
    for name in os.listdir('modules'):
        if os.path.isdir(os.path.join('modules', name)) and os.path.isfile(os.path.join('modules', name) + '/module.json'):
            modules.append(name)
    output.success("Found " + str(len(modules)) + " Modules")


def startShell():
    #build possible inputs:
    possibleInputs = [
        'modules',
        'cls',
        'clear',
        'quit',
        'exit',
        'help'
    ]
    for m in modules:
        possibleInputs.append(m)

    if autocomplete is True:
        completer = AutoCompleter(list(set(possibleInputs)), "\n" + Fore.LIGHTCYAN_EX + "pyd> " + Style.RESET_ALL)
        readline.set_completer_delims(' \t\n;')
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        readline.set_completion_display_matches_hook(completer.display_matches)
    cmd = input("\n" + Fore.LIGHTCYAN_EX + "pyd> " + Style.RESET_ALL)
    handleCommand(cmd)


def handleCommand(cmd):
    global loadedModule
    #output.info cmd
    if cmd[:4] == "info":
        cmdinfo(cmd)
    #list modules
    elif cmd[:7] == "modules" and len(cmd) == 7:
        cmdList()
    elif (cmd[:4] == "exit" or cmd[:4] == "quit") and len(cmd) == 4:
        output.success('KTHXBYE')
        sys.exit()
    elif cmd[:4] == "help" and len(cmd) == 4:
        cmdHelp(False)
    elif cmd[:3] == "cls" and len(cmd) == 3:
        output.cls()
    elif cmd[:5] == "clear" and len(cmd) == 5:
        output.cls()
    else:
        if cmd in modules:
            cmdUse(cmd)
        else:
            output.error('Unknown Command => ' + cmd)

    startShell()

def cmdinfo(cmd):
    modulename = cmd
    module_content = ''
    if os.path.isfile('modules/' + modulename + '/module.json'):
        with open('modules/' + modulename + '/module.json', 'r') as module:
            module_content = module.read().replace('\n','')
        loadedModule = json.loads(module_content)
        print('\n=> Module Info\n--------------------------------------')
        name = ['Name',loadedModule['title']]
        desc = ['Description', loadedModule['description']]
        firmware = ['Firmware', loadedModule['requirements']['firmware']]
        uacbypass = ['Bypass UAC', loadedModule['requirements']['has_uac_bypass']]
        print(tabulate([name, desc, firmware, uacbypass], headers=['Attribute', 'Value']))
    else:
        output.error("Module '" + modulename + "' does not exist")

def cmdList():
    global modules
    print('\n > Loaded Modules\n--------------------------------------')
    for module in modules:
        output.success(module)

def cmdHelp(showPayLoadhelp):
    clscmd = ['cls/clear', 'Clears the screen']

    if not showPayLoadhelp:
        print('\n=> Main Menu Command List\n--------------------------------------')
        listcmd = ['modules', 'Lists all available payloads in the modules folder']
        usecmd = ['<payload>', 'Loads the payload for further operation']
        exitcmd = ['quit/exit', 'Exits the program']
        print(tabulate([listcmd, usecmd, clscmd, exitcmd], headers=['Command', 'output.info']))

    else:
    #------------------------------------------------------------------------------------------------------------#
        print('\n\n=> Payload specific Command List\n--------------------------------------')
        gencmd = ['generate/gen', 'Generates the inject.bin and copies it to your rubber ducky']
        setcmd = ['set <attribute> <value>', 'Sets the given attribute to the given value']
        attributescmd = ['attributes', 'Returns a list of attributes to set']
        infocmd = ['info', 'Gives you information about the payload']
        exit2cmd = ['quit/exit', 'Returns to payload selection']
        print(tabulate([infocmd, gencmd, setcmd, attributescmd, clscmd, exit2cmd], headers=['Command', 'output.info']))

def cmdUse(cmd):
    global loadedModule
    global moduleAttributes
    modulename = cmd
    module_content = ''
    if os.path.isfile('modules/' + modulename + '/module.json'):
        with open('modules/' + modulename + '/module.json', 'r') as module:
            module_content = module.read().replace('\n','')
        loadedModule = json.loads(module_content)
        moduleAttributes = loadedModule['attributes']
        #add default attributes: lang,drive
        moduleAttributes['language'] = 'us'
        if os.name=='nt':
            moduleAttributes['sdcard_mount'] = 'H:\\'
        else:
            moduleAttributes['sdcard_mount'] = '/mnt/ducky/'
        #check for uac bypass and add attribute
        if loadedModule['requirements']['has_uac_bypass'].lower() == "true":
            moduleAttributes['uac_bypass_key'] = 'y'

        cmdUseShell(modulename)
    else:
        output.error("Module '" + modulename + "' does not exist")

def cmdUseShell(modulename):
    possibleInputs = [
        'info',
        'generate',
        'gen',
        'attributes',
        'exit',
        'quit',
        'set <attribute> <value>',
        'help'
    ]

    if autocomplete is True:
        completer = AutoCompleter(list(set(possibleInputs)), "\n" + Fore.LIGHTCYAN_EX + "pyd> " + Style.RESET_ALL + "(" + Fore.LIGHTRED_EX + modulename + Style.RESET_ALL +"): ")
        readline.set_completer_delims(' \t\n;')
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        readline.set_completion_display_matches_hook(completer.display_matches)
    cmdPay = input("\n" + Fore.LIGHTCYAN_EX + "pyd> " + Style.RESET_ALL + "(" + Fore.LIGHTRED_EX + modulename + Style.RESET_ALL +"): ")
    handleUseCmd(cmdPay, modulename)

def handleUseCmd(cmd, modulename):
    if cmd[:3] == "set" and len(cmd) > 3:
        cmdUseSet(cmd)
        cmdUseShell(modulename)
    elif (cmd[:4] == "exit" or cmd[:4] == "quit") and len(cmd) == 4:
        global moduleAttributes
        moduleAttributes = []
    elif cmd[:4] == "info" and len(cmd) == 4:
        cmdinfo(modulename)
        cmdUseShell(modulename)
    elif cmd[:10] == "attributes" and len(cmd) == 10:
        cmdUseAttributes()
        cmdUseShell(modulename)
    elif (cmd[:3] =="gen" and len(cmd) == 3) or (cmd[:8] == "generate" and len(cmd) == 8):
        print("This will delete and recreate the needed folders/files and replace inject.bin")
        sure = input("Are you sure? (y/n): ")
        if sure.lower() == 'y':
            cmdUseGenerate(modulename)
        else:
            cmdUseShell(modulename)
    elif cmd[:4] == "help" and len(cmd) == 4:
        cmdHelp(True)
        cmdUseShell(modulename)
    elif cmd[:3] == "cls" and len(cmd) == 3:
        output.cls()
        cmdUseShell(modulename)
    elif cmd[:5] == "clear" and len(cmd) == 5:
        output.cls()
        cmdUseShell(modulename)
    else:
        output.error('Unknown Command => ' + cmd)
        cmdUseShell(modulename)

def cmdUseSet(cmd):
    params = cmd.split(" ")
    if  len(params) < 3:
        output.error('Command Syntax => set <attribute> <value>')
    else:
        global moduleAttributes
        if params[1] in moduleAttributes:
            joined = params[2]
            if len(params) > 3:
                #add other after a space eg set text Hello World
                # so we add the World at the end
                for p in range(3, len(params)):
                    joined += " " + params[p]

            moduleAttributes[params[1]] = joined
            output.success(params[1] + '=>' + joined)
        else:
            output.error("Attribute '" + params[1] + "' is unknown" )

def cmdUseAttributes():
    attributes = []
    for key, value in moduleAttributes.items():
        attributes.append([key,value])
    print(tabulate(attributes, headers=['Attribute', 'Value']))





def cmdUseGenerate(modulename):
    #read the duckyscript and replace the uac key if needed
    global moduleAttributes
    ducky = moduleAttributes['sdcard_mount']
    suffix = "/"
    if os.name == 'nt':
        suffix = "\\"
    if not ducky.endswith(suffix, len(ducky)-1, len(ducky)):
        if os.name == 'nt':
            ducky = ducky + "\\"
        else:
            ducky = ducky + "/"

    lang = moduleAttributes['language']
    moduleAttributes.pop('sdcard_mount', None)
    moduleAttributes.pop('language', None)


    output.info("Reading duckyscript.txt")
    tmpduckyscript = ''
    with open('modules/' + modulename + '/duckyscript.txt', 'r') as script:
        if loadedModule['requirements']['has_uac_bypass'].lower() == "true":
            #now replace the uac key
            output.info("Replacing <uac_bypass_key>")
            tmpduckyscript = script.read().replace('<uac_bypass_key>', moduleAttributes['uac_bypass_key'])
            output.success("Replacing <uac_bypass_key> key... Done!")
            #pop uac_bypass_key
            moduleAttributes.pop('uac_bypass_key', None)
        else:
            output.info("No UAC Bypass needed")
            tmpduckyscript = script.read()

        for key, value in moduleAttributes.items():
            output.info("Replacing <" + key + "> with " + value)
            tmpduckyscript = tmpduckyscript.replace('<' + key + '>', value)

    output.info("Writing temporary duckyscript...")
    with open('tmp.duckyscript', 'w') as w:
        w.write(tmpduckyscript)
    output.success("Writing temporary duckyscript...Done!")

    output.info("Generating inject.bin...")
    # Generate the inject.bin
    encoderPath = "encoder/encoder.jar"
    inputFlag = "-i tmp.duckyscript"
    outputFlag = "-o inject.bin"
    langFlag = "-l " + lang
    fullExecCommand = "java -jar " + encoderPath + " " + inputFlag + " " + outputFlag + " " + langFlag
    result = subprocess.check_output(fullExecCommand, stderr=subprocess.STDOUT, shell=True)
    result = result.decode("utf-8")
    print(result)
    output.success("Generating inject.bin...Done!")

    os.remove("tmp.duckyscript")

    if "folders" in loadedModule['requirements']:
        output.info("Creating the necessary folders...")

        for folder in loadedModule['requirements']['folders']:
            if os.path.exists(ducky + folder):
                shutil.rmtree(ducky + folder)
                time.sleep(2)
            os.makedirs(ducky + folder)
        output.success("Creating the necessary folders...Done!")
    else:
        output.info("No folder creation needed")

    if "files" in loadedModule['requirements']:
        output.info("Copying files...")
        for ffile in loadedModule['requirements']['files']:
            if os.path.isfile(ducky + ffile):
                os.remove(ducky + ffile)
                time.sleep(2)
            shutil.copyfile('modules/' + modulename + '/' + ffile, ducky + ffile)
        output.success("Copying files...Done!")
    else:
        output.info("No file copying needed")

    output.info("Copying inject.bin to Ducky...")
    shutil.copyfile('inject.bin', ducky + "inject.bin")
    time.sleep(2)
    os.remove("inject.bin")
    output.success("Copying inject.bin to Ducky...Done!")

    print('')
    output.success("Thanks 4 shopping with PyDuckGen")
    sys.exit()

#Main entry point
if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) >= 3:
        main_quick()
    else:
        print('usage: python PyDuck.py [ <module> <ducky_mount> [list of module attributes in format: attr=value] ]')
