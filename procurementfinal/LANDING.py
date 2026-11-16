import INVENTORY, ORDER, TRANSPORT, WAREHOUSE, PROCUREMENT, ANALYTICS, storage, users

error1 = "Password should at least 8 characters or more"
error2 = "Password should contain at least 1 lower case letter"
error3 = "Password should contain at least 1 upper case letter"
error4 = "Password should contain at least 1 digit"
error5 = "Password should contain at least 1 special character"
error6 = "Password and Confirm password should the same"
special = "~`!@#$%^&*(){}[]-_=+;:|'""""/""?.,<>"""

storage.accounts = {"admin": "Admin@123"}
success = False


def signin():
    global success
    print("======================================")
    print("=============SIGNIN PAGE==============")
    print("======================================")
    print()
    while True:
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        conpass = input("Confirm Password: ")

        if len(password) < 8:
            print(error1)
            continue
        if not any(char.islower() for char in password):
            print(error2)
            continue
        if not any(char.isupper() for char in password):
            print(error3)
            continue
        if not any(char.isdigit() for char in password):
            print(error4)
            continue
        if not any(char in special for char in password):
            print(error5)
            continue
        if password != conpass:
            print(error6)
            continue
        success = True
        break

    if success:
        print(f"Account Successfully Created! {username}.\n")
        print(f"Welcome, {username}.\n")
        storage.accounts[username] = password #Storing the username and password in accounts dictionary
        return
    else:
        print("Try Again!!\n")


def login():
    print("======================================")
    print("=============LOGIN PAGE===============")
    print("======================================")
    print()

    username = input("Enter Username: ")
    password = input("Enter Password: ")

    # if storage.accounts.get(username) == password:
    #     print(f"Login Successful! {username}.\n")
    #     print(f"Welcome, {username}.\n")
    #
    #     if username.lower() == "admin":
    #         dashboard()
    #     else:
    #         users.user()
    # else:
    #     print("Incorrect username or password.\n")
    if storage.accounts.get(username) == password:
        print(f"Login Successful! {username}.\n")
        print(f"Welcome, {username}.\n")
        dashboard()
    else:
        print("Incorrect username or password.\n")



def dashboard():
    print("=============================================")
    print("===========PROCUREMENT MAIN PAGE=============")
    print("=============================================")
    print()
    while True:
        print()
        print("[1] Inventory Management Module\n"
              "[2] Order Management Module\n"
              "[3] Transportation Management Module\n"
              "[4] Warehouse Management Module\n"
              "[5] Procurement Management Module\n"
              "[6] Analytics and Reporting Module\n"
              "[7] Exit\n")

        # Try-except for number-only input para pag nag error edi babalik nya lang
        try:
            select = int(input("Select Option: "))
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")
            continue  # babalik sya sa menu para pumili ulit diba

        if select == 1:
            INVENTORY.one()
        elif select == 2:
            ORDER.two()
        elif select == 3:
            TRANSPORT.three()
        elif select == 4:
            WAREHOUSE.four()
        elif select == 5:
            PROCUREMENT.five()
        elif select == 6:
            ANALYTICS.six()
        elif select == 7:
            print("Exiting...")
            break
        else:
            print("Invalid Choice.\n")



def accounts():
    print("======================================")
    print("==============ACCOUNTS================")
    print("======================================")
    print()

    if not storage.accounts:
        print("No accounts found.\n")
        return

    print("Registered Accounts:")
    for username in storage.accounts.keys():
        print(f"- {username}")

    print()

def main():
    print("======================================")
    print("============PROCUREMENT===============")
    print("======================================")
    print()

    while True:
        print("[1] Login\n"
              "[2] Signin\n"
              "[3] Accounts\n"
              "[4] Exit")

        try:#same to sa try except sa taas only numbers
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")
            continue

        if choice == 1:
            login()
        elif choice == 2:
            signin()
        elif choice == 3:
            accounts()
        elif choice == 4:
            exit()
        else:
            print("Invalid choice.\n")

main()