import uuid
from datetime import datetime, timedelta

class VmessUser:
    def __init__(self, email:str, expiry_days: int):

        if not email.strip():
            raise ValueError("email cannot be empty")
    
        if expiry_days <= 0:
            raise ValueError("Expiry days must be greater than 0")

        self.email = email.strip()
        self.protocol = "vmess"
        self.expire_at = datetime.now() + timedelta(days=expiry_days)
        self.uuid = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            'id': self.uuid,
            'email': self.email
        }


class VlessUser:
    def __init__(self, email:str, expiry_days: int):
        if not email.strip():
            raise ValueError("email cannot be empty")
    
        if expiry_days <= 0:
            raise ValueError("Expiry days must be greater than 0")

        self.email = email.strip()
        self.protocol = "vless"
        self.expire_at = datetime.now() + timedelta(days=expiry_days)
        self.uuid = str(uuid.uuid4())

    def to_dict(self):
        return {
            'id': self.uuid,
            'email': self.email
        }

class TrojanUser:
    def __init__(self, email:str, expiry_days: int):

        if not email.strip():
            raise ValueError("email cannot be empty")
    
        if expiry_days <= 0:
            raise ValueError("Expiry days must be greater than 0")

        self.email = email.strip()
        self.protocol = "trojan"
        self.expire_at = datetime.now() + timedelta(days=expiry_days)
        self.password = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            'password': self.password,
            'email': self.email
        }