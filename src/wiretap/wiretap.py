# coding: utf-8

import os
import sys
import imp
import platform
import logging
import pprint
import xml.dom.minidom as minidom


DISCREET_PATH = "/usr/discreet"
WIRETAP_DEFAULT_VERSION = "2018.3"
WIRETAP_VERSION = os.environ.get('WIRETAP_VERSION', WIRETAP_DEFAULT_VERSION)
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
wt = None


def import_wiretap_library(version=WIRETAP_VERSION):
    logger.info('Use Wiretap version %s.' % version)
    library_path = os.path.join(
        DISCREET_PATH, 'python', version, 'lib', 'python2.7', 'site-packages', 'adsk',
        'libwiretapPythonClientAPI.so')
    return imp.load_dynamic('libwiretapPythonClientAPI', library_path)


wt = import_wiretap_library()


class WiretapException(Exception):
    """Manage WireTap exceptions"""
    pass


class WiretapNodeType:
    Node = 'NODE'
    Project = 'PROJECT'
    User = 'USER'
    Workspace = 'WORKSPACE'
    Desktop = 'DESKTOP'
    Volume = 'VOLUME'
    Folder = 'FOLDER'
    Library = 'LIBRARY'
    LibraryList = 'LIBRARY_LIST'


class WiretapHandler(object):

    def __init__(self, hostname='localhost'):
        """

        :param hostname:
        :type hostname: string
        """
        self.hostname = hostname

        # Initialize wiretap connection
        if not wt.WireTapClientInit():
            msg = "Unable to initialize WireTap client API"
            logger.critical(msg)
            raise WiretapException(msg)

        self._server = wt.WireTapServerHandle(hostname)

    def __del__(self):
        """
        Delete server objet and uninitialize connection with the server
        """
        self._server = None
        wt.WireTapClientUninit()

    def create_project(self, project_name, settings={}):
        """
        Create a Flame Family project.

        :param project_name: The name of project to create
        :type project_name: string
        :params settings: The settings of the project to create
        :type settings: dict
        :return: project node
        :rtype: WireTapNodeHandle
        """

        if not self._child_node_exists("/projects", project_name, WiretapNodeType.Project):
            logger.info("Project '%s' does not exists. Create it with settings: \n%s" % (project_name, pprint.pformat(settings)))

            volumes = self.get_volumes()
            logger.debug("Framestore found: %s" % volumes)

            if len(volumes) == 0:
                raise Exception("Cannot create project! There is no volumes defined for this flame.")

            # use the first volume available
            volume_node = self._get_node_from_path("/volumes/%s" % volumes[0])

            if not volume_node:
                raise WiretapException("Unable to retrieve a volume.")
            else:
                self._create_node(volume_node, WiretapNodeType.Node, project_name)

                # create project settings
                xml = '<Project>'
                for (k, v) in settings.iteritems():
                    xml += '<%s>%s</%s>' % (k, v, k)
                xml += '</Project>'

                project_node = wt.WireTapNodeHandle(self._server, "/projects/%s" % project_name)
                if not project_node.setMetaData("XML", xml):
                    raise WiretapException("Error setting metadata for %s: %s" % (project_name, project_node.lastError()))

                workspace_node = self._create_node(project_node, WiretapNodeType.Workspace)

                self._create_node(workspace_node, WiretapNodeType.Desktop)

                # create Custom Folders into the project
                # libraries = {
                #     '01_IMPORTS': ['2D', '3D', 'CONFO', 'CT', 'DP', 'ELEMENTS'],
                #     '02_JOB': [],
                #     '03_WIP': [],
                #     '04_MASTERS': []
                # }
                # self._create_project_librairies(project_node, 'Libraries', libraries)

                # shared_libraries = {'TRANSFERTS': []}
                # self._create_project_librairies(project_node, 'Shared Libraries', shared_libraries)

                return project_node

    def create_user(self, user_name):
        """
        Create a Flame Family user.

        :param user_name: The username to create
        :type user_name: string
        :return: user node
        :rtype: WireTapNodeHandle
        """
        users = wt.WireTapNodeHandle(self._server, "/users")
        user_node = self._create_node(users, WiretapNodeType.User, user_name)

        user_nodes = [
            '2dtransform', '3dblur', 'CreatedBy', 'action', 'audio', 'automatte',
            'autostabilize', 'average', 'batch', 'batchclip', 'blur', 'bumpDisplace',
            'burnin', 'burnmetadata', 'channelEditor', 'check', 'clamp', 'colourframe',
            'colourpicker', 'colourwarper', 'combine', 'comp', 'composite', 'compound',
            'correct', 'damage', 'deal', 'deform', 'degrain', 'deinterlace',
            'deliverables', 'denoise', 'depthOfField', 'desktop', 'difference',
            'dissolve', 'distort', 'dve', 'edgeDetect', 'editdesk', 'exposure',
            'fieldmerge', 'filter', 'flip', 'gatewayImport', 'glow', 'gradient',
            'guides', 'hotkey', 'interlace', 'keyerChannel', 'keyerHLS', 'keyerRGB',
            'keyerRGBCMYL', 'keyerYUV', 'letterbox', 'logicop', 'logo', 'look',
            'lut', 'mapConvert', 'mask', 'matchbox', 'mediaImport', 'modularKeyer',
            'mono', 'morf', 'motif', 'motionAnalyse', 'motionBlur', 'paint',
            'pixelspread', 'play', 'posterize', 'pulldown', 'pybox', 'recursiveOps',
            'regrain', 'resize', 'separate', 'stabilizer', 'status', 'stereo',
            'stereoAnaglyph', 'stereoInterlace', 'stereoToolbox', 'stylize',
            'substance', 'tangentPanel', 'text', 'timewarp', 'tmp', 'vectorViewer', 'viewing']
        for node in user_nodes:
            self._create_node(parent=user_node, node_type=WiretapNodeType.Node, node_name=node)

        return user_node

    def get_projects(self):
        """
        Retrieve all projects from the database
        :return: projects
        :rtype: list
        """
        projects_node = self._get_node_from_path('/projects')
        children = self._get_children(projects_node)

        return children.keys()

    def get_project(self, project_name):
        """
        Retrieve project from database

        :param project_name: project name
        :type project_name: string
        :return: project node handler
        :rtype: WireTapNodeHandle
        """
        return self._get_node_from_path("/projects/%s" % project_name)

    def get_users(self):
        """
        Retrieve all users from the database

        :return: users
        :rtype: list
        """
        users_node = self._get_node_from_path('/users')
        children = self._get_children(users_node)

        return children.keys()

    def get_user(self, user_name):
        """
        Retrieve user from database

        :param user_name: user name
        :type user_name: string
        :return: user node handler
        :rtype: WireTapNodeHandle
        """
        return self._get_node_from_path("/users/%s" % user_name)

    def delete_user(self, user_name):
        """
        Delete a user from database

        :param user_name: user name
        :type user_name: string
        """
        user_node = self.get_user(user_name)
        if not user_node.destroyNode():
            raise WiretapException("Unable to delete user: %s" % user_node.lastError())

    def get_volumes(self):
        """
        Return a list of volumes names

        :return: List of volumes available
        :rtype: list
        """

        volumes_node = self._get_node_from_path('/volumes')
        children = self._get_children(volumes_node)

        return children.keys()

    def _create_node(self, parent, node_type, node_name=None):
        """
        :param parent: parent node handler
        :type parent: WireTapNodeHandle
        :param node_type:
        :type node_type: string
        :param node_name:
        :type node_name: string
        :return: node created
        :rtype: WireTapNodeHandle
        :raises WiretapException: if can't create the node
        """
        node_name = node_type.title() if not node_name else node_name
        node = wt.WireTapNodeHandle()
        if not parent.createNode(node_name, node_type, node):
            raise WiretapException("Unable to create node: %s" % parent.lastError())

        return node

    def _create_project_librairies(self, parent, library_name, libraries_dict):
        """
        Create folders into libraries

        :param parent: parent node handler
        :type parent: WireTapNodeHandle
        :param library_name:
        :type library_name: string
        :param libraries_dict:
        :type libraries_dict: dict
        """

        library_node = self._get_node(parent, library_name, WiretapNodeType.LibraryList)
        for lib in libraries_dict.keys():
            lib_node = self._create_node(library_node, WiretapNodeType.Library, lib)

            if libraries_dict[lib]:
                for folder in libraries_dict[lib]:
                    self._create_node(lib_node, WiretapNodeType.Folder, folder)

    def _get_project_metadata(self, project_node):
        """
        Retrieve XML metadata of the project node

        :param project_node: project node handler
        :type project_node: WireTapNodeHandle
        :return: xml strings
        :rtype: string
        """
        if project_node is not None:
            xml = wt.WireTapStr()
            project_node.getMetaData("XML", "", 1, xml)

            pretty_xml = minidom.parseString(xml.c_str()).toprettyxml()
            return pretty_xml

    def _get_node_from_path(self, path):
        """
        Retrieve node handler from path

        :param path: the path of the node
        :type path: string
        :return: the node handler
        :rtype: WireTapNodeHandle
        """
        node = wt.WireTapNodeHandle(self._server, path)

        node_name = wt.WireTapStr()
        if node.getDisplayName(node_name):
            return node
        else:
            return None

    def _get_children(self, parent):
        """
        Retrieve all children from a parent node

        :param parent:
        :type parent: WireTapNodeHandle
        :return: a dictionnary contening children of the node handler
        :rtype: dict
        """
        children = dict()
        num_children = wt.WireTapInt(0)
        if not parent.getNumChildren(num_children):
            raise WiretapException("Unable to obtain number of volumes: %s" % parent.lastError())

        child_obj = wt.WireTapNodeHandle()
        for child_idx in range(num_children):
            if not parent.getChild(child_idx, child_obj):
                raise WiretapException("Unable to get child: %s" % parent.lastError())

            node_name = wt.WireTapStr()
            if not child_obj.getDisplayName(node_name):
                raise WiretapException("Unable to get child name: %s" % child_obj.lastError())

            children[str(node_name)] = child_obj
        return children

    def _get_node(self, parent_node, node_name, node_type):
        """
        Get a node

        :param parent_node: Node from which we want to search
        :type parent_node: WireTapNodeHandle
        :param node_name: Name of the node we search
        :type node_name: str
        :param node_type: Type of the node we search
        :type node_type: str
        :returns: the searched node
        :rtype: WireTapNodeHandle
        """
        parent_node_name = wt.WireTapStr()

        if not parent_node.getDisplayName(parent_node_name):
            raise WiretapException("Couldn't get node name: %s" % parent_node.lastError())
        # logger.debug("parent node name: %s" % parent_node_name)

        num_children = wt.WireTapInt(0)
        if not parent_node.getNumChildren(num_children):
            raise WiretapException("Couldn't get children number for the node %s: %s" % (parent_node_name.c_str(), parent_node.lastError()))
        # logger.debug("parent num children: %s" % int(num_children))

        result_node = None
        child_node = wt.WireTapNodeHandle()
        child_node_type = wt.WireTapStr()
        child_node_name = wt.WireTapStr()

        # iterate over children
        for child_idx in range(num_children):
            # get child node
            if not parent_node.getChild(child_idx, child_node):
                raise WiretapException("Unable to get child: %s" % parent_node.lastError())
            # logger.debug("child: %s" % child_node)

            # get child node name
            if not child_node.getDisplayName(child_node_name):
                raise WiretapException("Couldn't get node name: %s" % child_node.lastError())
            # logger.debug("child node name: %s" % child_node_name.c_str())

            # get child node type
            if not child_node.getNodeTypeStr(child_node_type):
                raise WiretapException("Couldn't get node type: %s" % child_node.lastError())
            # logger.debug("child node type: %s" % child_node_type.c_str())

            # check if child match criteria
            if child_node_name.c_str() == node_name and child_node_type.c_str() == node_type:
                result_node = child_node
                # logger.debug("node found !")
                break

            result_node = self._get_node(child_node, node_name, node_type)
            if result_node:
                # logger.debug("node found !")
                return result_node

        return result_node

    def _child_node_exists(self, parent_path, child_name, child_type):
        """
        Helper method. Check if wiretap node exists.

        :param parent_path: Parent node to scan
        :type parent_name: str
        :param child_name: Name of the child node to look for
        :type child_name: str
        :param child_type: Type of the child node to look for
        :type child_type: str
        :returns: Type if node exists, false otherwize.
        """
        # get the parent
        parent = wt.WireTapNodeHandle(self._server, parent_path)

        # get number of children
        num_children = wt.WireTapInt(0)
        if not parent.getNumChildren(num_children):
            raise WiretapException(
                "Wiretap error: Unable to obtain number of "
                "children for node %s> Please check that your "
                "wiretap service is running. "
                "Error reported: %s" % (parent_path, parent.lastError()))

        # iterate over children, look for the given node
        child_obj = wt.WireTapNodeHandle()
        for child_idx in range(num_children):
            # get the child
            if not parent.getChild(child_idx, child_obj):
                raise WiretapException("Unable to get child: %s" % parent.lastError())

            node_name = wt.WireTapStr()
            node_type = wt.WireTapStr()

            if not child_obj.getDisplayName(node_name):
                raise WiretapException("Unable to get child: %s" % child_obj.lastError())

            if not child_obj.getNodeTypeStr(node_type):
                raise WiretapException("Unable to obtain child type: %s" % child_obj.lastError())

            if node_name.c_str() == child_name and node_type.c_str() == child_type:
                return True

        return False
