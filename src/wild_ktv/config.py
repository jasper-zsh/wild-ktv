import yaml

Config = {}

def load():
    global Config
    with open('config.yaml') as f:
        Config = yaml.load(f, Loader=yaml.Loader)

def get(key: str):
    return Config[key]