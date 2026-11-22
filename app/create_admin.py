from database import SessionLocal
from models.models import User
from auth import hash_password

db = SessionLocal()

# Hapus admin lama jika ada
db.query(User).filter(User.username == "admin").delete()
db.commit()

# Buat admin baru dengan password terenkripsi
new_admin = User(
    username="admin",
    hashed_password=hash_password("admin"),
    role="admin"
)
db.add(new_admin)
db.commit()
print("Admin berhasil dibuat dengan password terenkripsi!")