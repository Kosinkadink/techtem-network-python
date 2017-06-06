import os, sys, ast

common_location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
main_dir = os.path.realpath(os.path.join(common_location, '..'))
sys.path.insert(0, os.path.join(main_dir, 'source/'))
import CommonCode_Client


class TemplateProt(CommonCode_Client.TemplateProt):
    """
    Protocol's data sent is as follows:
        {"namereq": name_request}: string type
    Returns ip corresponding to name_request string 
    """
    standalone = True
    default_vars = ["url"]
    default_command = "getname"
    varDict = dict(send_cache=409600, scriptname='name', version='3.0.0')

    def __init__(self, location, startTerminal):
        CommonCode_Client.TemplateProt.__init__(self, location, startTerminal)

    def set_funcMap(self):
        self.add_to_funcMap("getname", self.getNameCommand)

    def set_terminalMap(self):
        self.terminalMap["getname"] = (lambda data: self.makeNameConnection(data[1],data[2]))

    def process_list_to_dict(self, input_list):
        """
        Transform a list of strings into proper dictionary output to be sent to server
        :param input_list: list containing name requested
        :return: dictionary to use as data
        """
        return {"namereq": input_list[0]}

    def init_spec_extra(self):
        if not os.path.exists(self.__location__ + '/resources/programparts/%s/nameservers.txt' % self.varDict["scriptname"]):
            with open(self.__location__ + '/resources/programparts/%s/nameservers.txt' % self.varDict["scriptname"],
                      "a") as makeprot:  # file used for listing network name servers for /connect functionality
                makeprot.write("")

    def getNameCommand(self, s, data=None, dataToSave=None):
        return ast.literal_eval(s.recv(128))

    def makeNameConnection(self, name_request, ip=None):
        if not ip:
            nameservers = self.parse_settings_file(
                os.path.join(self.__location__, 'resources/programparts/name/nameservers.txt'))
        else:
            nameservers = [[ip]]
        for server in nameservers:
            if not isinstance(name_request,list):
                name_request = [name_request]
            return self.connectip(server[0], self.process_list_to_dict(name_request), "getname")
