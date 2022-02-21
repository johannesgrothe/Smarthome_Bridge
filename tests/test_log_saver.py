from test_helpers.log_saver import LogSaver, LogLevel


def test_log_saver():
    saver = LogSaver()
    saver.add_log_string("[I][client_main.cpp:29] ClientMain(): Git Branch: fb_74_led_random_colors")
    messages = saver.get_log_messages()
    assert len(messages) == 1

    msg = messages[0]
    assert msg.level == LogLevel.info
    assert msg.trigger_location == "client_main.cpp:29"
    assert msg.trigger_method == "ClientMain()"
    assert msg.message == "Git Branch: fb_74_led_random_colors"

    saver.add_log_string("[P][client_main.cpp:29] ClientMain(): Git Branch: fb_74_led_random_colors")
    messages = saver.get_log_messages()
    assert len(messages) == 1

    saver.add_log_string("yolokopter")
    messages = saver.get_log_messages()
    assert len(messages) == 1
