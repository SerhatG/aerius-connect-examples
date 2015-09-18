#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Dit voorbeeld script verstuurt de GML naar AERIUS connect en geeft terug of validatie goed was of de fouten.
"""
import json
import time
import os
import pprint
import sys
import getopt
import websocket

AERIUS_SERVER = "ws://connect.aerius.nl"
debug = False

def convert2GML(inputfile):
	f = open(inputfile,'r')
	data = f.read()
	f.close
	# create json text object
	json_text = """
	{
		"jsonrpc":"2.0",
		"id":0,
		"method":"validation.validate",
		"params":{
			"dataType":"GML",
			"contentType":"TEXT",
			"data":""
		}
	}
	"""
	# replace paramaters
	json_data = json.loads(json_text)
	json_data["id"] = int(time.time() * 1000) #create unique id
	json_data["params"]["data"] = data

	try:
		ws = websocket.create_connection(AERIUS_SERVER + "/connect/2/services")
	except Exception as e:
		print ("Unexpected connection error:", e)
		return

	try:
		#sending data
		ws.send(json.dumps(json_data))
		result = ws.recv()
		ws.close()
		if debug:
			print ("DEBUG json data send:")
			print (json.dumps(json_data))
			print ("DEBUG json data recieved:")
			print (result)
		# write result part
		if result.find("successful") > -1:
			json_output = json.loads(result)
			if (result.find("errors") > -1):
				for error in json_output["result"]["errors"]:
					print (error["errorCode"] + " - " + error["description"])
			else:
				print ("gml validated correctly!")
		else: 
			# we have JSON-RPC error
			json_output = json.loads(result)
			error = json_output["error"]
			print ("error: " + str(error["code"]) + " - " + error["message"])

	except Exception as e:
		print ("Unexpected result error:", e)
		
	finally:
		ws.close()

	return

def main(argv):
	opts, args = getopt.getopt(argv,"hdi:o:",["ifile=","ofile="])
	for opt, arg in opts:
		if opt == '-h':
			print('AERIUS_validate.py [-d] -i <gml file>')
			sys.exit()
		elif opt == '-d':
			global debug
			debug = True
		elif opt in ("-i", "--ifile"):
			inputfile = arg

	print("reading ", inputfile)
	convert2GML(inputfile)

if __name__ == "__main__":
   main(sys.argv[1:])
