def is_both_client_and_server_hello_present(client_hello, server_hello):
    """
    Validates that both TLS Client Hello and Server Hello cipher suite lists were captured.

    :param client_hello: List of cipher suite strings from the Client Hello message.
    :param server_hello: List of cipher suite strings from the Server Hello message.
    :return: "PASSED" if both lists are present and non-empty, otherwise a "FAILED" error string.
    """
    not_found_err = "FAILED -> {} hello not found"
    try:
        assert client_hello is not None, not_found_err.format("Client")
        assert server_hello is not None, not_found_err.format("Server")
        assert client_hello != [], not_found_err.format("Client")
        assert server_hello != [], not_found_err.format("Server")
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_cipher_suites_hello_has_sha_256(hello_list):
    """
    Validates that the given cipher suite list contains at least one SHA-256 entry.

    :param hello_list: List of cipher suite strings extracted from a Client Hello message.
    :return: "PASSED" if a SHA-256 cipher suite is found, otherwise a "FAILED" error string.
    """
    sha_256_found = False
    try:
        assert hello_list is not None, "FAILED -> Cipher Suites cannot be None"
        assert hello_list != [], "FAILED -> Cipher Suites list cannot be empty"
        for item in hello_list:
            if "sha256" in item.lower():
                sha_256_found = True
                break
        assert sha_256_found, "FAILED -> Cipher Suites list does not contain SHA 256"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_server_hello_contain_sha_256_from_client_hello(client_hello, server_hello):
    """
    Validates that every cipher suite selected by the Server Hello is also present
    in the Client Hello cipher suite list.

    Ensures the server did not negotiate a cipher suite that the client did not advertise.

    :param client_hello: List of cipher suite strings from the Client Hello message.
    :param server_hello: List of cipher suite strings from the Server Hello message.
    :return: "PASSED" if all server suites are present in the client list,
             otherwise a "FAILED" error string identifying the mismatched suite.
    """
    not_found_err = "FAILED -> {} hello not found"
    try:
        assert client_hello is not None, not_found_err.format("Client")
        assert server_hello is not None, not_found_err.format("Server")
        assert client_hello != [], not_found_err.format("Client")
        assert server_hello != [], not_found_err.format("Server")

        for server_hello_item in server_hello:
            assert server_hello_item in client_hello, (
                f"FAILED -> Server Cipher suite value - {server_hello_item} is not present in "
                f"Client Cipher Suite list: {str(client_hello)}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)
