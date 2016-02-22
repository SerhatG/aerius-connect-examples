#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.
"""
import base64
import getopt
import json
import time
import sys
import os
import websocket

DEBUG_ENABLED = False
DEBUG_INPUT_FILE = 'debug.input.json'
DEBUG_RESULT_FILE = 'debug.result.json'
CONNECT_HOST = 'ws://connect.aerius.nl'
CONNECT_SERVICE_URL = '/connect/2/services'
CONNECT_SERVICE_FULL = CONNECT_HOST + CONNECT_SERVICE_URL

COMMAND_VALIDATE = "validate"
COMMAND_CONVERT = "convert"
COMMAND_CALCULATEANDEMAIL = "calculateAndEmail"
COMMAND_CALCULATEREPORTANDEMAIL = "calculateReportAndEmail"
COMMAND_MERGE = "merge"

ALL_COMMANDS = [
    COMMAND_VALIDATE,
    COMMAND_CONVERT,
    COMMAND_CALCULATEANDEMAIL,
    COMMAND_CALCULATEREPORTANDEMAIL,
    COMMAND_MERGE
]

# JSON BASE will we will fill based on the action chosen
JSON_BASE = """
{
    "jsonrpc":"2.0",
    "id":0,
    "method":"",
    "params":{
        "dataType":"GML",
        "contentType":"TEXT",
        "data":""
    }
}
"""


def debug(args):
    if DEBUG_ENABLED:
        print("DEBUG:" + args)


def get_json(method, params):
    json_data = json.loads(JSON_BASE)
    json_data["method"] = method
    # Create an unique id
    json_data["id"] = int(time.time() * 1000)
    json_data["params"] = params

    return json_data


def service_convert2gml(inputgml, outputfile):
    call_connect(
        get_json(
            'conversion.convert2GML',
            {
                "dataType": "GML",
                "contentType": "TEXT",
                "data": inputgml
            }
        ),
        outputfile
    )


def service_validate(inputgml):
    call_connect(
        get_json(
            'validation.validate',
            {
                "dataType": "GML",
                "contentType": "TEXT",
                "data": inputgml
            }
        )
    )


def service_calculate_and_email(inputgml, emailaddress):
    json_data = get_json(
        'calculation.calculateAndEmail',
        {
            "email": emailaddress,
            "options": {
                "calculationType": "NBWET",
                "year": 2016,
                "substances": [
                    "NOX",
                    "NH3"
                ]
            },
            "data": [{
                "dataType": "GML",
                "contentType": "TEXT",
                "data": inputgml
            }]
        }
    )

    call_connect(json_data)


def service_calculate_report_and_email(inputgml, emailaddress):
    json_data = get_json(
        'report.calculateReportAndEmail',
        {
            "email": emailaddress,
            "options": {
                "calculationType": "NBWET",
                "year": 2016,
                "substances": [
                    "NOX",
                    "NH3"
                ]
            },
            "proposed": [{
                "dataType": "GML",
                "contentType": "TEXT",
                "data": inputgml
            }]
        }
    )

    call_connect(json_data)


def service_merge(inputgml, inputgml2, outputfile):
    call_connect(
        get_json(
            'util.merge',
            {
                "data": [{
                    "dataType": "GML",
                    "contentType": "TEXT",
                    "data": inputgml
                }, {
                    "dataType": "GML",
                    "contentType": "TEXT",
                    "data": inputgml2
                }]
            }
        ),
        outputfile
    )


def process_results(json_data):
    # write result part
    json_output = json.loads(json_data)
    if json_data.find("successful") > -1:
        if json_data.find("errors") > -1:
            for error in json_output["result"]["errors"]:
                print('ERROR:', error["code"], "-", error["message"])
                sys.exit(1)
        elif json_data.find("warnings") > -1 and len(json_output["result"]["warnings"]) > 0:	
            print("Call succeeded without errors, but with following warnings:")
            for warning in json_output["result"]["warnings"]:
                print('WARNING:', warning["code"], "-", warning["message"])
        else:
            print("Call succeeded without errors")
    else:
        # we have a JSON-RPC error
        error = json_output["error"]
        print("ERROR:", error["code"], "-", error["message"])
        sys.exit(1)

    return json_output


def read_file_content(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except IOError as e:
        print("Error reading file:", e)
        sys.exit(1)


def call_connect(json_data, outputfile=None):
    try:
        debug("Connecting using websocket...")
        ws = websocket.create_connection(CONNECT_HOST + CONNECT_SERVICE_URL)
    except Exception as e:
        print("Unexpected connection error while trying to establish connection:", e)
        return

    try:
        debug("Trying to send data to service..")
        if DEBUG_ENABLED:
            debug("Writing input data send to service to:" + DEBUG_INPUT_FILE)
            fileout = open(DEBUG_INPUT_FILE, "w+")
            fileout.write(json.dumps(json_data))

        ws.send(json.dumps(json_data))
        debug("Send! Trying to receive data from service..")
        result = ws.recv()
        debug("Done receiving!")

        if DEBUG_ENABLED:
            debug("Writing full result from service to:" + DEBUG_RESULT_FILE)
            fileout = open(DEBUG_RESULT_FILE, "w+")
            fileout.write(str(result))

        json_output = process_results(result)
    except Exception as e:
        print("Unexpected connection error:", e)
        return False
    finally:
        debug("Closing connection")
        ws.close()

    if json_output and outputfile:
        outputdata = json_output["result"]["data"].encode("UTF-8")
        if json_output["result"]["contentType"]:
            print("Result has contentType:", json_output["result"]["contentType"]);
            if json_output["result"]["contentType"] == 'BASE64':
                outputdata = base64.standard_b64decode(outputdata)

        print("Writing content to:", outputfile)
        fileout = open(outputfile, "wb+")
        fileout.write(outputdata)


def usage(errormessage=None):
    if errormessage:
        print("ERROR:", errormessage)
        print()

    print("Usage:")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_VALIDATE + " <input GML file>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CONVERT + " <input GML file> <output GML file>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CALCULATEANDEMAIL + " <input GML file> <email address>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CALCULATEREPORTANDEMAIL +
          " <input GML file> <email address>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_MERGE +
          " <input GML file 1> <input GML file 2> <output GML file>")
    print()
    print()
    print("-d, --debug")
    print("\trun in debug mode. Writes debug lines and the full result JSON")
    print("-h, --help")
    print("\tshow this help text")
    print()
    print()
    print("Actions:")
    print("- " + COMMAND_VALIDATE + ":", '\t\t\t', "Validate the GML file")
    print("- " + COMMAND_CONVERT + ":", '\t\t\t', "Convert GML file to the latest version")
    print("- " + COMMAND_CALCULATEANDEMAIL + ":", '\t\t', "Import and calculate the GML and email the results")
    print("- " + COMMAND_CALCULATEREPORTANDEMAIL + ":", '\t', "Import and produce a NBWET PDF and email the results")
    print("- " + COMMAND_MERGE + ":", '\t\t\t',
          "Merge given GML files and return single GML containing the highest depositions of the two")

    if errormessage:
        sys.exit(1)
    else:
        sys.exit(0)


def main(argv):
    try:
        opts, remainder = getopt.getopt(argv, 'hd', ['help', 'debug'])
    except getopt.GetoptError as err:
        print("Invalid argument(s):", str(err))
        usage(1)

    inputgml = None
    inputgml2 = None
    email_address = None
    outputfile = None

    needs_input_file = True
    needs_input_file2 = False
    needs_output_file = False
    needs_email_address = False

    for opt, arg in opts:
        if opt == '-d':
            global DEBUG_ENABLED
            DEBUG_ENABLED = True
        else:
            usage()

    if len(remainder) > 0:
        command_to_execute = remainder[0]
        # By default we expect the command followed by the input GML file
        amount_of_args_expected = 2

        # Check if the command given is valid
        if not any(x == command_to_execute for x in ALL_COMMANDS):
            usage("Command not recognized")

        # Let's determine which and how much arguments we expect, default is specified above
        if command_to_execute == COMMAND_CONVERT:
            needs_output_file = True
            amount_of_args_expected = 3
        elif command_to_execute == COMMAND_CALCULATEANDEMAIL:
            needs_email_address = True
            amount_of_args_expected = 3
        elif command_to_execute == COMMAND_CALCULATEREPORTANDEMAIL:
            needs_email_address = True
            amount_of_args_expected = 3
        elif command_to_execute == COMMAND_MERGE:
            needs_input_file2 = True
            needs_output_file = True
            amount_of_args_expected = 4

        if len(remainder) != amount_of_args_expected:
            usage("Unexpected amount of args received")

        outputfile_argument_position = 1
        if needs_input_file:
            inputgml = read_file_content(remainder[1])
            outputfile_argument_position += 1
        if needs_input_file2:
            inputgml2 = read_file_content(remainder[2])
            outputfile_argument_position += 1
        if needs_email_address:
            email_address = remainder[2]
        if needs_output_file:
            outputfile = remainder[outputfile_argument_position]

        if command_to_execute == COMMAND_CONVERT:
            service_convert2gml(inputgml, outputfile)
        elif command_to_execute == COMMAND_VALIDATE:
            service_validate(inputgml)
        elif command_to_execute == COMMAND_CALCULATEANDEMAIL:
            service_calculate_and_email(inputgml, email_address)
        elif command_to_execute == COMMAND_CALCULATEREPORTANDEMAIL:
            service_calculate_report_and_email(inputgml, email_address)
        elif command_to_execute == COMMAND_MERGE:
            service_merge(inputgml, inputgml2, outputfile)

    else:
        usage("No command specified")


if __name__ == '__main__':
    main(sys.argv[1:])
