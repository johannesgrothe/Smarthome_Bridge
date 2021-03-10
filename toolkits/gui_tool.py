import PySimpleGUI as sg

main_menu_options = ["Option 1", "Option 2", "Option 3"]


class BridgeGUITool:

    __app_layout: list
    __app_window: sg.Window

    def __init__(self):
        pass

    def __del__(self):
        self.close()

    @staticmethod
    def __create_button_list(data):
        buttons = []

        for line in data:
            buttons.append([
                sg.Text('', size=(5, 1)),
                sg.Button(line, size=(20, 1)),
                sg.Text('', size=(5, 1)),
            ])

        return buttons

    @staticmethod
    def __gen_head_line(text):
        return [[
            sg.Text(text, size=(25, 1))
        ]]

    @staticmethod
    def __gen_bottom_line(btn_text):
        return [[
            sg.Text('', size=(5, 1)),
            sg.Button(btn_text, size=(10, 1)),
            sg.Text('', size=(5, 1)),
        ]]

    def __view_main(self):
        buttons = self.__create_button_list(main_menu_options)

        head_line = self.__gen_head_line("Please select what to do")
        bottom_line = self.__gen_bottom_line("Quit")

        self.__app_layout = head_line + buttons + bottom_line

    def run(self):
        print("Starting GUI")

        self.__view_main()

        self.__app_window = sg.Window('Window Title', self.__app_layout)

        while True:
            event, values = self.__app_window.read()
            if event == sg.WIN_CLOSED or event == 'Quit':
                break
            # print('You entered ', values[0])

    def close(self):
        print("Closing GUI")
        self.__app_window.close()


if __name__ == "__main__":
    print("Launching...")
    app = BridgeGUITool()
    app.run()
    app.close()
