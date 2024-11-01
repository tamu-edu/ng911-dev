#!/bin/bash
# --------------------------------------------------------------------
#
# Version: 	010.3d.2.0.7
# Date:		20241031
#
# REQUIREMENTS:
# - installed SIPp
# - installed bash, grep, awk, cut, tr
# - NG911 repository cloned
# - script is started from it's location in repository
# 
# USAGE:
# sudo bash TC_ESRP_001.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script runs 2 separate SIPp with following scenario files:
# - SIP SUBSCRIBE_ServiceState.xml
# - SIP SUBSCRIBE_QueueState.xml
# From received SIP NOTIFY message bodies "state" is being extracted
# 
# After simulating change of ServiceState to 'Down' (manually by tester)
# script runs SIPp once again to check is ServiceState has changed
# and QueueState changed its status appropriately
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
# 
SIPP="/usr/local/src/sipp-3.6.1/sipp"

ServiceState_SIPP_SCENARIO_PATH="../../Test_files/SIPp_scenarios/SIP_SUBSCRIBE"
ServiceState_SIPP_SCENARIO_FILE="SIP_SUBSCRIBE_ServiceState.xml"

QueueState_SIPP_SCENARIO_PATH="../../Test_files/SIPp_scenarios/SIP_SUBSCRIBE"
QueueState_SIPP_SCENARIO_FILE="SIP_SUBSCRIBE_QueueState.xml"

SIP_LOCAL_IP_ADDRESS=""
SIP_LOCAL_PORT=""
SIP_REMOTE_IP_ADDRESS=""
SIP_REMOTE_PORT=""

SIP_RECEIVE_TIMEOUT="30"

MANUAL_ACTIONS_TIMEOUT="30"
#
# --------------------------------------------------------------------
# TEST 1 - ServiceState change from 'Normal' to 'Down'
# TEST 2 - QueueState change from 'Active' to 'Inactive' after change of ServiceState
#
TESTS=(
	"error" 
	"error"
)

ServiceState_SIPP_SCENARIO_NAME=`echo $ServiceState_SIPP_SCENARIO_FILE | cut -d . -f 1`
QueueState_SIPP_SCENARIO_NAME=`echo $QueueState_SIPP_SCENARIO_FILE | cut -d . -f 1`


function subscribe_and_get_status_parameter(){
	file_path=$1
	scenario_file=$2
	parameter=$3
	PID=$($SIPP -t t5 -sf "$file_path/$scenario_file" -i "$SIP_LOCAL_IP_ADDRESS:$SIP_LOCAL_PORT" "$SIP_REMOTE_IP_ADDRESS:$SIP_REMOTE_PORT" -trace_msg -timeout "$SIP_RECEIVE_TIMEOUT" -max_recv_loops 1 -m 3 -bg & >> /dev/null)
	sleep $SIP_RECEIVE_TIMEOUT
	PID=`echo $PID | sed 's/.*\[\(.*\)\].*/\1/'`
	SCENARIO_NAME=`echo $scenario_file | cut -d . -f 1`
	MSG_FILE=`ls "$SCENARIO_NAME"_*_messages.log`
	if [[ "$MSG_FILE" = "" ]]; then
		echo "ERROR"
		exit 1
	fi
	STATE=`cat $MSG_FILE | awk '/NOTIFY/ {found=1} found && /'$parameter':/ {print; exit}' | awk '{print $2}' | sed 's/.*\"\(.*\)\".*/\1/'`
	echo $STATE
	if [[ `ps aux | awk '{print $2}' | grep $PID | tr -d ' '` != "" ]]; then
		kill -9 $PID > /dev/null
	fi
	rm $MSG_FILE
}


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
	echo "TEST 1 ( ${TESTS[0]} ) - ServiceState change from 'Normal' to 'Down'"
	echo "TEST 2 ( ${TESTS[1]} ) - QueueState change from 'Active' to 'Inactive' after change of ServiceState"
	echo
	echo "-------"
	echo
	FINAL_VERDICT=$(check_final_verdict)
	echo "Test case $0 finished. Verdict: $FINAL_VERDICT"
	if [[ "$FINAL_VERDICT" = "error" ]]; then
		exit 1
	fi
	exit 0
}


