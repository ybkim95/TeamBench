"""Application entry point."""
from app.api.client import ApiClient
from app.services.user_service import UserService


def main():
    client = ApiClient(base_url="https://api.example.com")
    user_svc = UserService(client)
    users = user_svc.get_all_users()
    print(f"Found {len(users)} users")
    return users


if __name__ == "__main__":
    main()
