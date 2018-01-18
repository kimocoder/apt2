try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from core.actionModule import actionModule
from core.keystore import KeyStore as kb
from core.mynmap import mynmap


class scan_nmap_vncbrute(actionModule):
    def __init__(self, config, display, lock):
        super(scan_nmap_vncbrute, self).__init__(config, display, lock)
        self.title = "NMap VNC Brute Scan"
        self.shortName = "NmapVNCBruteScan"
        self.description = "execute [nmap -p5800,5900 --script=vnc-brute] on each target"

        self.requirements = ["nmap"]
        self.triggers = ["newPort_tcp_5800", "newPort_tcp_5900"]

        self.safeLevel = 5

    def getTargets(self):
        self.targets = kb.get(['port/tcp_5800/ip', 'port/tcp_5900/ip'])

    def process(self):
        # load any targets we are interested in
        self.getTargets()

        # loop over each target
        for t in self.targets:
            # verify we have not tested this host before
            if not self.seentarget(t):
                # add the new IP to the already seen list
                self.addseentarget(t)
                self.display.verbose(self.shortName + " - Connecting to " + t)
                # run nmap
                n = mynmap(self.config, self.display)
                scan_results = n.run(target=t, flags="--script=vnc-brute", ports="5800,5900", vector=self.vector, filetag=t + "_VNCBRUTE")
                for porttag in scan_results.iter('port'):
                    portnum = porttag.attrib['portid']
                    for scriptid in porttag.findall('script'):
                        if scriptid.attrib['id'] == "vnc-brute":
                            if scriptid.attrib['output'] == "No authentication required":
                                self.addVuln(t, "VNCNoAuth", {"port":portnum,"message":"No authentication required","output": n.outfile.replace("/", "%2F") + ".xml"})
                                self.fire("VNCNoAuth")
                            for elem in scriptid.iter('elem'):
                                if elem.attrib['key'] == "password":
                                    self.addVuln(t, "VNCBrutePass", {"port":portnum, "password":elem.text})
                                    self.fire("VNCBrutePass")

        return