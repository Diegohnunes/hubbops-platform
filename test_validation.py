from pydantic import BaseModel, EmailStr, ValidationError

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "viewer"

def test_payload(payload):
    try:
        r = RegisterRequest(**payload)
        print(f"✅ Valid: {payload}")
    except ValidationError as e:
        print(f"❌ Invalid: {payload}")
        print(e)

# Test cases
test_payload({"email": "admin@hubbops.local", "password": "123", "name": "Admin"})
test_payload({"email": "invalid-email", "password": "123", "name": "Admin"})
test_payload({"email": "admin@hubbops.local", "password": "", "name": "Admin"})
test_payload({"email": "admin@hubbops.local", "password": "123"}) # Missing name
