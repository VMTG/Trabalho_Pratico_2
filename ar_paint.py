import json
import argparse
import sys

def readDile(path):
    B ={}
    G ={}
    R ={}
    try:
        with open(json_path, 'r') as openfile:
            json_object = json.load(openfile)
            ranges = json_object['limits']
    # if the file doesn't exist, send out an error message and quit
    except FileNotFoundError:
        sys.exit('The .json file with the color data doesn\'t exist.')

    # Iterating through the json
    G ={'min': int(data['limits']['G']['min']), 'max': int(data['limits']['G']['max'])}
    B = {'min': int(data['limits']['B']['min']), 'max': int(data['limits']['B']['max'])}
    R = {'min': int(data['limits']['R']['min']), 'max': int(data['limits']['R']['max'])}
    # Closing file
    f.close()
    return R, G , B

def initialization():
    # Definição dos argumentos de entrada:
    parser = argparse.ArgumentParser(description='Ar Paint ')
    parser.add_argument('-j','--json',type = str, required= True, help='Full path to json file')
    parser.add_argument('-usm','--use_shake_prevention', action='store_true', help='Use shake prevention mode')
    args = vars(parser.parse_args())

    
    path = 'limits.json' if not args['json'] else args['json'] # A localização do ficheiro json
    usp = args['use_shake_prevention'] # Ativacao do use shake mode
    return path , usp