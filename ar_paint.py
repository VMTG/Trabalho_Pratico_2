import json
import argparse
import sys

def readFile(path):
    B ={}
    G ={}
    R ={}

    file = open(path)
    data = json.load(file)

    # Iterating through the json
    G ={'min': int(data['limits']['G']['min']), 'max': int(data['limits']['G']['max'])}
    B = {'min': int(data['limits']['B']['min']), 'max': int(data['limits']['B']['max'])}
    R = {'min': int(data['limits']['R']['min']), 'max': int(data['limits']['R']['max'])}
    # Closing file
    file.close()
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

