#WAREHOUSE MANAGEMENT MODULE
from idlelib.autocomplete import TRY_A

import storage



# Add or update product storage location
def set_product_location():
    print("\n--- CURRENT INVENTORY ---")
    for item in storage.inventory:
        print(
            f"{item['name']} - Stock: {item['stock']}")
    print()


    name = input("Enter product name: ").lower()

    #dito naman for aisle and shelf input para saan sya istore ang mga things natin
    aisle = input("Enter Aisle (e.g., Aisle 3): ")
    shelf = input("Enter Shelf (e.g., Shelf 2): ")

    # Combine location para iisa lang sila
    location = f"{aisle}, {shelf}"

#dito iinput natin yung product kung saan natin sya gusto ilagay may example naman dyan, btw if gusto natin sya na mag input ng lower like example yung ininput dun sa INVENTORY.py is "Paper" tas tinype ni user jan is "paper" so invalid kasi malaki yung P dapat. pag gusto mo naman na kahit maliit i type tatangapin pwede ko naman iedit yan
    for item in storage.warehouse:
        if item["name"] == name: # == name.lower():
            item["location"] = location
            print("Location updated!\n")
            return
#dito naman if yung item is naka store na sya sa warehouse of location i update nya lang or pag wala edi lalagay nya dun

    storage.warehouse.append({
        "name": name,
        "location": location,
        "stock": 0
    })#dito nilagay lang natin sya sa storage.warehouse para ma store dun yung location ng product

    print("Product location recorded!\n")


# Show all product locations
def display_warehouse():
    print("\n--- WAREHOUSE LAYOUT ---")
    if not storage.warehouse:#dito if walang naka store kahit isa edi wala sya ipprint pag meron naman proceed sa baba
        print("No items stored yet.\n")
        return

#dito ipprint lang natin yung name tsaka location ng product
    for item in storage.warehouse:
        print(f"{item['name']} → {item['location']}")
    print()


# Update inventory when items are dispatched or restocked
def update_warehouse_inventory():
    name = input("Enter product name: ").lower()
    while True:
        try:
            qty = int(input("Enter quantity change (+ - (+12) for restock, - - (-20) for dispatch): "))
            break
        except ValueError:
            print("Invalid input! quantity must be a number.")

#dito naman i update lang natin yung qty ng product so gets naman yan basta update yan

    # CHECK IF PRODUCT EXISTS IN WAREHOUSE
    for w_item in storage.warehouse:
        if w_item["name"] == name:#check if the item is in the warehouse if not then error

            for item in storage.inventory:#hahanapin nya dito yung product para i update yung stock gets naman yan kaya goods na yan
                if item["name"] == name:
                    item["stock"] = max(0, item["stock"] + qty)#para ma prevent natin yung negative na stock if we update it hehe
                    print("Inventory updated!\n")
                    return#ito return para di na mag loop after update para mag return na sya sa main after the update process

    print("Product not found in warehouse.\n")


# Search for a product's storage location
def search_product_location():
    name = input("Enter product name to search: ").lower()
#dito naman sa function na to aalamin lang natin kung saan naka store yung isang product di ko alam bat kailangan pato kung pwede naman i print lahat yung nasa taas pero okay na yan. tas dito dapat same talaga ng name if malaki yung letter dapat malaki din. let me know if gusto nyo na kahit maliit yung i input ni user tatangapin pa din.
    for item in storage.warehouse:
        if item["name"] == name:
            print(f"{name} is stored at: {item['location']}\n")
            return

    print("Product location not found.\n")

#para to sa integration ng warehouse to transportation that the warehouse make the orders ready before it ship
def prepare_order_for_shipping():
    # Show orders that are not yet ready
    print("\n--- ORDERS NOT YET READY FOR SHIPMENT ---")
    has_pending = False
    for order in storage.orders:
        if not order.get("ready_for_shipment", False):
            has_pending = True
            print(f"Order ID: {order['id']} | Customer: {order['customer']} | Status: {order['status']}")
    if not has_pending:
        print("No pending orders to prepare.\n")
        return

    # Input order ID to mark as ready
    try:
        order_id = int(input("\nEnter the Order ID to mark as ready for shipment: "))
        if order_id < 0:
            print("Order ID cannot be negative!")
            return#para ma prevent yung pag input ng negative kainis kasi yung negative e
    except ValueError:
        print("Invalid input! Order ID must be a number.")
        return

    # Find the order
    order = None
    for o in storage.orders:
        if o["id"] == order_id:
            order = o
            break

    if order is None:
        print(f"Order {order_id} not found.")
        return

    # Mark order ready for shipment
    order["ready_for_shipment"] = True
    print(f"Order {order_id} is now ready for shipment!")



# Main menu
def four():
    while True:
        print("=======================================")
        print("===== WAREHOUSE MANAGEMENT MODULE =====")
        print("=======================================")
        print("1. Set Product Location")
        print("2. Display Warehouse Layout")
        print("3. Update Inventory After Dispatch/Restock")
        print("4. Search Product Location")
        print("5. Preparing orders to be shipped")
        print("6. Back")

        while True:
            try:
                choice = int(input("Choose an option: "))
                break
            except ValueError:
                print("Invalid input! Please enter numbers only.\n")


        if choice == 1:
            set_product_location()
        elif choice == 2:
            display_warehouse()
        elif choice == 3:
            update_warehouse_inventory()
        elif choice == 4:
            search_product_location()
        elif choice == 5:
            prepare_order_for_shipping()
        elif choice == 6:
            print("Exiting Warehouse Module...\n")
            break
        else:
            print("Invalid choice!\n")