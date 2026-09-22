#!/bin/bash
# --------------------------------------------------------------------
#
# Version:      0.1
# Date:         20240724
#
# REQUIREMENTS:
# - installed curl
# - installed bash, ps, tr, date, touch, ls, rm, grep, awk, sed, head
# - NG911 repository cloned
# - script is started from it's location in repository
#
# USAGE:
# sudo bash script_LIS_001.sh
#
# CONFIGURATION:
# - all parameters to be set in CONFIG section
#
# DESCRIPTION:
# Script runs wget commands with LIS lookups against predefined DIDs
# which are converted into Geolocation formatted URLs and tested
# against known good values.
#
# OUTPUT:
# - print of detailed test results
#
# --------------------------------------------------------------------
#
# CONFIG
#
#
TEST_NAME="foo"
TEST_VERDICT="pass"
LIS_REQUEST_TYPE="https"
LIS_FQDN="lis.demo.gridgears.io"
POINT_DID="+19798451200"
POINT_LAT="30.609969"
POINT_LONG="-96.340449"
AREA_DID="+19798451201"
AREA_LAT="30.605485"
AREA_LONG="-96.341423"
AREA_RADIUS="30.0"
FAIL_DID="+19798459999"

echo
echo
echo
echo TC_LIS_001 test script..
echo
echo "------------------------------------------------------------------------------"
echo "Begining at" `date`

#LOG_FILE=`ps -ef | awk '/'${0##*/}'/{ print $2 }' | head -1`.log
LOG_FILE=`date +"%Y%m%d%H%M%S%N"`.log
echo -n " - Creating temporary log file ${LOG_FILE}: "

echo foo > ${LOG_FILE}
CHECK_LOG=`ls ${LOG_FILE}`

if [[ "$CHECK_LOG" != "" ]]; then
        echo "SUCCESS"
else
        echo "FAILED"
        echo
        echo "Test case ${TEST_NAME} finished. Verdict: error"
        exit 1
fi
echo "------------------------------------------------------------------------------"

echo
echo "Testing LIS with calls originating from ${POINT_DID} (for point ${POINT_LAT}, ${POINT_LONG})"
curl -X POST "https://lis.demo.gridgears.io?x-api-key=0fc1d6fb44de486580fbc6819eb081e7" -d '<?xml version="1.0" ?><held:locationRequest xmlns:held="urn:ietf:params:xml:ns:geopriv:held">  <held:locationType exac
t="false">locationURI</held:locationType>  <device xmlns="urn:ietf:params:xml:ns:geopriv:held:id">  <uri>tel:'${POINT_DID}'</uri>  </device>  </held:locationRequest>' > $LOG_FILE 2> /dev/null
echo " - Querying for locationURI (point): SUCCESS"

echo -n " - Parsing log file for \"locationURI\": "

URI=`cat ${LOG_FILE} | grep locationURI | sed -e 's/<[^>]*>//g' | tr -d ' '`

if [[ "$URI" != "" ]]; then
        echo "SUCCESS"
else
        echo "FAILED"
        echo
        echo "Test case ${TEST_NAME} finished. Verdict: error"
        exit 1
fi

echo " - Querying location from ${URI}"
curl -X POST "${URI}" -d "<locationRequest xmlns=\"urn:ietf:params:xml:ns:geopriv:held\" responseTime=\"emergencyRouting\"></locationRequest>" > $LOG_FILE 2> /dev/null

LIS_POINT=`cat ${LOG_FILE} | awk -F"<pos>|</pos>" '{print $2}' | tr -d '\n'`
LIS_POINT_LAT=`echo ${LIS_POINT} | awk '{print $1}'`
LIS_POINT_LONG=`echo ${LIS_POINT} | awk '{print $2}'`

echo " - Provided location from LIS: '${LIS_POINT_LAT} ${LIS_POINT_LONG}'"

if [ ${POINT_LAT} == ${LIS_POINT_LAT} ] && [ ${POINT_LONG} == ${LIS_POINT_LONG} ] ; then
        echo " - Location matches!"
else
        echo " - Location does not match!   ---RESULT = FAILURE---"
        TEST_VERDICT="fail"
fi




