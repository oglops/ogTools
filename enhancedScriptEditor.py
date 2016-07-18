# author: oglops@gmail.com The Tree Widget guy

# todo
# ctrl+d remove multiple line
# double click go to line
# ctrl+g go to line
# ctrl+r sublime style 

try:
    qApp.removeEventFilter(filter)
    print 'removed filter'
except:
    print 'first run'

from PyQt4 import QtCore,QtGui

from PyQt4.QtCore import Qt,QObject,QEvent,QChar
from PyQt4.QtGui import QTextCursor,qApp

import maya.cmds as mc
import maya.mel as mel

import maya.OpenMayaUI as apiUI
import sip

import sys
import logging
_logger = logging.getLogger('hackScriptEditor')

for handler in _logger.handlers:
    _logger.removeHandler(handler)

# _logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
ch.setFormatter(formatter)
_logger.addHandler(ch)
_logger.propagate=0

class CustomFilter(QObject):
    
    def __init__(self,parent=None):
        super(CustomFilter,self).__init__(parent)
        self.textedit=None

    def get_exec_type(self):
        gCommandExecuterTabs= get_mel_global('$gCommandExecuterTabs')
        tabIdx = mc.tabLayout(gCommandExecuterTabs, q=1, st=1)
        cmd_executer = mc.layout(tabIdx,q=1,ca=1)[0]
        return mc.cmdScrollFieldExecuter(cmd_executer,q=1,st=1)

    
    def eventFilter(self,  obj,  event):
        if event.type() == QEvent.KeyPress:
            if 'scriptEditorPanel' in mc.getPanel(up=1):
                self.get_text_edit()

                self.exec_type = self.get_exec_type()
                if self.exec_type=='python':
                    self.comment_str='#'
                elif self.exec_type=='mel':
                    self.comment_str='//'

                # print event.key(),event.modifiers()
                if event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:
                    _logger.debug('ctrl+/ pressed')
                    self.toggle_comment()
                    return True
                elif event.key() == Qt.Key_Tab and event.modifiers() == Qt.NoModifier:
                    _logger.debug('tab pressed')
                    self.tab('tab')
                    return True
                elif event.key() == Qt.Key_Backtab and event.modifiers() == Qt.ShiftModifier:
                    _logger.debug('shift+tab pressed')
                    self.tab('shift_tab')
                    return True  
                elif event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
                    _logger.debug('ctrl+d pressed')
                    self.test('delete_line')
                    return True                  
                elif event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
                    _logger.debug('ctrl+e pressed')
                    self.test('execute')
                    return True   
                    
                elif event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
                    _logger.debug('ctrl+z pressed')
                    self.test('undo')
                    return True              

                elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
                    _logger.debug('ctrl+r pressed')
                    # self.test('goto_symbol')
                    return True         
        return False
        
    def get_text_edit(self):
        'get current qtextedit from script editor'
        tabIdx = mc.tabLayout(gCommandExecuterTabs, q=1, st=1)
        _logger.debug('current tab: %s', tabIdx)
        cmd_executer = mc.layout(tabIdx,q=1,ca=1)[0]
        ptr=apiUI.MQtUtil.findControl(cmd_executer)
        
        self.textedit=sip.wrapinstance(long(ptr),QObject)
        
    def moveToPosition(self, pos):
        'move cursor actual position to pos'
        cursor = self.textedit.textCursor()
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, pos)
        self.textedit.setTextCursor(cursor)



    def restore_selection(fn):

        from functools import wraps
        @wraps(fn)
        def wrapper(self,*args, **kw):
           
            _logger.debug('before')
            self.test('get_range')

            fn(self,*args, **kw)

            _logger.debug('after')
            self.test('load_range')

        return wrapper


    @restore_selection
    def toggle_comment(self,*args):
        self.last_change='toggle_comment'
        self.test('multi_line_comment')


    @restore_selection
    def tab(self,mode='tab',*args):
        self.test(mode)

    def position_in_block(self,cursor):
        # this can be replaced with cursor.positionInBlock after qt 4.7
        pos = cursor.position()-cursor.block().position()
        return pos


    def get_line_range(self,cursor,start_pos,end_pos):

        # find left most line
        cursor.setPosition(end_pos)
        last_line = cursor.block().blockNumber()
        if cursor.atBlockStart() and start_pos != end_pos:
            _logger.debug('start_pos: %s end_pos: %s',start_pos,end_pos)
            last_line -= 1

        cursor.setPosition(start_pos)
        first_line = cursor.block().blockNumber()  
        
        return (first_line,last_line)    

    def get_min_indent(self,cursor,start_pos,first_line,last_line):
        # find the leftmost line and get its position
        cursor.setPosition(start_pos)
        indents = []
        for _line_nb in range(first_line, last_line+1):

            text = str(cursor.block().text())
            indent = len(text)-len(text.lstrip())
            indents.append(indent)
            cursor.movePosition(QTextCursor.NextBlock)
         
        min_indent = min(indents)
        _logger.debug('min_indent: %s', min_indent)
        return min_indent
        
    def is_empty_line(self,cursor):
        empty=False
        if len( str( cursor.block().text()).strip(' '))==0:
            empty=True
            _logger.debug('empty line [%s]', cursor.block().text() )
        return empty

    def test(self, mode='current_pos'):
        cursor = self.textedit.textCursor()

        if mode == 'current_pos':
            _logger.debug('current pos: %s', cursor.position())
        elif mode == 'single_line_comment':

            cursor.movePosition(
                QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
            self.textedit.setTextCursor(cursor)
            cursor.insertText(self.comment_str+' ')

        elif mode == 'get_range':
            start_pos, end_pos = [cursor.selectionStart(),
                                  cursor.selectionEnd()]
            _logger.debug('range: %s %s', start_pos, end_pos)
            self.sel_range = (start_pos, end_pos)

        elif mode == 'load_range':
            start_pos, end_pos = self.sel_range
            _logger.debug('load range: %s %s', start_pos, end_pos)
            self.moveToPosition(start_pos)

            cursor = self.textedit.textCursor()
            cursor.movePosition(
                QTextCursor.Right, QTextCursor.KeepAnchor, end_pos - start_pos)
            self.textedit.setTextCursor(cursor)

        elif mode == 'multi_line_comment':
            # find selected lines
            start_pos, end_pos = [cursor.selectionStart(),
                                  cursor.selectionEnd()]


            first_line,last_line = self.get_line_range(cursor,start_pos, end_pos)

            # If the selection contains only commented lines and surrounding
            # whitespace, uncomment. Otherwise, comment.
            is_comment_or_whitespace = True
            at_least_one_comment = False
            for _line_nb in range(first_line, last_line+1):

                text = str(cursor.block().text()).lstrip()
                _logger.debug('dealing text: %s', text)

                is_comment = text.startswith(self.comment_str)
                is_whitespace = (text == '')
                is_comment_or_whitespace *= (is_comment or is_whitespace)
                if is_comment:
                    at_least_one_comment = True
                cursor.movePosition(QTextCursor.NextBlock)



            min_indent = self.get_min_indent(cursor,start_pos,first_line,last_line)

            cursor.beginEditBlock()

            if is_comment_or_whitespace and at_least_one_comment:
                _logger.debug('need to uncomment')

                cursor.setPosition(start_pos)
                for _line_nb in range(first_line, last_line+1):
                    
                    if self.is_empty_line(cursor): 
                        cursor.movePosition(QTextCursor.NextBlock)
                        continue
                    
                    if _line_nb==first_line:
                        self.moveToPosition(start_pos)
                        if self.position_in_block(cursor)>min_indent:
                            start_pos-= len(self.comment_str)+1

                    cursor.movePosition(QTextCursor.StartOfLine)

                    cursor.movePosition(
                        QTextCursor.Right, QTextCursor.MoveAnchor, min_indent)

                    self.textedit.setTextCursor(cursor)
                    for i in range(len(self.comment_str)):
                        cursor.deleteChar()
                        end_pos-=1

                    next_char = cursor.block().text()[self.position_in_block(cursor)]
                    _logger.debug('next char: %s', next_char)

                    if next_char == ' ':
                        cursor.deleteChar()
                        end_pos-=1

                    cursor.movePosition(QTextCursor.NextBlock)

                    self.sel_range=(start_pos,end_pos)
                  
            else:
                
                _logger.debug('need to comment')
                cursor.setPosition(start_pos)
                for _line_nb in range(first_line, last_line+1):
                    if self.is_empty_line(cursor): 
                        cursor.movePosition(QTextCursor.NextBlock)
                        continue
                        
                    if _line_nb==first_line:
                        self.moveToPosition(start_pos)
                        
                        if self.position_in_block(cursor)>=min_indent:
                            start_pos+= len(self.comment_str)+1


                    cursor.movePosition(QTextCursor.StartOfLine)

                    cursor.movePosition(
                        QTextCursor.Right, QTextCursor.MoveAnchor, min_indent)

                    self.textedit.setTextCursor(cursor)
                    cursor.insertText('%s ' % self.comment_str)
                    end_pos+=len(self.comment_str)+1

                    cursor.movePosition(QTextCursor.NextBlock)

                    self.sel_range=(start_pos,end_pos)

            cursor.endEditBlock()


        elif mode == 'get_text_cur_pos':
            _logger.debug('get cur pos text')
            cursor = self.textedit.textCursor()

            positionInBlock = self.position_in_block(cursor)
            _logger.debug('block pos: %s', positionInBlock)
            _logger.debug('block text: %s', cursor.block().text())
            _logger.debug( cursor.block().text()[positionInBlock])

        elif mode == 'tab':
            print 'tab'
            cursor.beginEditBlock()
            
            start_pos, end_pos = [cursor.selectionStart(),
                  cursor.selectionEnd()]

            

            # get last first line
            first_line,last_line = self.get_line_range(cursor,start_pos, end_pos)
            _logger.debug('tab key: %s %s',first_line,last_line) # range(first_line, last_line+1)
            
            start_pos+=4
            
            # indent 4 spaces
            for _line_nb in range(first_line, last_line+1):
                cursor.movePosition(QTextCursor.StartOfLine)
                self.textedit.setTextCursor(cursor)
                
                # skip empty line
                if len(str(cursor.block().text()).strip(' ')) or first_line==last_line:
                       
                    cursor.insertText(' '*4)
                    end_pos+=4

                cursor.movePosition(QTextCursor.NextBlock)

            self.sel_range=(start_pos,end_pos)
            
            cursor.endEditBlock()

        elif mode == 'shift_tab':
            _logger.debug('shift_tab')
            cursor.beginEditBlock()
            
            start_pos, end_pos = [cursor.selectionStart(),
                  cursor.selectionEnd()]

            # get last first line
            first_line,last_line = self.get_line_range(cursor,start_pos, end_pos)

            for _line_nb in range(first_line, last_line+1):

                cursor.movePosition(QTextCursor.StartOfLine)

                if _line_nb==first_line:

                    for i in range(4):
                        next_char = cursor.block().text()[self.position_in_block(cursor)]
                        if next_char == ' ':
                            cursor.deleteChar()
                            start_pos-=1
                            end_pos-=1

                else:
                    for i in range(4):
                        next_char = cursor.block().text()
                        if next_char:
                            next_char = next_char[self.position_in_block(cursor)]
                        else:
                            break
                        if next_char == ' ':
                            cursor.deleteChar()
                            end_pos-=1

                
                self.textedit.setTextCursor(cursor)
                cursor.movePosition(QTextCursor.NextBlock)

            self.sel_range=(start_pos,end_pos)
            
            cursor.endEditBlock()
            
        elif mode == 'undo':
            _logger.debug('undo') # self.sel_range
            # if self.last_change=='toggle_comment':
                # self.toggle_comment()
            self.textedit.undo()
            
            if getattr(self,'sel_range',None):
                self.test('load_range')
                self.sel_range=None
                

        elif mode == 'delete_line':
            _logger.debug('delete_line')
            cursor.beginEditBlock()

            start_pos, end_pos = [cursor.selectionStart(),
                  cursor.selectionEnd()]

            # get last first line
            first_line,last_line = sorted(self.get_line_range(cursor,start_pos, end_pos))

            for _line_nb in reversed(range(first_line,last_line+1)):

                text_block=self.textedit.document().findBlockByLineNumber(_line_nb)
                cursor.setPosition (text_block.position ())
                self.textedit.setTextCursor(cursor)

                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()


            cursor.endEditBlock()
            
        elif mode == 'execute':
            _logger.debug('execute')
            # if self.lastnge=='toggle_comment':
                # self.toggle_comment()
            # if something selected, run it
            start_pos, end_pos = [cursor.selectionStart(),
                  cursor.selectionEnd()]
            
            run_all=0      
            if start_pos== end_pos:
                # run all
                cmd = self.textedit.toPlainText()
                run_all=1
            else:
                cmd = cursor.selectedText() 
                
            
            # get first "non-empty" line content
            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, start_pos)
            first_line=str(cursor.block().text())

            spaces=len(first_line)-len(first_line.lstrip(' '))
            start_pos_in_block = self.position_in_block(cursor)
            
            if not run_all:
                if start_pos_in_block < spaces:
                    # fill spaces
                    cmd = ' '*start_pos_in_block+cmd
                else:
                    cmd =  ' '*spaces + cmd
           
            cmd=str(cmd.replace(QChar(0x2029),QChar('\n')))
            
            cmd = self.dedent_code(cmd)
            # print 'will run cmd:\n',cmd
            exec(cmd)

    def dedent_code(self,code):
        indents=[]
        for line in code.splitlines():
            _logger.debug('---> %s',line)
            spaces = len(line)-len(line.lstrip(' '))
            if len(line.strip(' '))>0:
                indents.append(spaces)
            
        indent = min(indents)
        _logger.debug('min indents: %s',indent)
        new_code=''
        for line in code.splitlines():
            if len(line)>indent:
                _logger.debug('working on: %s',line)
                new_code+=line[indent:]+'\n'
            else:
                new_code+=line+'\n'
                
        return new_code 

def get_mel_global(var):
    try:
        return mel.eval('$tmp_var1=%s' % var)
    except:
        return mel.eval('$tmp_var2=%s' % var)

gCommandExecuterTabs = get_mel_global('$gCommandExecuterTabs')

filter = CustomFilter()
#qApp.removeEventFilter(filter)
qApp.installEventFilter(filter)

# This can remove the filter we installed
# qApp.removeEventFilter(filter)
