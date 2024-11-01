#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.1
# Date:		20241028
#
# REQUIREMENTS:
# - installed SIPp, openssl
# - installed bash, grep, awk, cut, tr, sed
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_ESRP_003.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# As a first step simple HTTPS server is started in background.
# In second step script runs two types of SIPp processes:
# - receiver - running in background waits for SIP INVITE from ESRP
# - sender - sends SIP INVITE to ESRP
#
# After sending SIP INVITE to ESRP script waits for:
# - HTTP LoST request - then 200 OK response is sent back with XML from HTTP_RECEIVER_SCENARIO_FILE
# - SIP INVITE - with header fields added by ESRP
#
# Then test process include followning checklist for received SIP INVITE from ESRP:
# 
# - adding Via header field specifying ESRP
# - adding Route header field with queue URI received from ECRF (script's HTTP server)
# - added Route header field contains lr parameter
# - adding Emergency Call ID
# - adding Incident Tracking ID
# - SIP INVITE exiting ESRP contains original header fields
#
# OUTPUT:
# - print of test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 

SIPP="/usr/local/src/sipp-3.6.1/sipp"

SIP_SENDER_LOCAL_IP_ADDRESS=""
SIP_SENDER_LOCAL_PORT=""
SIP_SENDER_REMOTE_IP_ADDRESS=""
SIP_SENDER_REMOTE_PORT=""

SIP_SENDER_CERT_FILE=""
SIP_SENDER_KEY_FILE=""

SIP_RECEIVER_LOCAL_IP_ADDRESS=""
SIP_RECEIVER_LOCAL_PORT=""
SIP_RECEIVER_REMOTE_IP_ADDRESS=""
SIP_RECEIVER_REMOTE_PORT=""

SIP_RECEIVER_CERT_FILE=""
SIP_RECEIVER_KEY_FILE=""

SIP_SEND_TIMEOUT="2"
SIP_RECEIVE_TIMEOUT="5"

SIP_SENDER_SCENARIOS_PATH="../../Test_files/SIPp_scenarios/SIP_INVITE"

SIP_RECEIVER_SCENARIOS_PATH="../../Test_files/SIPp_scenarios/SIP_RECEIVE"

TEST_SCENARIO_SIP_RECEIVE_FILE="SIP_INVITE_RECEIVE.xml"

HTTP_RECEIVER_LOCAL_IP_ADDRESS=""
HTTP_RECEIVER_LOCAL_PORT=""

HTTP_RECEIVER_SCENARIOS_PATH="../../Test_files/HTTP_messages/HTTP_LoST"

HTTP_RECEIVER_SCENARIO_FILE="findServiceResponse"

HTTP_RECEIVE_TIMEOUT="5"

HTTP_RECEIVER_CERT_FILE=""
HTTP_RECEIVER_KEY_FILE=""
#
# --------------------------------------------------------------------
#

TESTS=()

FILES_GENERATED=()
CURRENT_SCENARIO=""
HTTP_RECEIVER_PID=""


function check_final_verdict(){
	FINAL_VERDICT="pass"
	for TEST in ${TESTS[@]}; do
		if [[ "$TEST" = "error" ]]; then
			FINAL_VERDICT="error"
			break
		fi
		if [[ "$TEST" = "inconc" ]]; then
			FINAL_VERDICT="inconc"
			break
		fi
		if [[ "$TEST" = "fail" ]]; then
			FINAL_VERDICT="fail"
			break
		fi
	done
	echo $FINAL_VERDICT
}


function print_results_and_exit(){
	echo
	echo "Ending at" `date`
	echo
	echo "-- TEST RESULTS --"
	echo
	echo "SIP_INVITE_EMERGENCY_SINGLE.xml"
	echo "TEST 1 ( ${TESTS[0]} ) - adding Via header field specifying ESRP"
	echo "TEST 2 ( ${TESTS[1]} ) - adding Route header field with queue URI received from ECRF"
	echo "TEST 3 ( ${TESTS[2]} ) - added Route header field contains lr parameter"
	echo "TEST 4 ( ${TESTS[3]} ) - adding Emergency Call ID"
	echo "TEST 5 ( ${TESTS[4]} ) - adding Incident Tracking ID"
	echo "TEST 6 ( ${TESTS[5]} ) - SIP INVITE exiting ESRP contains original header fields"
	echo
	echo "-------"
	echo
	FINAL_VERDICT=$(check_final_verdict)
	echo "Test case $0 finished. Verdict: $FINAL_VERDICT"
	for file in ${FILES_GENERATED[@]}; do
		rm $file 2> /dev/null
	done
	if [[ "$FINAL_VERDICT" = "error" ]]; then
		exit 1
	fi
	exit 0
}