echo
echo "Testing LIS with calls originating from ${AREA_DID} (for area ${AREA_LAT}, ${AREA_LONG} radius: ${AREA_RADIUS})"
curl -X POST "https://lis.demo.gridgears.io?x-api-key=0fc1d6fb44de486580fbc6819eb081e7" -d '<?xml version="1.0" ?><held:locationRequest xmlns:held="urn:ietf:params:xml:ns:geopriv:held">  <held:locationType exac
t="false">locationURI</held:locationType>  <device xmlns="urn:ietf:params:xml:ns:geopriv:held:id">  <uri>tel:'${AREA_DID}'</uri>  </device>  </held:locationRequest>' > $LOG_FILE 2> /dev/null
echo " - Querying for locationURI (area): SUCCESS"

echo -n " - Parsing log file for \"locationURI\": "

URI=`cat ${LOG_FILE} | grep locationURI | sed -e 's/<[^>]*>//g' | tr -d ' '`

if [[ "$URI" != "" ]]; then
        echo "SUCCESS"
else
        echo "FAILED"
        echo
        echo "Test case ${TEST_NAME} finished. Verdict: error"
        exit 1
fi

echo " - Querying location from ${URI}"
curl -X POST "${URI}" -d "<locationRequest xmlns=\"urn:ietf:params:xml:ns:geopriv:held\" responseTime=\"emergencyRouting\"></locationRequest>" > $LOG_FILE 2> /dev/null

LIS_AREA=`cat ${LOG_FILE} | awk -F"<gml:pos>|</gml:pos>" '{print $2}' | tr -d '\n'`
LIS_AREA_LAT=`echo ${LIS_AREA} | awk '{print $1}'`
LIS_AREA_LONG=`echo ${LIS_AREA} | awk '{print $2}'`
LIS_AREA_RADIUS=`cat ${LOG_FILE} | awk -F"<gs:radius|</gs:radius" '{print $2}' | awk -F">" '{print $2}' | tr -d '\n'`

echo " - Provided location from LIS: '${LIS_AREA_LAT} ${LIS_AREA_LONG} radius: ${LIS_AREA_RADIUS}'"

if [ ${AREA_LAT} == ${LIS_AREA_LAT} ] && [ ${AREA_LONG} == ${LIS_AREA_LONG} ] && [ ${AREA_RADIUS} == ${LIS_AREA_RADIUS} ] ; then
        echo " - Location matches!"
else
        echo " - Location and/or radius does not match!   ---RESULT = FAILURE---"
        TEST_VERDICT="fail"
fi




echo
echo "Testing LIS with calls originating from ${FAIL_DID} (which is designed to fail)"
curl -X POST "https://lis.demo.gridgears.io?x-api-key=0fc1d6fb44de486580fbc6819eb081e7" -d '<?xml version="1.0" ?><held:locationRequest xmlns:held="urn:ietf:params:xml:ns:geopriv:held">  <held:locationType exac
t="false">locationURI</held:locationType>  <device xmlns="urn:ietf:params:xml:ns:geopriv:held:id">  <uri>tel:'${FAIL_DID}'</uri>  </device>  </held:locationRequest>' > $LOG_FILE 2> /dev/null
echo " - Querying for locationURI: SUCCESS"

echo " - Parsing log file for \"error\" message(s)"

ERROR_MSG=`cat ${LOG_FILE} | grep error`

if [[ "$ERROR_MSG" != "" ]]; then
        echo " - Error message(s) found in returned data!"
else
        echo " - Error message(s) not found in returned data!   ---RESULT = FAILURE---"
        TEST_VERDICT="fail"
fi



echo
echo "------------------------------------------------------------------------------"
echo "Ending at" `date`
#echo
#echo "CURRENT LOG_FILE"
#echo "--------"
#cat $LOG_FILE
#echo
echo -n " - Removing temporary log file ${LOG_FILE}: "
rm -rf $LOG_FILE

CHECK_LOG=`ls ${LOG_FILE} 2> /dev/null`

if [[ "$CHECK_LOG" != "" ]]; then
        echo "FAILURE"
else
        echo "SUCCESS"
fi

echo "------------------------------------------------------------------------------"
echo
echo
echo
echo "RESULTS"
echo "-------"
echo "Test case ${TEST_NAME} finished. Verdict: ${TEST_VERDICT}"
echo

#echo
#echo "CURRENT LOG_FILE"
#echo "--------"
#cat $LOG_FILE
#echo

rm -rf $LOG_FILE
exit 0
