"""User service — calls the API client."""


class UserService:
    def __init__(self, api_client):
        self.client = api_client

    def get_all_users(self):
        return self.client.get("/users")

    def get_user(self, user_id):
        return self.client.get(f"/users/{user_id}")

    def create_user(self, data):
        return self.client.post("/users", data=data)

    def delete_user(self, user_id):
        return self.client.delete(f"/users/{user_id}")
