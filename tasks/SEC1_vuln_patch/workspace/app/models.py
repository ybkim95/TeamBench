"""Data models — clean, no vulnerabilities."""


class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Session:
    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token
