import re
import maya.cmds as mc
import maya.mel as mel


def get_optionvar(var, type='iv'):
    pref_file = mc.internalVar(userPrefDir=1)+'userPrefs.mel'
    values = []
    with open(pref_file) as f:
        for line in f.readlines():
            match = re.search(
                '(?<=\s-{type}\s"{var}"\s)(?P<value>.*)'.format(type=type, var=var), line)
            if match:
                value = match.group('value').strip('"')
                values.append(value)

    if len(values) == 1:
        values = values[0]
    return values

# get_optionvar('ScriptEditorExecuterLabelArray','sva')
# get_optionvar('ScriptEditorExecuterTabIndex','iv')

def save_tabs():
    cmd = '''
    syncExecuterBackupFiles();

    syncExecuterTabState();

    savePrefs -general;
    '''
    mel.eval(cmd)


def load_tabs():
    cmd = '''
    global string $gCommandExecuterName[];
    global string $gCommandExecuterType[];

    global string $gLastFocusedCommandExecuter;
    global string $gLastFocusedCommandControl;

    global string $gCommandExecuterTabs;

    deleteUI `tabLayout -q -ca $gCommandExecuterTabs`;

    $gCommandExecuterName=python("get_optionvar('ScriptEditorExecuterLabelArray','sva')");


    $gCommandExecuterType=python("get_optionvar('ScriptEditorExecuterTypeArray','sva')");

    int $len = size($gCommandExecuterName);
    int $i;
    for ($i = 0; $i < $len; ++$i) {
        buildNewExecuterTab($i, $gCommandExecuterName[$i], $gCommandExecuterType[$i], 0);                       
    }

    int $prevIdx = python("get_optionvar('ScriptEditorExecuterTabIndex','iv')");
    tabLayout -e -selectTabIndex $prevIdx $gCommandExecuterTabs;

    '''
    mel.eval(cmd)
