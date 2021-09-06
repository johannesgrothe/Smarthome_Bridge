import pytest


LOREM_IPSUM = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut " \
              "labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores " \
              "et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem " \
              "ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore " \
              "et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea " \
              "rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet."

LOREM_IPSUM_SHORT = "Lorem ipsum, digga"


@pytest.fixture
def f_payload_big() -> dict:
    return {"data": 12345,
            "list": [1, 2, 3, 4, 5],
            "strings":
                {
                    "lorem_long": LOREM_IPSUM,
                    "lorem_short": LOREM_IPSUM_SHORT
                }
            }


@pytest.fixture
def f_payload_small() -> dict:
    return {"lorem": LOREM_IPSUM_SHORT}
