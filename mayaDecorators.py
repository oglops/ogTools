from functools import wraps
import time
import maya.cmds as mc
import maya.api.OpenMaya as OM


class ContextDecorator(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __enter__(self):
        # Note: Returning self means that in "with ... as x", x will be self
        return self

    def __exit__(self, typ, val, traceback):
        pass

    def __call__(self, f, rollback=False):
        @wraps(f)
        def wrapper(*args, **kw):
            with self:
                try:
                    return f(*args, **kw)
                except:
                    if rollback:
                        mc.undo()
                    raise
        return wrapper


class undochunk(ContextDecorator):

    def __enter__(self):
        mc.undoInfo(openChunk=True)
        return self

    def __exit__(self, typ, val, traceback):
        # Note: typ, val and traceback will only be not None
        # If an exception occured
        mc.undoInfo(closeChunk=True)


class disableundo(ContextDecorator):

    def __enter__(self):
        mc.undoInfo(stateWithoutFlush=False)
        return self

    def __exit__(self, typ, val, traceback):
        mc.undoInfo(stateWithoutFlush=True)


class disablerefresh(ContextDecorator):

    def __enter__(self):
        mc.refresh(suspend=True)
        return self

    def __exit__(self, typ, val, traceback):
        mc.refresh(suspend=False)
        # force refresh
        mc.refresh(suspend=False)


class disableviewport(ContextDecorator):

    def __enter__(self):
        mm.eval('setNamedPanelLayout "Single Perspective View";')
        model_panel = next(
            (x for x in mc.getPanel(vis=1) if x.startswith('modelPanel')), None)
        mm.eval('outlinerPanel -e -rp %s outlinerPanel1;' % model_panel)
        return self

    def __exit__(self, typ, val, traceback):
        mm.eval('PreviousViewArrangement;')


class capturenewnodes(ContextDecorator):

    def __init__(self, **kwargs):
        super(capturenewnodes, self).__init__(**kwargs)
        self._id = None
        self._nodes = []

    def __enter__(self):
        if not self._id:
            self._id = OM.MDGMessage.addNodeAddedCallback(
                self.node_added, 'dependNode')
        return self

    def __exit__(self, typ, val, traceback):
        if self._id:
            OM.MDGMessage.removeCallback(self._id)
            self._id = None

    def node_added(self, node, *args):
        self._nodes.append(OM.MObjectHandle(node))

    def get_nodes(self, handle=False, full_path=False):
        self._nodes = filter(lambda x: x.isValid(), self._nodes)
        nodes = self._nodes
        if not handle:
            nodes = []
            for n in self._nodes:
                mObj = n.object()
                if mObj.hasFn(OM.MFn.kDagNode):
                    fnNode = OM.MFnDagNode(mObj)

                    if full_path:
                        path = fnNode.fullPathName()
                    else:
                        path = fnNode.partialPathName()

                elif mObj.hasFn(OM.MFn.kDependencyNode):
                    path = OM.MFnDependencyNode(mObj).name()

                nodes.append(path)

        return nodes
