import re
import maya.cmds as mc
import maya.mel as mel


def get_optionvar(var, type='iv'):
    pref_file = mc.internalVar(userPrefDir=1)+'userPrefs.mel'
    values = []
    with open(pref_file) as f:
        for line in f.readlines():
            match = re.search(
                '(?<=\s-{type}\s"{var}"\s)(?P<value>[^;\n]*)'.format(type=type, var=var), line)
            if match:
                value = match.group('value').strip('"')
                values.append(value)

    if len(values) == 1:
        values = values[0]
    return values


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

    global string $gCommandExecuterTabs;

    deleteUI `tabLayout -q -ca $gCommandExecuterTabs`;

    python("from syncScriptEditor import get_optionvar");
    $gCommandExecuterName=python("get_optionvar('ScriptEditorExecuterLabelArray','sva')");

    $gCommandExecuterType=python("get_optionvar('ScriptEditorExecuterTypeArray','sva')");
    
    {
    int $len = size($gCommandExecuterName);
    int $i;
    for ($i = 0; $i < $len; ++$i) {
        buildNewExecuterTab($i, $gCommandExecuterName[$i], $gCommandExecuterType[$i], 0);                       
    }

    int $prevIdx = python("get_optionvar('ScriptEditorExecuterTabIndex','iv')");
    tabLayout -e -selectTabIndex $prevIdx $gCommandExecuterTabs;
    }

    '''
    mel.eval(cmd)


def add_script_editor_toolbar():
    # this is the last contorl on script editor tool bar
    goto_btn = mc.iconTextButton(
        'scriptEditorToolbarGotoLineButton', q=1, fullPathName=1)
    flow_layout = re.search('.*(?=\|)', goto_btn).group()

    for x in reversed(mc.layout(flow_layout, q=1, ca=1)):
        if x == 'scriptEditorToolbarGotoLineButton':
            break
        else:
            mc.deleteUI(x)

    mc.setParent(flow_layout)

    iconSize = 23
    mc.separator(height=iconSize, horizontal=0, style='single')

    mc.iconTextButton(
        width=iconSize, height=iconSize,
        annotation='save tabs',
        image="save.png",
        c=lambda *x: save_tabs()
    )

    mc.iconTextButton(
        width=iconSize, height=iconSize,
        annotation='load tabs',
        image="refresh.png",
        c=lambda *x: load_tabs()
    )
