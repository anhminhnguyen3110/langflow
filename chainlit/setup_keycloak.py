# -*- coding: utf-8 -*-
"""
Script to automatically configure Keycloak for Chainlit SSO.
Creates realm, client, and test user using Keycloak Admin REST API.
"""

import requests
import json

KEYCLOAK_URL = "http://localhost:8080"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
REALM_NAME = "chainlit"
CLIENT_ID = "chainlit-client"
CHAINLIT_URL = "http://localhost:8000"

def get_admin_token():
    """Get admin access token from master realm."""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def create_realm(token):
    """Create chainlit realm."""
    url = f"{KEYCLOAK_URL}/admin/realms"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    realm_data = {
        "realm": REALM_NAME,
        "enabled": True,
        "registrationAllowed": False,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": True,
        "editUsernameAllowed": False,
        "bruteForceProtected": True
    }
    
    response = requests.post(url, headers=headers, json=realm_data)
    if response.status_code == 409:
        print(f"[OK] Realm '{REALM_NAME}' already exists")
        return True
    elif response.status_code == 201:
        print(f"[OK] Realm '{REALM_NAME}' created successfully")
        return True
    else:
        print(f"[ERROR] Failed to create realm: {response.text}")
        return False

def create_client(token):
    """Create chainlit-client in the realm."""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    client_data = {
        "clientId": CLIENT_ID,
        "name": "Chainlit Application",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": [f"{CHAINLIT_URL}/auth/oauth/keycloak/callback"],
        "webOrigins": [CHAINLIT_URL],
        "publicClient": False,
        "protocol": "openid-connect",
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": False,
        "authorizationServicesEnabled": False,
        "fullScopeAllowed": True,
        "defaultClientScopes": ["openid", "profile", "email"]
    }
    
    response = requests.post(url, headers=headers, json=client_data)
    if response.status_code == 409:
        print(f"[OK] Client '{CLIENT_ID}' already exists")
    elif response.status_code == 201:
        print(f"[OK] Client '{CLIENT_ID}' created successfully")
    else:
        print(f"[ERROR] Failed to create client: {response.text}")
        return None
    
    # Get client secret
    clients_url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients?clientId={CLIENT_ID}"
    response = requests.get(clients_url, headers=headers)
    clients = response.json()
    if clients:
        client_uuid = clients[0]["id"]
        secret_url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_uuid}/client-secret"
        response = requests.get(secret_url, headers=headers)
        if response.status_code == 200:
            secret = response.json().get("value")
            print(f"[KEY] Client Secret: {secret}")
            return secret
    return None

def create_user(token, username, password, email, first_name, last_name):
    """Create a test user in the realm."""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    user_data = {
        "username": username,
        "email": email,
        "emailVerified": True,
        "enabled": True,
        "firstName": first_name,
        "lastName": last_name,
        "credentials": [{
            "type": "password",
            "value": password,
            "temporary": False
        }]
    }
    
    response = requests.post(url, headers=headers, json=user_data)
    if response.status_code == 409:
        print(f"[OK] User '{username}' already exists")
        return True
    elif response.status_code == 201:
        print(f"[OK] User '{username}' created successfully")
        return True
    else:
        print(f"[ERROR] Failed to create user: {response.text}")
        return False

def main():
    print("=" * 50)
    print("Keycloak SSO Setup for Chainlit")
    print("=" * 50)
    
    # Get admin token
    print("\n1. Getting admin token...")
    token = get_admin_token()
    print("[OK] Got admin token")
    
    # Create realm
    print(f"\n2. Creating realm '{REALM_NAME}'...")
    create_realm(token)
    
    # Create client
    print(f"\n3. Creating client '{CLIENT_ID}'...")
    client_secret = create_client(token)
    
    # Create test user
    print("\n4. Creating test user...")
    create_user(token, "testuser", "password123", "testuser@example.com", "Test", "User")
    
    # Print configuration
    print("\n" + "=" * 50)
    print("CONFIGURATION FOR chainlit/.env")
    print("=" * 50)
    print(f"""
OAUTH_KEYCLOAK_CLIENT_ID={CLIENT_ID}
OAUTH_KEYCLOAK_CLIENT_SECRET={client_secret}
OAUTH_KEYCLOAK_REALM={REALM_NAME}
OAUTH_KEYCLOAK_BASE_URL={KEYCLOAK_URL}
OAUTH_KEYCLOAK_NAME=keycloak
""")
    
    print("=" * 50)
    print("TEST LOGIN CREDENTIALS")
    print("=" * 50)
    print("Username: testuser")
    print("Password: password123")
    print("=" * 50)

if __name__ == "__main__":
    main()
