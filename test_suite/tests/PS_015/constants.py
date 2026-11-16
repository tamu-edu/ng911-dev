NOT_RUN = "NOT RUN -> No stimulus message found."
NO_PS_RESPONSE = "FAILED -> No Policy Store response found."
POST_SUCCESS_VARIATIONS = (1,)
POST_ERROR_VARIATIONS = (2, 3, 6, 7, 8)
PUT_ERROR_VARIATIONS = (4, 5, 9, 10, 11)

VARIATIONS = {
    "HTTP_POST_with_correct_policy": 1,
    "HTTP_POST_with_multiple_timeStart_values": 2,
    "HTTP_POST_with_multiple_timeEnd_values": 3,
    "HTTP_PUT_with_multiple_timeStart_values": 4,
    "HTTP_PUT_with_multiple_timeEnd_values": 5,
    "HTTP_POST_with_equal_timeStart_and_timeEnd_values": 6,
    "HTTP_POST_with_timeStart_greater_than_timeEnd": 7,
    "HTTP_POST_with_timeStart_empty_and_timeEnd_is_midnight": 8,
    "HTTP_PUT_with_equal_timeStart_and_timeEnd_values": 9,
    "HTTP_PUT_with_timeStart_greater_than_timeEnd": 10,
    "HTTP_PUT_with_timeStart_empty_and_timeEnd_is_midnight": 11,
}
