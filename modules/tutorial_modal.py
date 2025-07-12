from shiny import ui


def tutorial_modal():
    return ui.modal("Hier ist das Modal", easy_close=True, title="Tutorial Modal")
