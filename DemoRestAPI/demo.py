# -*- coding: utf-8 -*-

from __future__ import print_function

"""
City4Age test demo application
=================================

This Python script performs a simple test to deployed RestAPI Interface and Linked Data Interface to test
if data is storing well into DB.

The script makes the following actions:

--> Test some initial GET actions
--> Test if it can make some actions into DB without a registered cookie.
--> Perform a invalid user login into the API.
--> Log into the system.
--> Perform a search into DB with a criteria to show that there isn't data
--> Show a sample data. This data will be the data used in the demo to test if all works great.
--> Send INVALID data to test application JSON Errors
--> Send VALID data to insert data into DB
--> Perform a second search into DB to demonstrate that data is inserted OK.
--> Send a SPARQL query to Fuseki to request data from DB and inference support.

"""

import time
import ssl
import urllib
from datetime import datetime
import json
import requests
from SPARQLWrapper import SPARQLWrapper
import os

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Demo"

# Configuration
REST_API_URL = "nowhere"
USERNAME = "jonh"
PASSWORD = "DOE"

##################################################
#######
# Configuring request with sample data
#######

# Configuring actual file PATH
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

SERVER = 'https://dev_c4a.morelab.deusto.es/api'
FUSEKI = 'https://dev_c4a.morelab.deusto.es/fuseki/city4age/query'
CERT = __location__ + '/morelab.crt'


def start_demo():
    #### Start Time
    start_time = datetime.now()
    #
    # Step 1: Making some GET actions into RA
    #
    print("--> TEST 1: Simple query to API to know if it works \n")
    time.sleep(2)
    #
    r = requests.get(SERVER, verify=CERT)
    if r.status_code == 200:
        print(r.text, "\n")
    else:
        raise TestException("Server returned an error status code: " + r.status_code)

    time.sleep(3)
    #
    # Step 2: Basic query failure
    #
    print("--> TEST 2: A search without login into the API \n")
    time.sleep(2)
    #
    file = open("./data/json_search.txt", "r")
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/search', json=data, verify=CERT)
    if r.status_code != 200:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned a valid status code when it needs to return an error status code \n"
                            ": " + r.status_code)
    file.close()
    time.sleep(3)
    #
    # Step 3: Performing an invalid user login into Rest
    #
    print("--> TEST 3: Log into the system with INVALID user", "\n")
    #
    time.sleep(2)
    #
    file = open("./data/invalid_json_login.txt", "r")
    data = json.load(file)
    print("Data sent to the api: ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/login', json=data, verify=CERT)
    if r.status_code == 401:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + r.status_code)
    time.sleep(3)
    #
    # Step 4: Valid log into the system
    #
    print("--> TEST 4: Log into the system with VALID user", "\n")
    #
    time.sleep(2)
    #
    file = open("./data/json_login.txt", "r")
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/login', json=data, verify=CERT)
    if r.status_code == 200:
        cookies = r.cookies.get_dict()
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + r.status_code)
    time.sleep(3)
    #
    # Step 5: Search into DB from sample DATA
    #
    print("--> TEST 5: Query to API to know if there is previously data into database", "\n")
    #
    time.sleep(2)
    #
    file = open("./data/json_search.txt", "r")
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/search', cookies=cookies, json=data, verify=CERT)
    if r.status_code == 200:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + r.status_code)
    time.sleep(3)
    #
    # Step 6: Sending execution error sample INVALID DATA
    #
    print("--> TEST 6: Send INVALID executed action data ", "\n")
    #
    time.sleep(2)
    #
    file = open('./data/invalid_json_data_sample.txt', 'r')
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/add_action', cookies=cookies, json=data, verify=CERT)
    if r.status_code != 200:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an valid status code \n"
                            ": " + r.status_code)
    time.sleep(3)
    #
    # Step 7: Send Valid JSON DATA
    #
    print("--> TEST 7: Send VALID executed action data ", "\n")
    #
    time.sleep(2)
    #
    file = open('./data/json_data_sample.txt', 'r')
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/add_action', cookies=cookies, json=data, verify=CERT)
    if r.status_code == 200:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + str(r.status_code))
    time.sleep(3)
    #
    # Step 8: Query again to know if the data is stored into DB
    #
    print("--> TEST 8: 2º Query To API to know if data is inserted into DB", "\n")
    #
    time.sleep(2)
    #
    file = open("./data/json_search.txt", "r")
    data = json.load(file)
    print("Data sent to the api ", data, "\n")
    time.sleep(1)
    #
    r = requests.post(SERVER + '/search', cookies=cookies, json=data, verify=CERT)
    if r.status_code == 200:
        print(r.text, "status code: ", r.status_code, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + r.status_code)
    time.sleep(3)
    #
    # Step 9: Send SPARQL query to retrieve information
    #
    print("--> TEST 9: Sending a SPARQL query to Fuseki server to show knowledge", "\n")
    #
    time.sleep(2)
    #
    query_string = "SELECT ?subject ?predicate ?object WHERE { ?subject " \
                   "<file:///opt/c4a_data_repository/LinkedDataInterface/conf/vocab/location_location_name> ?object }"
    print("SPARQL query to be sent to FUSEKI endpoint: ", query_string, "\n")
    time.sleep(1)
    #
    sparql = SPARQLWrapper(FUSEKI)
    sparql.method = 'GET'
    sparql.setQuery(query_string)
    sparql.setReturnFormat('json')
    res = sparql.query()
    if res.response.code == 200:
        res_dict = res.convert()
        print(res_dict, "\n")
    else:
        raise TestException("Server returned an invalid status code \n"
                            ": " + res.response.status)
    time.sleep(3)
    #
    # End time
    #
    end_time = datetime.now()
    print("Script succeeded in: ", (end_time - start_time).seconds, " seconds", "\n")


# Exception
class TestException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "There is an error while executing this tests: " + str(self.value)
