IS_XX_CLAIMS = {
    "iss": {"essential": True},
    "sub": {"essential": True},
    "aud": {"essential": True},
    "exp": {"essential": True},
    "iat": {"essential": False},
    "nbf": {"essential": False},
    "client_id": {"essential": True},
    "scope": {"essential": False},
    "x-nmos-api": {
        "essential": True,
        "values": ["registration", "query", "node", "connection"]
    }
}

IS_04_REG_CLAIMS = {
    "iss": {"essential": True},
    "sub": {"essential": True},
    "aud": {"essential": True},
    "exp": {"essential": True},
    "iat": {"essential": False},
    "nbf": {"essential": False},
    "client_id": {"essential": True},
    "scope": {"essential": False},
    "x-nmos-api": {
        "essential": True,
        "value": "registration"
    }
}

IS_04_QUERY_CLAIMS = {
    "iss": {"essential": True},
    "sub": {"essential": True},
    "aud": {"essential": True},
    "exp": {"essential": True},
    "iat": {"essential": False},
    "nbf": {"essential": False},
    "client_id": {"essential": True},
    "scope": {"essential": False},
    "x-nmos-api": {
        "essential": True,
        "value": "query"
    }
}

IS_04_NODE_CLAIMS = {
    "iss": {"essential": True},
    "sub": {"essential": True},
    "aud": {"essential": True},
    "exp": {"essential": True},
    "iat": {"essential": False},
    "nbf": {"essential": False},
    "client_id": {"essential": True},
    "scope": {"essential": False},
    "x-nmos-api": {
        "essential": True,
        "value": "node"
    }
}

IS_05_CLAIMS = {
    "iss": {"essential": True},
    "sub": {"essential": True},
    "aud": {"essential": True},
    "exp": {"essential": True},
    "iat": {"essential": False},
    "nbf": {"essential": False},
    "client_id": {"essential": True},
    "scope": {"essential": False},
    "x-nmos-api": {
        "essential": True,
        "value": "connection"
    }
}
