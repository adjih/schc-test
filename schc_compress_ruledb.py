#---------------------------------------------------------------------------
# The Compression/Decompression rule database
# Copying/following closely the equivalent code from schc_fragment_ruledb.py
#
# Cedric Adjih - Inria - 2018
#---------------------------------------------------------------------------

from schc_param import *
import json
from schc_ruledb_tag import *
from schc_ruledb import schc_ruledb

from pypacket_dissector import _json_keys
SCHC_FID_LIST = [
    getattr(_json_keys, k)
    for k in dir(_json_keys)
    if k.startswith("JK_")
] + [ # XXX currently missing from the pypacket_dissector._json_keys:
    "IPV6.DEV_PREFIX", "IPV6.DEV_IID", "IPV6.APP_PREFIX", "IPV6.APP_IID",
    "UDP.DEV_PORT", "UDP.APP_PORT"
]

SCHC_DI_LIST = ["Bi"]
SCHC_MO_LIST = ["equal", "ignore", "match-mapping", "mapping-sent"]
SCHC_CDA_LIST = [
    "not-sent", "value-sent", "mapping-sent", "lsb",
    "comp-length", "comp-chk", "DEViid", "APPiid"
]

class schc_runtime_compress_rule:
    def __init__(self, C, r):
        '''
        C: a runtime context.
        r: a dict-like compression/decompression rule.
        '''
        self.C = C
        self.r = r

class schc_compress_ruledb(schc_ruledb):
    def __init__(self):
        self.ruledb = {}

    def get_runtime_rule(self, cid, rid):
        return schc_runtime_compress_rule(self.get_runtime_context(cid),
                                          self.get_rule(cid, rid))


    def check_action_rule(self, action):
        ''' Check whether an action rule is coherent '''
        # XXX: only very partial checks are implemented
        self.is_one_of(action, TAG_FID, SCHC_FID_LIST, ignore_case=True)
        self.is_int(action, TAG_FL)
        self.is_int(action, TAG_FP)
        self.is_one_of(action, TAG_DI, SCHC_DI_LIST, ignore_case=True)
        self.is_one_of(action, TAG_MO, SCHC_MO_LIST, ignore_case=True)
        self.is_one_of(action, TAG_CDA, SCHC_CDA_LIST, ignore_case=True)

    def canonicalize_action_rule(self, action):
        for tag in action:
            upper_tag = tag.upper()
            if upper_tag != tag:
                action[upper_tag] = action[tag]
                del action[tag]
        for tag in [TAG_FID, TAG_DI, TAG_MO, TAG_CDA]:
            if tag in action:
                action[tag] = action[tag].upper()

    def load_json_file_one(self, cid, json_file):
        """see schc-test/example-rule/schc-rule-draft-09-r1.json"""

        j = json.load(open(json_file))
        self.is_defined(j, TAG_COMP_RULE)
        #
        rule = j[TAG_COMP_RULE]
        self.is_int(rule, TAG_RID)
        self.is_defined(rule, TAG_RULE_SET)
        #
        action_list = rule[TAG_RULE_SET]
        for action in action_list:
            self.canonicalize_action_rule(action)
            self.check_action_rule(action)
        #
        self.update_rule(cid, rule[TAG_RID], rule)
        return rule[TAG_RID]

'''
test code
'''
if __name__ == "__main__":
    cdb = schc_compress_ruledb()
    cid = cdb.load_context_json_file("example-rule/context-001.json")
    rid = cdb.load_json_file(cid, "example-rule/schc-rule-draft-09-r1.json")
    print("## pprint()")
    cdb.pprint()
    print("## get_context(%s)" % str(cid))
    print(cdb.get_context(cid))
    print("## get_rule(%s, %s)" % (str(cid), str(rid)))
    print(cdb.get_rule(cid, rid))
    print("## pprint(cid=%s, rid=%s)" % (str(cid), str(rid)))
    cdb.pprint(cid=cid, rid=rid)
    #
    cdb.get_runtime_context(cid)
    rrc = cdb.get_runtime_rule(cid, rid)
    print(rrc)
