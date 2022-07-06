def get_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
