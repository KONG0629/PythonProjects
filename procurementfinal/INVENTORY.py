#INVENTORY MANAGEMENT MODULE
import storage



# 1. Add Product
def add_product():
    while True:
        name = input("Enter product name: ").lower()


        duplicate = False
        for product in storage.inventory:
            if product["name"].lower() == name:
                duplicate = True
                break
        if duplicate:
            print(f"Product '{name}' already exists in inventory. Please enter a different product.\n")
            continue
        if name == "":
            print("Product name cannot be empty.\n")
            continue
        break


    while True:
        try:
            price = float(input("Enter product price: "))
            if price <= 0:
                print("Price cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! Price must be a number.\n")

    while True:
        try:
            stock = int(input("Enter product stock: "))
            if stock <= 0:
                print("Stock cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! Stock must be a whole number.\n")

    while True:
        try:
            reorder_level = int(input("Enter reorder level: "))
            if reorder_level <= 0:
                print("Reorder level cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! Reorder level must be a number.\n")

    while True:
        try:
            reorder_amount = int(input("Enter reorder amount: "))
            if reorder_amount <= 0:
                print("Reorder amount cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! Reorder amount must be a number.\n")



#mag aadd ka dito and after i store natin sya sa dictionary product
    product = {
        "name": name,
        "price": price,
        "stock": stock,
        "reorder_level": reorder_level,
        "reorder_amount": reorder_amount#ito magagamit to sa five sa pag ship mamaya makikita mo dun
    }
#aapend natin yan dito sa storage.inventory naka another file yung storage para maganda
    storage.inventory.append(product)
    print("Product added successfully!\n")


# 2. Edit Product
def edit_product():

    edit_product = []

    name = input("Enter the product name to edit: ").lower()
#dito naman i edit natin yung product if makikita nya sa inventory
    for item in storage.inventory:
        if item["name"] == name:
            print("Editing product:", name)


            #dito nag dagdag ulit me ng try except kaya gets nyo naman yan mahaba lang talaga and same lang naman yan e
            while True:
                try:
                    new_price = float(input("Enter new product price: "))
                    if new_price <= 0:
                        print("Error: Price cannot be negative.\n")
                        continue
                    break
                except ValueError:
                    print("Invalid input! Price must be a number.\n")

            while True:
                try:
                    new_stock = int(input("Enter new stock value: "))
                    if new_stock <= 0:
                        print("Error: Stock cannot be negative.\n")
                        continue
                    break
                except ValueError:
                    print("Invalid input! Stock must be a whole number.\n")

            while True:
                try:
                    new_reorder = int(input("Enter new reorder level: "))
                    if new_reorder <= 0:
                        print("Error: Reorder level cannot be negative.\n")
                        continue
                    break
                except ValueError:
                    print("Invalid input! Reorder level must be a number.\n")

            while True:
                try:
                    new_reorder_amount = int(input("Enter new reorder amount: "))
                    if new_reorder_amount <= 0:
                        print("Error: Reorder amount cannot be negative.\n")
                        continue
                    break
                except ValueError:
                    print("Invalid input! Reorder amount must be a number.\n")



            #dito syempre iupdate nya lang yung product na inedit natin sa taas
            item["price"] = new_price
            item["stock"] = new_stock
            item["reorder_level"] = new_reorder
            item["reorder_amount"] = new_reorder_amount

            print("Product updated!\n")
            return
#gamit tayo ng return para isang edit lang pag di tayo gumamit di sya mag rereturn after we edit 1 product

    print("Product not found.\n")


# 3. Delete Product
def delete_product():
    name = input("Enter product name to delete: ").lower()
#dito we need to find the product that we want to delete
    for item in storage.inventory:
        if item["name"] == name:
            storage.inventory.remove(item)
            print("Product deleted!\n")
            return
#return pa din para after we delete babalik sa main

    print("Product not found.\n")


# 4. Update Stock (after sale or purchase)
def update_stock():
    name = input("Enter product name to update stock: ").lower()
    while True:
        try:
            change = int(input("Enter stock change (+ - (+20) for adding, - - (-12) for selling): "))
            break
        except ValueError:
            print("Invalid input! Change must be a number.")

#dito iedit lang natin yung stock ng product
    for item in storage.inventory:
        if item["name"] == name:

            #prevent to negative stock pag inedit natin yung stock
            if item["stock"] + change < 0:
                print(f"Error: Stock cannot go negative! Current stock is {item['stock']}.\n")
                return

            #ito naman if hindi negative
            item["stock"] += change
            print(f"Stock updated! New stock for {name}: {item['stock']}\n")
            return

    print("Product not found.\n")


# 5. View Inventory
def view_inventory():
    print("\n--- CURRENT INVENTORY ---")
    for item in storage.inventory:
        print(f"{item['name']} - Price: {item['price']} Stock: {item['stock']} (Reorder level: {item['reorder_level']})")
    print()
#pprint lang natin yung inventory dito


# 6. Check Low-Stock Alerts
def low_stock_alerts():
    print("\n--- LOW STOCK ITEMS ---")
    found = False
#found false para pag wala syang makita na low stock edi walang print

#dito pag meron ipprint nya yung sa less than ng reorder_level
    for item in storage.inventory:
        if item["stock"] < item["reorder_level"]:
            print(f"{item['name']} is LOW on stock! (Current: {item['stock']})")
            found = True

#ito yung false pag walang low stock edit print nya yan
    if not found:
        print("No low-stock items.")
    print()



def one():
    while True:
        print("=======================================")
        print("===== INVENTORY MANAGEMENT MODULE =====")
        print("=======================================")
        print("1. Add Product")
        print("2. Edit Product")
        print("3. Delete Product")
        print("4. Update Stock (Sale/Purchase)")
        print("5. View Inventory")
        print("6. Low Stock Alerts")
        print("7. Back")

        # Try-except for number-only input para pag nag error edi babalik nya lang
        try:
            choice = int(input("Select Option: "))
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")
            continue  # babalik sya sa menu para pumili ulit diba

        if choice == 1:
            add_product()
        elif choice == 2:
            edit_product()
        elif choice == 3:
            delete_product()
        elif choice == 4:
            update_stock()
        elif choice == 5:
            view_inventory()
        elif choice == 6:
            low_stock_alerts()
        elif choice == 7:
            print("Exiting Inventory Module...")
            break
        else:
            print("Invalid choice. Try again.\n")


