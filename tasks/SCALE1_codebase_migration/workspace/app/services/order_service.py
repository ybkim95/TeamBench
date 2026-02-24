"""Order service."""


class OrderService:
    def __init__(self, api_client):
        self.client = api_client

    def get_orders(self):
        return self.client.get("/orders")

    def create_order(self, data):
        return self.client.post("/orders", data=data)
