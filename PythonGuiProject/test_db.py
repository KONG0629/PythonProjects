from databases.auth_backend import login_user

user = login_user("admin", "admin123")

print("Final user result:")
print(user)