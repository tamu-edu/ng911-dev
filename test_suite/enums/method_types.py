from enum import Enum


class SIPMethodEnum(str, Enum):
    """
    Enum for SIP Methods.
    """
    INVITE = "INVITE"  # SIP Method for initiating a call
    ACK = "ACK"  # Acknowledges final response to an INVITE
    BYE = "BYE"  # Terminates a session
    CANCEL = "CANCEL"  # Cancels a pending request
    REGISTER = "REGISTER"  # Registers a user agent to a server
    OPTIONS = "OPTIONS"  # Queries capabilities of a server
    INFO = "INFO"  # Sends mid-session information
    PRACK = "PRACK"  # Provisional acknowledgment
    SUBSCRIBE = "SUBSCRIBE"  # Subscribes to an event
    NOTIFY = "NOTIFY"  # Notifies subscriber of an event
    PUBLISH = "PUBLISH"  # Publishes an event to the server
    REFER = "REFER"  # Asks the recipient to issue a SIP request
    MESSAGE = "MESSAGE"  # Transports instant messages
    UPDATE = "UPDATE"  # Modifies the state of a session without changing the state of the dialog
    OK = "OK"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class HTTPMethodEnum(str, Enum):
    """
    Enum for HTTP Methods.
    """
    GET = "GET"  # Request to retrieve data from the server
    POST = "POST"  # Request to send data to the server
    PUT = "PUT"  # Request to update a resource on the server
    DELETE = "DELETE"  # Request to delete a resource on the server
    HEAD = "HEAD"  # Request for headers, identical to GET but without the response body
    OPTIONS = "OPTIONS"  # Request to describe the communication options for the target resource
    PATCH = "PATCH"  # Request to apply partial modifications to a resource
    CONNECT = "CONNECT"  # Establishes a tunnel to the server identified by the target resource
    TRACE = "TRACE"  # Performs a message loop-back test along the path to the target resource

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class HTTPStatusCodeEnum(int, Enum):
    """
    Enum for HTTP Response Status Codes.
    """
    # Informational responses (100–199)
    CONTINUE = 100  # Request received, please continue
    SWITCHING_PROTOCOLS = 101  # Switching to new protocol; obey Upgrade header
    PROCESSING = 102  # WebDAV: Processing the request, no response yet
    EARLY_HINTS = 103  # Early hints to preload resources

    # Successful responses (200–299)
    OK = 200  # The request has succeeded
    CREATED = 201  # The request has succeeded and a new resource has been created
    ACCEPTED = 202  # The request has been accepted for processing
    NON_AUTHORITATIVE_INFORMATION = 203  # The request succeeded, but meta-information is from another source
    NO_CONTENT = 204  # The server successfully processed the request, but is not returning any content
    RESET_CONTENT = 205  # The server processed the request, reset the document view
    PARTIAL_CONTENT = 206  # The server delivered partial response

    # Redirection messages (300–399)
    MULTIPLE_CHOICES = 300  # Multiple options for the resource
    MOVED_PERMANENTLY = 301  # The resource has been permanently moved
    FOUND = 302  # Temporary redirection
    SEE_OTHER = 303  # Resource available at another URI
    NOT_MODIFIED = 304  # Resource has not been modified since last request
    TEMPORARY_REDIRECT = 307  # Request should be repeated at another URI
    PERMANENT_REDIRECT = 308  # Permanent redirection to another URI

    # Client error responses (400–499)
    BAD_REQUEST = 400  # The server could not understand the request
    UNAUTHORIZED = 401  # Authentication is required and has failed
    FORBIDDEN = 403  # The client does not have access rights to the content
    NOT_FOUND = 404  # The server cannot find the requested resource
    METHOD_NOT_ALLOWED = 405  # The HTTP method is not allowed for the resource
    NOT_ACCEPTABLE = 406  # The server cannot produce a response matching the list of acceptable values
    REQUEST_TIMEOUT = 408  # The server timed out waiting for the request
    CONFLICT = 409  # The request conflicts with the current state of the server

    # Server error responses (500–599)
    INTERNAL_SERVER_ERROR = 500  # The server encountered an error
    NOT_IMPLEMENTED = 501  # The server does not support the request
    BAD_GATEWAY = 502  # The server received an invalid response from the upstream server
    SERVICE_UNAVAILABLE = 503  # The server is not ready to handle the request
    GATEWAY_TIMEOUT = 504  # The server is acting as a gateway and cannot get a response in time
    HTTP_VERSION_NOT_SUPPORTED = 505  # The server does not support the HTTP protocol version

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class SIPStatusCodeEnum(int, Enum):
    """
    Enum for SIP Response Status Codes.
    """

    # Provisional responses (100–199)
    TRYING = 100
    RINGING = 180
    QUEUED = 182
    SESSION_PROGRESS = 183

    # Successful responses (200–299)
    OK = 200
    ACCEPTED = 202
    MOVED_TEMPORARILY = 302

    # Redirection responses (300–399)
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    USE_PROXY = 305
    ALTERNATIVE_SERVICE = 380

    # Client failure responses (400–499)
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    REQUEST_ENTITY_TOO_LARGE = 413
    REQUEST_URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    PARAMETER_ERROR = 420
    BAD_EXTENSION = 421
    TEMPORARILY_UNAVAILABLE = 480
    CALL_OR_TRANSACTION_DOES_NOT_EXIST = 481
    LOOP_DETECTED = 482
    TOO_MANY_HOPS = 483
    ADDRESS_INCOMPLETE = 484
    AMBIGUOUS = 485
    BUSY_HERE = 486
    REQUEST_TERMINATED = 487
    NOT_ACCEPTABLE_HERE = 488
    REQUEST_PENDING = 491
    UNDECIPHERABLE = 493

    # Server failure responses (500–599)
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    VERSION_NOT_SUPPORTED = 505
    MESSAGE_TOO_LARGE = 513
    SESSION_NOT_FOUND = 580

    # Global failure responses (600–699)
    BUSY_EVERYWHERE = 600
    DECLINE = 603
    DOES_NOT_EXIST_ANYWHERE = 604
    NOT_ACCEPTABLE_ANYWHERE = 606

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
