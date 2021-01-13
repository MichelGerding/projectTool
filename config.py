import json
import os, pathlib

config_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "config.json")

def Get(index):
    #check if index is set correctly
    if index == "" or index == None or index == False:
        return None

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        indexes = index.split('.')
        
        #get the value of the requested config part. if it doesnt exist return None
        try:
            configValue = config
            for index in indexes:
                configValue = configValue[index]
        except:
            return None

        return configValue


def Set(index, value):
    if index == "" or index == None or index == False:
        return None

    # load the config file into the config variable
    config_file_read = open(config_path, 'r')
    config = json.load(config_file_read)
    config_file_read.close()

    # update the config
    current = config
    parts = index.split('.')
    last_part = parts.pop()

    while parts:
        part = parts.pop(0)

        # check if it is a list and if it is make the part an int
        if isinstance(current, list):
            part = int(part)

            
        # check if the current part of the obj is a str 
        if isinstance(current, str):
            current = {}
        
        #try to set current to the next part of the array
        try:
            current = current[part]
        # if it doesnt exist set the next part to an empty dict 
        except:
            current[part] = {}
            current = current[part]


    # check if current is a list and if it is make it an the last part an int
    if isinstance(current, list):
        last_part = int(last_part)

    #set the value to the correct part and write it to the config
    current[last_part] = value
    with open(config_path, 'w') as config_file:
        config_file.write(json.dumps(config))


if __name__== "__main__":
    pass