function with_scenario_file(){
	scenario=$1
	if [[ `ls $SIP_RECEIVER_SCENARIOS_PATH/$TEST_SCENARIO_SIP_RECEIVE_FILE 2> /dev/null` == "" ]]; then
		echo "ERROR - missing scenario file $TEST_SCENARIO_SIP_RECEIVE_FILE" >&2
		print_results_and_exit
	fi
	if [[ `ls $SIP_SENDER_SCENARIOS_PATH/$scenario 2> /dev/null` == "" ]]; then
		echo "ERROR - missing scenario file $scenario" >&2
		CURRENT_SCENARIO="skip"
	else
		scenario_name=`echo $scenario | cut -d . -f 1`
		CURRENT_SCENARIO=$scenario_name
	fi
}


function start_HTTPS_server(){
	if [[ "$HTTP_RECEIVER_CERT_FILE" = "" || "$HTTP_RECEIVER_KEY_FILE" = "" ]]; then
		openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.pem -days 1 -nodes -subj "/CN=$HTTP_RECEIVER_LOCAL_IP_ADDRESS" 2> /dev/null
	else
		cp $HTTP_RECEIVER_CERT_FILE ./server.pem
		cp $HTTP_RECEIVER_KEY_FILE ./server.key
	fi
	while true; do
		echo -e "HTTP/1.1 200 OK\r\nContent-Type: application/xml\r\nContent-Length: 1167\r\n\r\n$(cat $HTTP_RECEIVER_SCENARIOS_PATH/$HTTP_RECEIVER_SCENARIO_FILE | sed -n  '/<?xml/,/findServiceResponse>/p')\r\n" | \
		openssl s_server -quiet -accept $HTTP_RECEIVER_LOCAL_PORT -cert server.pem -key server.key > http.log 2>&1
	done
}


function with_HTTP_server_started(){
	echo -n "Starting HTTP server process (IP=${HTTP_RECEIVER_LOCAL_IP_ADDRESS}, PORT=${HTTP_RECEIVER_LOCAL_PORT})... "
	start_HTTPS_server > /dev/null 2>&1 & 
	HTTP_RECEIVER_PID=$!
	if [[ $HTTP_RECEIVER_PID != "" ]]; then
		echo "DONE"
	else
		echo "ERROR"
		exit 1
	fi
}


function when_HTTP_scenario_is_sent_and_received_response(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		return 1
	fi
	echo -n "Waiting for HTTP LoST requests from ESRP (timeout=${HTTP_RECEIVE_TIMEOUT}s) ..."
	sleep $HTTP_RECEIVE_TIMEOUT
	echo -n "Stopping HTTP server process (PID=${HTTP_RECEIVER_PID})..."
	kill -9 $HTTP_RECEIVER_PID > /dev/null 2>&1
	echo "DONE"
	echo -n "Stopping Openssl processes ..."
	openssl_pid=`ps aux | grep "openssl" | grep "$HTTP_RECEIVER_LOCAL_PORT" | grep "server.pem" | awk '{print $2}'`
	for openssl in $openssl_pid; do
		kill -9 $openssl > /dev/null 2>&1
	done
	echo "DONE"
	rm server.pem 2> /dev/null
	rm server.key 2> /dev/null
}


