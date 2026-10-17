def assert_error(response, code):
    assert response["status"] == "ERROR", response
    assert response["code"] == code, response
