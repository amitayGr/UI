

import bcrypt

# הסיסמה שהמשתמש הזין
password = "Sh123456"

# hash ששמור ב‑DB
stored_hash = "$2b$12$YH/TvQYnIoyM.zAOeH90t.ZxvdtH2J.XLpgMF3.IEkHFn3RZMSrjq"

# בדיקה
if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
    print("Match!")
else:
    print("No match!")
