#Transportation Management Module
import storage


# Assign delivery to a driver or vehicle
def assign_delivery():
    while True:
        try:
            order_id = int(input("Enter Order ID to deliver: "))
            if order_id < 0:#dito para maiwasan yung pag negative input ahh
                print("ID cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! ID must be a number.\n")


    # Check if the order exists
    order = None
    for o in storage.orders:
        if o["id"] == order_id:
            order = o
            break

    if order is None:
        print(f"No order found with ID {order_id}. Cannot assign delivery.\n")
        return

    # Prevent assigning if order is not ready for shipment
    if not order.get("ready_for_shipment", False):
        print(f"Order {order_id} is not ready for shipment yet. Cannot assign delivery.\n")
        return

    # Prevent assigning if already delivered or in transit
    if order["status"] == "Delivered":
        print(f"Order {order_id} has already been delivered. Cannot assign again.\n")
        return
    elif order["status"] == "In Transit":
        print(f"Order {order_id} is already in transit. Cannot assign again.\n")
        return

    i = 0
    print()
    for driver in storage.drivers:
        i += 1
        print(f"{i}: {driver['name']}, {driver['availability']}")

    driver_assign = input("\nEnter driver name: ").capitalize()

    temp_driver = ''
    found = False
    avail = False
    for driver in storage.drivers:
        if driver_assign == driver["name"]:
            found = True
            if not driver["availability"] == "available":
                print('Driver not available.')
                break
            else:
                avail = True
            temp_driver = driver["name"]
            driver["availability"] = "not available"
            break
    if not found:
        print('Driver not found.')
    if not avail:
        return
    driver = temp_driver

    print("\nSelect vehicle type:")
    print("1. Motorcycle")
    print("2. Van")
    print("3. Truck")

    while True:
        vehicle_choice = input("Enter choice (1-3): ")

        if vehicle_choice == "1":
            vehicle = "Motorcycle"
            break
        elif vehicle_choice == "2":
            vehicle = "Van"
            break
        elif vehicle_choice == "3":
            vehicle = "Truck"
            break
        else:
            print("Invalid choice! Please enter 1, 2, or 3.\n")

    while True:
        eta = input("Enter estimated delivery time (This value is set by number of days): ").strip()

        # constraints to avoid input errors
        if not eta.isdigit():
            print("Invalid input! Estimated delivery time must be an integer and not a negative value.\n")
            continue
        elif not int(eta) > 0:
            print("Invalid input! Estimated delivery time must be greater than 0.\n")
            continue

        # singular and plural formatter
        if int(eta) > 1:
            eta = eta + " days"
        else:
            eta = eta + " day"

        break
#dito we input a order_id para ideliver dun sakanya gamit yang input

    #dito sstore lang natin yung record ng driver natin dito sa record na dictionary
    record = {
        "delivery_id": len(storage.delivery_records) + 1,
        "order_id": order_id,
        "driver": driver,
        "vehicle": vehicle,
        "eta": eta,
        "status": "In Transit"
    }


#dito i store natin yung record na dict sa delivery_records para malaman yung mga records na mga na deliver na
    storage.delivery_records.append(record)

    # also update the order status to "In Transit"
    for order in storage.orders:
        if order["id"] == order_id:
            order["status"] = "In Transit"
            break
    print("Delivery assigned successfully!\n")


# Update delivery status
def update_delivery_status():
    while True:
        try:
            d_id = int(input("Enter Delivery ID to update: "))
            if d_id < 0:#prevent natin yung pag negative input dito
                print("ID cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! ID must be a number.\n")

    print("\nSelect New Delivery Status:")
    print("1. In Transit")
    print("2. Delivered")

    while True:
        choice = input("Enter choice (1-2): ")

        if choice == "1":
            new_status = "In Transit"
            break
        elif choice == "2":
            new_status = "Delivered"
            break
        else:
            print("Invalid choice! Please enter 1 or 2.\n")
#dito naman i update lang natin yung status ng deliver if na deliver na or not so yah gets naman ata yan
    for delivery in storage.delivery_records:
        if delivery["delivery_id"] == d_id:
            delivery["status"] = new_status

            # Update order status para same sila pag nag update ang transportation part then the order edi ma update sila pareho
            for order in storage.orders:
                if order["id"] == d_id:
                    order["status"] = new_status
                    break

            print("Delivery status updated!\n")
            return #return para di mag loop yan para after i edit mag rereturn sya sa main

    print("Delivery record not found.\n")


# View delivery records
def view_deliveries():
    print("\n--- DELIVERY RECORDS ---")
    for d in storage.delivery_records:
        print(f"Delivery {d['delivery_id']} | Order {d['order_id']} | Driver: {d['driver']} | Vehicle: {d['vehicle']} | ETA: {d['eta']} | Status: {d['status']}")
    print()
#dito naman pprint lang yung deliver records


# Display all orders
def view_orders():
    print("\n--- ALL ORDERS FOR TRANSPORTATION ---")

    if not storage.orders:
        print("No orders found.\n")
        return

    ready_orders = []
    delivered_orders = []


    for order in storage.orders:
        if order["status"] == "Delivered":
            delivered_orders.append(order)#dito ano pag yung order status is == to delivered syempre is store nya jan yung status sa order
        elif order.get("ready_for_shipment"):
            ready_orders.append(order)

    print("\n--- ORDERS READY FOR SHIPMENT ---")
    if not ready_orders:
        print("No orders are ready for shipment.\n")
    else:
        for order in ready_orders:
            print(f"\nOrder ID: {order['id']}")
            print(f"Customer: {order['customer']}")
            print(f"Status: {order['status']}")  # Could be "Pending" or "In Transit"
            print("Items:")
            for item in order["items"]:
                print(f"  - {item['item']} x {item['qty']} @ {item['price']} each = {item['cost']}")
            print(f"Total Cost: {order['total_cost']}")
            print("-----------------------------")

    # Display DELIVERED orders
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



# Main menu
def three():
    while True:
        print("============================================")
        print("===== TRANSPORTATION MANAGEMENT MODULE =====")
        print("============================================")
        print("1. Assign Delivery")
        print("2. Update Delivery Status")
        print("3. View Delivery Records")
        print("4. View Orders")
        print("5. Back")

        while True:
            try:
                choice = int(input("Choose an option: "))
                break
            except ValueError:
                print("Invalid input! Choose a valid option.")


        if choice == 1:
            assign_delivery()
        elif choice == 2:
            update_delivery_status()
        elif choice == 3:
            view_deliveries()
        elif choice == 4:
            view_orders()
        elif choice == 5:
            print("Exiting Transportation Module...\n")
            break
        else:
            print("Invalid choice!\n")
