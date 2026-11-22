from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.auth import SECRET_KEY, ALGORITHM

# Inisialisasi skema pembawa token Bearer
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi ini otomatis membaca header 'Authorization: Bearer <token>',
    lalu mendekode dan memvalidasi isinya.
    """
    token = credentials.credentials
    try:
        # Dekode token menggunakan SECRET_KEY yang sama
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid atau tidak memiliki subjek."
            )
        return {"username": username, "role": role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token kedaluwarsa atau tidak sah."
        )

# Fungsi khusus untuk memfilter hak akses khusus Admin
def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur ini khusus untuk Admin."
        )
    return current_user