function with_ServiceState_Normal(){
	echo
	echo -n "Subscribing for ServiceState (timeout=$SIP_RECEIVE_TIMEOUT s) ... "
	ServiceState_DEFAULT=$(subscribe_and_get_status_parameter $ServiceState_SIPP_SCENARIO_PATH $ServiceState_SIPP_SCENARIO_FILE '"state"')
	if [[ "$ServiceState_DEFAULT" != "Normal" ]]; then
		echo "ERROR"
		echo "ERROR - ServiceState should be 'Normal' before starting test!"
		echo
		print_results_and_exit
	fi
	echo -n "DONE"
	echo " (ServiceState=$ServiceState_DEFAULT)"
}


function with_QueueState_Active(){
	echo -n "Subscribing for QueueState (timeout=$SIP_RECEIVE_TIMEOUT s) ... "
	QueueState_DEFAULT=$(subscribe_and_get_status_parameter $QueueState_SIPP_SCENARIO_PATH $QueueState_SIPP_SCENARIO_FILE '"state"')
	if [[ "$QueueState_DEFAULT" != "Active" ]]; then
		echo "ERROR"
		echo "ERROR - QueueState should be 'Active' before starting test!"
		echo
		print_results_and_exit
	fi
	echo -n "DONE"
	echo " (QueueState=$QueueState_DEFAULT)"
}


function when_tester_simulates_change_of_ServiceState_to_Down(){
	echo 
	echo "-------"
	echo "Please simulate change of serviceState to 'Down' manually"
	echo "Script will wait for configured MANUAL_ACTIONS_TIMEOUT=$MANUAL_ACTIONS_TIMEOUT s ..."
	echo "-------"
	echo
	sleep $MANUAL_ACTIONS_TIMEOUT
}


function then_ServiceState_is_Down(){
	echo -n "Subscribing for current ServiceState (timeout=$SIP_RECEIVE_TIMEOUT s) ... "
	ServiceState_CURRENT=$(subscribe_and_get_status_parameter $ServiceState_SIPP_SCENARIO_PATH $ServiceState_SIPP_SCENARIO_FILE '"state"')
	if [[ "$ServiceState_CURRENT" = "" ]]; then
		TESTS[0]="error"
		echo -n "ERROR"
	elif [[ "$ServiceState_CURRENT" = "Down" || "$ServiceState_CURRENT" = "GoingDown" ]]; then
		TESTS[0]="pass"
		echo -n "DONE"
	else
		TESTS[0]="fail"
		echo -n "DONE"
	fi
	echo " (ServiceState=$ServiceState_CURRENT)"
}


function then_QueueState_is_Inactive(){
	echo -n "Subscribing for current QueueState (timeout=$SIP_RECEIVE_TIMEOUT s) ... "
	QueueState_CURRENT=$(subscribe_and_get_status_parameter $QueueState_SIPP_SCENARIO_PATH $QueueState_SIPP_SCENARIO_FILE '"state"')
	if [[ "$QueueState_CURRENT" = "" ]]; then
		TESTS[1]="error"
		echo -n "ERROR"
	elif [[ "$QueueState_CURRENT" = "Inactive" && "${TESTS[0]}" = "pass" ]]; then
		TESTS[1]="pass"
		echo -n "DONE"
	else
		TESTS[1]="fail"
		echo -n "DONE"
	fi
	echo " (QueueState=$QueueState_CURRENT)"
}

# --------------------------------------------------------------------

echo
echo $0
echo "-------"
echo "Begining at" `date`

with_ServiceState_Normal
with_QueueState_Active

when_tester_simulates_change_of_ServiceState_to_Down

then_ServiceState_is_Down
then_QueueState_is_Inactive

print_results_and_exit
