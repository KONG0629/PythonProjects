import storage

def reduce_stock(item_name, qty):
    for item in storage.inventory:
        if item["name"] == item_name:
            item["stock"] -= qty

#Place an Order
def place_order():
    customer = input("Enter customer name: ")

    order_items = []  # store multiple items here
    total_cost = 0

    print("\nEnter products to buy. Type 'done' to finish.\n")
    # mag input ka ng done if gusto mo na ma tapos yung pag order okay

    # Temporary stock tracker so selling twice won't go negative
    temp_stock = {item["name"]: item["stock"] for item in storage.inventory}
    # para mas madali nyo magets to ito yung temporary stock lang para ma prevent natin na maging negative yung stock
    # example nag buy yung user ng paper which is 5 and the stock is also 5 so 0 na yung stock ng paper
    # if bibili pa sya ulit ng paper di na sya makakabili kasi nasa 0 na yung stock. and this is only temporary. magagamit to sa reduce_stock
    # pag bumili si user ng paper sa inventory is 5 but here it will minus the stock it will finalize the stock only if the transaction is done or the order is done. gets??? 12/04/25
    # btw, kukunin lang jan yung name and yung stock it will iterate sa inventory

    while True:
        print("\n--- CURRENT INVENTORY ---")
        for item in storage.inventory:
            print(
                f"{item['name']} - Price: {item['price']} | stock: {item['stock']}")
        print()

        item_name = input("Enter item: ").lower()

        if item_name.lower() == "done":
            break  # dito pag nag done ka edi okay end na

        # Check if the item exists ginamit natin yung temp_stock na variable dito
        if item_name not in temp_stock:
            print("Item not found in inventory!\n")
            continue

        # Check natin if yung stock is 0 if 0 na edi bawal na bilhin ginamit natin yung temp stock for temporary storage for name and stock
        if temp_stock[item_name] == 0:
            print(f"X {item_name} is OUT OF STOCK! Cannot order again.\n")
            continue

        while True:
            try:
                qty = int(input("Enter quantity: "))
                if qty < 0:
                    print("Quantity cannot be negative!\n")
                    continue
                break
            except ValueError:
                print("Invalid input! Quantity must be a number.\n")

        # Check if enough temporary stock exists
        if qty > temp_stock[item_name]:
            print(f"X Not enough stock! Only {temp_stock[item_name]} available.\n")
            continue

        # # Check stock
        # if not check_stock(item_name, qty):
        #     print("Not enough stock! Item skipped.\n")   #ito din wag nalang muna to burahin ahh 12/04/2025
        #     continue#checking stock each item you want to buy if it's enough or not

        # Get price
        price = 0
        for item in storage.inventory:  # getting the price each item
            if item["name"] == item_name:
                price = item["price"]
                break

        cost = price * qty
        total_cost += cost

        # Add item to order list
        order_items.append({
            "item": item_name,
            "qty": qty,
            "price": price,
            "cost": cost
        })
        # ito naman pineprevent natin yung negative na stock so this is only temporary reducing stock, i hope u understand this block of code if not then let me know i can explain this whole code to make it easier to defend dala lang kayo spada.
        temp_stock[item_name] -= qty

        print(f"Added: {price} x {qty} (₱{cost})\n")

    # If no items were added
    if not order_items:
        print("No items added. Order cancelled.\n")
        return

    # Create the full order
    order = {
        "id": len(storage.orders) + 1,
        "customer": customer,
        "items": order_items,
        "total_cost": total_cost,
        "status": "Pending",
        "ready_for_shipment": False
    }

    # Save order
    storage.orders.append(order)

    # Reduce stock for all ordered items
    for item in order_items:
        reduce_stock(item["item"], item["qty"])

    print("\nOrder created successfully!")
    print(f"Total cost: ₱{total_cost}\n")


#Check Order Status
def order_status():
    if not storage.orders:
        print("No orders found.\n")
        return

    print("\n--- LIST ORDERS ---")
    for o in storage.orders:
        print(f"Order ID: {o['id']} | Customer: {o['customer']}")
    print()

    try:
        order_id = int(input("Enter your Order ID: "))
    except ValueError:
        print("Invalid input! Order ID must be a number.\n")
        return

    order = next((o for o in storage.orders if o["id"] == order_id), None)
    if not order:
        print("Order not found.\n")
        return


    print(f"\nOrder ID: {order['id']}")
    print(f"Customer: {order['customer']}")
    print("Items:")
    for i in order["items"]:
        print(f"- {i['item']} x {i['qty']} (₱{i['cost']})")
    print(f"Total Cost: ₱{order['total_cost']}")
    print(f"Status: {order['status']}\n")





def user():
    print("======================================")
    print("============USER MODULE===============")
    print("======================================")
    print()

    while True:
        print("[1] Orders\n"
              "[2] Order Status\n"
              "[3] Exit")

        try:#same to sa try except sa taas only numbers
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")
            continue

        if choice == 1:
            place_order()
        elif choice == 2:
            order_status()
        elif choice == 3:
            print("Exiting...")
            break
        else:
            print("Invalid choice.\n")