function run_sipp_scenario_as_sender_or_receiver(){
	scenario_filename=$1
	#
	# mode
	#
	# 1. sender - runs scenario and kills created SIPp process
	# 2. receiver - runs scenario and prints PID of SIPp running in background
	mode=$2 #sender/receiver

	if [[ $mode = "sender" ]]; then
		if [[ $SIP_SENDER_CERT_FILE = "" ]]; then
			pid=$($SIPP -t t1 -sf "$SIP_SENDER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_SENDER_LOCAL_IP_ADDRESS:$SIP_SENDER_LOCAL_PORT" "$SIP_SENDER_REMOTE_IP_ADDRESS:$SIP_SENDER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 2> /dev/null >> /dev/null )
		else
			pid=$($SIPP -t l1 -tls_cert $SIP_SENDER_CERT_FILE -tls_key $SIP_SENDER_KEY_FILE -sf "$SIP_SENDER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_SENDER_LOCAL_IP_ADDRESS:$SIP_SENDER_LOCAL_PORT" "$SIP_SENDER_REMOTE_IP_ADDRESS:$SIP_SENDER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -tls_version 1.2 -bg & >> /dev/null) 
		fi
	else
		if [[ $SIP_RECEIVER_CERT_FILE = "" ]]; then
			pid=$($SIPP -t t1 -sf "$SIP_RECEIVER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_RECEIVER_LOCAL_IP_ADDRESS:$SIP_RECEIVER_LOCAL_PORT" "$SIP_RECEIVER_REMOTE_IP_ADDRESS:$SIP_RECEIVER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -bg & >> /dev/null)
		else
			pid=$($SIPP -t l1 -tls_cert $SIP_RECEIVER_CERT_FILE -tls_key $SIP_RECEIVER_KEY_FILE -sf "$SIP_RECEIVER_SCENARIOS_PATH/${scenario_filename}" -i "$SIP_RECEIVER_LOCAL_IP_ADDRESS:$SIP_RECEIVER_LOCAL_PORT" "$SIP_RECEIVER_REMOTE_IP_ADDRESS:$SIP_RECEIVER_REMOTE_PORT" -trace_msg -max_recv_loops 1 -m 1 -tls_version 1.2 -bg & >> /dev/null)
		fi
	fi
	pid=`echo $pid | sed 's/.*\[\(.*\)\].*/\1/'`
	scenario_name=`echo $scenario_filename | cut -d . -f 1`
	sip_msg_file=`ls "$scenario_name"_*_messages.log`
	if [[ $mode = "sender" ]]; then
		mv $sip_msg_file "${scenario_name}_sender.log"
	else
		mv $sip_msg_file "${CURRENT_SCENARIO}.log"
		echo "$pid"
	fi
	return 0
}


function when_SIP_scenario_is_sent_and_received_response(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		return 1
	fi
	scenario_name=`echo $CURRENT_SCENARIO | cut -d . -f1`
	echo -n "Starting SIPp receiver process (scenario=${TEST_SCENARIO_SIP_RECEIVE_FILE})..."
	sipp_receiver_pid=`run_sipp_scenario_as_sender_or_receiver ${TEST_SCENARIO_SIP_RECEIVE_FILE} receiver`
	echo "DONE"
	FILES_GENERATED+=("${CURRENT_SCENARIO}.log")
	echo -n "Running SIPp sender process (scenario=${CURRENT_SCENARIO}.xml)..."
	run_sipp_scenario_as_sender_or_receiver ${CURRENT_SCENARIO}.xml sender
	sleep $SIP_SEND_TIMEOUT
	echo "DONE"
	FILES_GENERATED+=("${CURRENT_SCENARIO}_sender.log")
	echo -n "Waiting for SIPp to receive messages and stop (timeout=${SIP_RECEIVE_TIMEOUT}s, scenario=${TEST_SCENARIO_SIP_RECEIVE_FILE})..."
	sleep $SIP_RECEIVE_TIMEOUT
	kill -9 $sipp_receiver_pid 2> /dev/null
	echo "DONE"
}


function then_SIP_INVITE_received_contains_Via_header_field_specifying_ESRP(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	received_Via_header_fields_addresses=`cat ${CURRENT_SCENARIO}.log | grep "Via" | awk '{print $3}'`
	esrp_address_port=`cat ${CURRENT_SCENARIO}.log | grep "From" | cut -d '@' -f2 | cut -d ';' -f1 | cut -d '>' -f1`
	for address_port in $received_Via_header_fields_addresses; do
		address_port=`echo $address_port | cut -d ';' -f1 | tr -d '\n' | tr -d '\r'`
		if [[ "$address_port" = "$esrp_address_port" ]]; then
			TESTS[${#TESTS[@]}-1]="pass"
			return 0
		fi
	done
	TESTS[${#TESTS[@]}-1]="fail"
}


function then_SIP_INVITE_received_contains_Route_header_field_with_queue_URI(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	queue_uri=`cat $HTTP_RECEIVER_SCENARIOS_PATH/$HTTP_RECEIVER_SCENARIO_FILE | grep "sip:" | cut -d '>' -f2 | cut -d '<' -f1 | tr -d '\n' | tr -d '\r'`
	received_queue_uri=`cat ${CURRENT_SCENARIO}.log | grep "Route:" | awk '{print $2}' | cut -d '<' -f2 | cut -d '>' -f1 | tr -d '\n' | tr -d '\r'`
	received_queue_uri=`echo $received_queue_uri | awk -F';' '{print $1}'`
	if [[ $queue_uri != $received_queue_uri ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
	else
		TESTS[${#TESTS[@]}-1]="pass"
	fi
	rm http.log 2> /dev/null
}


function then_SIP_INVITE_received_contains_Route_header_field_containing_lr(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	received_queue_uri=`cat ${CURRENT_SCENARIO}.log | grep "Route:" | cut -d '<' -f2 | cut -d '>' -f1 | tr -d '\n' | tr -d '\r'`
	lr=`echo $received_queue_uri | cut -d ';' -f2 | tr -d ' '`
	if [[ $lr != "lr" ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
	else
		TESTS[${#TESTS[@]}-1]="pass"
	fi
}


function then_SIP_INVITE_received_contains_Emergency_Call_ID(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	call_info_emergency_call_id=`cat ${CURRENT_SCENARIO}.log | grep "Call-Info" | grep -m1 "urn:emergency:uid:callid"`
	id_string=`echo $call_info_emergency_call_id | rev | cut -d ':' -f2 | rev`
	fqdn=`echo $call_info_emergency_call_id | rev | cut -d ':' -f1 | rev | tr -d '\n' | tr -d '\r'`
	if ! [[ "$call_info_emergency_call_id" =~ "urn:emergency:uid:callid" ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	if ! [[ "$id_string" =~ ^[A-Za-z0-9]{10,32}$ ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	if ! [[ "$fqdn" =~ ^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	TESTS[${#TESTS[@]}-1]="pass"
}


function then_SIP_INVITE_received_contains_Incident_Tracking_ID(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	call_info_incident_id=`cat ${CURRENT_SCENARIO}.log | grep "Call-Info" | grep -m1 "urn:emergency:uid:incidentid"`
	id_string=`echo $call_info_incident_id | rev | cut -d ':' -f2 | rev`
	fqdn=`echo $call_info_incident_id | rev | cut -d ':' -f1 | rev | tr -d '\n' | tr -d '\r'`
	if ! [[ "$call_info_incident_id" =~ "urn:emergency:uid:incidentid" ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	if ! [[ "$id_string" =~ ^[A-Za-z0-9]{10,32}$ ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	if ! [[ "$fqdn" =~ ^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
		TESTS[${#TESTS[@]}-1]="fail"
		return 1
	fi
	TESTS[${#TESTS[@]}-1]="pass"
}


SIP_HEADER_FIELDS_CHECK_EXCLUDED=(
	Via
	From
	To
	Call-ID
	Cseq
	Route
	Contact
	Content-Length
)


function then_SIP_INVITE_received_contains_original_header_fields(){
	if [[ $CURRENT_SCENARIO = "skip" ]]; then
		TESTS+=("skip")
		return 1
	else
		TESTS+=("error")
	fi
	sip_invite_read=false
	while IFS= read -r line; do
		if [[ `echo $line | grep 'INVITE '` != "" ]]; then
			sip_invite_read=true
		fi
		if ! [[ "$line" =~ [a-zA-Z0-9] ]]; then
			sip_invite_read=false
		fi
		if $sip_invite_read; then
			for header in ${SIP_HEADER_FIELDS_CHECK_EXCLUDED[@]}; do
				if [[ `echo $line | grep "${header}: "` != "" ]]; then
					continue
				fi
			done
			if [[ `grep -F "$line" ${CURRENT_SCENARIO}.log` != "" ]]; then
				all_fields_found=true
			else
				all_fields_found=false
			fi
		fi
	done < ${CURRENT_SCENARIO}_sender.log
	if $all_fields_found; then
		TESTS[${#TESTS[@]}-1]="pass"
	else
		TESTS[${#TESTS[@]}-1]="fail"
	fi
	for line in ${lines[@]}; do
		echo $line
	done
}


# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`
echo

with_scenario_file "SIP_INVITE_EMERGENCY_SINGLE.xml"
with_HTTP_server_started
when_SIP_scenario_is_sent_and_received_response
when_HTTP_scenario_is_sent_and_received_response
then_SIP_INVITE_received_contains_Via_header_field_specifying_ESRP
then_SIP_INVITE_received_contains_Route_header_field_with_queue_URI
then_SIP_INVITE_received_contains_Route_header_field_containing_lr
then_SIP_INVITE_received_contains_Emergency_Call_ID
then_SIP_INVITE_received_contains_Incident_Tracking_ID
then_SIP_INVITE_received_contains_original_header_fields

print_results_and_exit
