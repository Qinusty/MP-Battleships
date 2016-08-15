import json

def myJoin(list1, list2, joiner=" "):
    retList = []
    for x in range(len(list1)):
        retList.append(list1[x].replace('\n', '') + joiner + list2[x])
    return retList

def jsencode(dict):
    return json.dumps(dict).encode('utf-8')

def jsdecode(data):
    return json.loads(data.decode('utf-8'))