import json

default_config = {'address':'127.0.0.1', 'port':5000}
def load():
    try:
        with open('config.json') as config_file:
            json_data = json.loads(config_file.read())
            return json_data
    except:
        return default_config