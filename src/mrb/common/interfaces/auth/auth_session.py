import flet as ft


class AuthSession:
    def __init__(self, page: ft.Page):
        self.page = page

    def set_auth_data(self, token, user_data):
        self.page.session.set("token", token)
        self.page.session.set("user_data", user_data)

    def get_auth_data(self):
        return {
            "token": self.page.session.get("token"),
            "user_data": self.page.session.get("user_data"),
        }

    def clear_auth_data(self):
        if self.page.session.get("token") is not None:
            self.page.session.remove("token")

        if self.page.session.get("user_data") is not None:
            self.page.session.remove("user_data")

    def token(self) -> str:
        return self.get_auth_data()["token"]

    def user_data(self) -> dict:
        return self.get_auth_data()["user_data"]
