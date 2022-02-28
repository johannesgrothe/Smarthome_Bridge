import datetime
from datetime import datetime, timedelta
from test_helpers.timing_organizer import TimingOrganizer


_legal_delta = 15


def time_test(ms: int):
    t_start = datetime.now()
    TimingOrganizer.delay(ms)
    t_end = datetime.now()
    deviation = ((t_end - t_start) - timedelta(milliseconds=ms)).microseconds / 1000
    print(f"Test finished with deviation of {round(deviation, 2)}ms")
    assert abs(deviation) < _legal_delta


def test_time_organizer():
    print()
    time_test(10)
    time_test(400)
    time_test(1000)
    time_test(3422)
    time_test(25471)
