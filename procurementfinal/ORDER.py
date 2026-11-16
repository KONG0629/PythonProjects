#Order Management Module
import storage



# Check item availability
# def check_stock(item_name, qty):
#     for item in storage.inventory:
#         if item["name"] == item_name:   #wag nalang muna to pakeelaman not fully functional sya so may iba ako gagawin hehe
#             return item["stock"] >= qty
#     return False
#dito sya mag chcheck ng stock if yung stock is greater than or equal sa qty then return nya yan if hindi then false



# Reduce stock after successful order
def reduce_stock(item_name, qty):
    for item in storage.inventory:
        if item["name"] == item_name:
            item["stock"] -= qty
#dito naman if we made order sa create order i rereduce nya yung stock sa qty na kinuha ng customer



# Create a new order
def create_order():
    customer = input("Enter customer name: ")

    order_items = []   # store multiple items here
    total_cost = 0

    print("\nEnter products to buy. Type 'done' to finish.\n")
    #mag input ka ng done if gusto mo na ma tapos yung pag order okay

    # Temporary stock tracker so selling twice won't go negative
    temp_stock = {item["name"]: item["stock"] for item in storage.inventory}
    #para mas madali nyo magets to ito yung temporary stock lang para ma prevent natin na maging negative yung stock
    #example nag buy yung user ng paper which is 5 and the stock is also 5 so 0 na yung stock ng paper
    #if bibili pa sya ulit ng paper di na sya makakabili kasi nasa 0 na yung stock. and this is only temporary. magagamit to sa reduce_stock
    #pag bumili si user ng paper sa inventory is 5 but here it will minus the stock it will finalize the stock only if the transaction is done or the order is done. gets??? 12/04/25
    #btw, kukunin lang jan yung name and yung stock it will iterate sa inventory

    while True:
        print("\n--- CURRENT INVENTORY ---")
        for item in storage.inventory:
            print(
                f"{item['name']} - Price: {item['price']} | stock: {item['stock']}")
        print()

        item_name = input("Enter item: ").lower()

        if item_name.lower() == "done":
            break#dito pag nag done ka edi okay end na

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
                if qty <= 0:
                    print("Quantity cannot be negative or zero!\n")
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
        for item in storage.inventory: #getting the price each item
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
        #ito naman pineprevent natin yung negative na stock so this is only temporary reducing stock, i hope u understand this block of code if not then let me know i can explain this whole code to make it easier to defend dala lang kayo spada.
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



# Change order status
def update_order_status():
    while True:
        try:
            order_id = int(input("Enter Order ID to update: "))
            if order_id < 0:#para ma prevent yung pag negative value
                print("Order ID cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! Order ID must be a number.\n")

    print("\nSelect new status:")
    print("1. Pending")
    print("2. Transit")
    print("3. Delivered")
#dito pumili kayo jan
    while True:
        choice = input("Enter choice (1-3): ")

        if choice == "1":
            new_status = "Pending"
            break
        elif choice == "2":
            new_status = "Transit"
            break
        elif choice == "3":
            new_status = "Delivered"
            break
        else:
            print("Invalid choice! Please enter 1, 2, or 3.\n")

#dito naman i update natin yung product by these three category
    for order in storage.orders:
        if order["id"] == order_id:
            order["status"] = new_status
            print("Order status updated!\n")
            return
    #dito hahanapin natin yung id ng customer para ma update yung status ng order
    print("Order not found.\n")


# Display all orders
def view_orders():
    print("\n--- ALL ORDERS ---")

    if not storage.orders:
        print("No orders found.\n")
        return#pag walang laman ang order edi wala

    not_ready_orders = []
    ready_orders = []#ito storage lang sa mga not,ready,delivered
    delivered_orders = []

    for order in storage.orders:
        if order["status"] == "Delivered":
            delivered_orders.append(order)
        elif order.get("ready_for_shipment"):
            ready_orders.append(order)
        else:
            not_ready_orders.append(order)

        #Display orders NOT ready for shipment getsss ahhh
        print("\n--- ORDERS NOT READY FOR SHIPMENT ---")
        if not not_ready_orders:
            print("No orders pending preparation.\n")
        else:
            for order in not_ready_orders:
                print(f"\nOrder ID: {order['id']}")
                print(f"Customer: {order['customer']}")
                print(f"Status: {order['status']}")
                print("Items:")
                for item in order["items"]:
                    print(f"  - {item['item']} x {item['qty']} @ {item['price']} each = {item['cost']}")
                print(f"Total Cost: {order['total_cost']}")
                print("-----------------------------")

        #Display orders READY for shipment getssss?
        print("\n--- ORDERS READY FOR SHIPMENT ---")
        if not ready_orders:
            print("No orders are ready for shipment.\n")
        else:
            for order in ready_orders:
                print(f"\nOrder ID: {order['id']}")
                print(f"Customer: {order['customer']}")
                print(f"Status: {order['status']}")  #Could be "In Transit" or "Delivered" after transportation updates
                print("Items:")
                for item in order["items"]:
                    print(f"  - {item['item']} x {item['qty']} @ {item['price']} each = {item['cost']}")
                print(f"Total Cost: {order['total_cost']}")
                print("-----------------------------")

        # Display orders that are DELIVERED
        print("\n--- DELIVERED ORDERS ---")
        if not delivered_orders:
            print("No orders have been delivered yet.\n")
        else:
            for order in delivered_orders:
                print(f"\nOrder ID: {order['id']}")
                print(f"Customer: {order['customer']}")
                print(f"Status: {order['status']}")  # Will always be "Delivered"
                print("Items:")
                for item in order["items"]:
                    print(f"  - {item['item']} x {item['qty']} @ {item['price']} each = {item['cost']}")
                print(f"Total Cost: {order['total_cost']}")
                print("-----------------------------")
#dito naman ipprint lang natin yung customer or yung mga order na ginawa natin




# Main menu
def two():
    while True:
        print("===================================")
        print("===== ORDER MANAGEMENT MODULE =====")
        print("===================================")
        print("1. Create Order")
        print("2. Update Order Status")
        print("3. View Orders")
        print("4. Back")

        # Try-except for number-only input para pag nag error edi babalik nya lang
        try:
            choice = int(input("Select Option: "))
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")
            continue  # babalik sya sa menu para pumili ulit diba

        if choice == 1:
            create_order()
        elif choice == 2:
            update_order_status()
        elif choice == 3:
            view_orders()
        elif choice == 4:
            print("Exiting Order Module...")
            break
        else:
            print("Invalid choice!\n")

