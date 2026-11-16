#Analytics and Reporting Module
import storage
import csv


# Helper function to save CSV, ito na yung ginamit natin para sa pag save ng file or csv sa mga 1-9 na option jan
def save_csv(filename, headers, rows):
    save = input(f"\nDo you want to save this report as '{filename}'? (y/n): ").strip().lower()
    if save == "y":#yung filename is yung file na name ng csv yung headers yan yung title ng list natin yung rows yan yung mga values natin
        try:
            with open(filename, "w", newline="") as file:#automatic open yung csv sa gilid natin gamit yun with na function
                writer = csv.writer(file)
                writer.writerow(headers)#this writer converting the python file into csv rows
                writer.writerows(rows)
            print(f"Report saved as '{filename}'\n")
        except Exception as e:#dito naman if error so mag tthrow sya ng error
            print(f"Error saving CSV: {e}")
    else:
        print("CSV not created.\n")


# Total orders processed
def report_total_orders():
    total = len(storage.orders) #len to kasi sa loob nyang orders is dictionary so it counts all the dictionary inside to that list, okay
    print(f"\nTotal Orders Processed: {total}\n")
    save_csv("total_orders.csv", ["Total Orders"], [[total]])


# Top Selling Items
def report_top_selling_items():
    print("\n--- TOP SELLING ITEMS ---")

    # count how many times each item was bought
    sales_count = {}

    for order in storage.orders:#hahanapin natin jan yung item na lagi binibili or top selling to it will iterate all the items in orders storage
        for item in order["items"]:
            name = item["item"]
            qty = item["qty"]

            if name not in sales_count:#if wala sya sa sales_count dictionary then = 0
                sales_count[name] = 0

            sales_count[name] += qty

    # If no sales pprint nya lang yan
    if not sales_count:
        print("No items sold yet.\n")
        return

    # Sort by most sold, we use (.items()) to turn the dictionary into tuples, because we can't sort the dictionary with a key and value
    # so we need to convert it into tuples to make a sorted correct, and the key=lambda is for python function that makes our project easy
    # the argument there is we going to take the 2nd value of the sales_count that we convert into tuples as you can see in the top after this function
    # we only get the item and the qty so inside that is the name and the quantity so only the quantity we need to make a sorted. and after is reverse=true
    # so we sorted it from highest to lowest. okay?
    sorted_sales = sorted(sales_count.items(), key=lambda x: x[1], reverse=True)

    for name, qty in sorted_sales:
        print(f"{name}: {qty} sold")
    # here we print the name and the qty sold for each item in sorted_sales
    print()
    save_csv("top_selling_items.csv", ["Item Name", "Quantity Sold"], sorted_sales)


# 3. Current Inventory Value
def report_inventory_value():
    print("\n--- INVENTORY VALUE ---")
    total_value = 0
    rows = []
    #dito naman sa part nato itototal lang natin lahat ng quantity ng price ng mga items so ipprint natin jan
    for item in storage.inventory:
        value = item["price"] * item["stock"]
        total_value += value
        print(f"{item['name']}: ₱{value}")
        rows.append([item["name"], item["price"], item["stock"], value])

    print(f"\nTotal Inventory Value: ₱{total_value}\n")
    rows.append(["TOTAL", "", "", total_value])
    save_csv("inventory_value.csv", ["Item Name", "Price", "Stock", "Value"], rows)



#######FIVE#######
# 4. Supplier Activity Report
def report_supplier_activity():
    print("\n--- SUPPLIER ACTIVITY REPORT ---")
    rows = []

    if not storage.suppliers:
        print("No suppliers recorded.\n")
        return

    for supplier in storage.suppliers:
        totalShip = supplier.get("shipmentCount", 0)  # cumulative count

        # print supplier info and total orders
        print(f"\nSupplier Name : {supplier['name']}")
        print(f"Contact       : {supplier['contact']}")
        print(f"Total Orders  : {totalShip}")
        rows.append([supplier["name"], supplier["contact"], totalShip])

    save_csv("supplier_activity.csv", ["Supplier Name", "Contact", "Total Orders"], rows)


# 5. Delivery Performance Summary
def report_delivery_performance():
    print("\n--- DELIVERY PERFORMANCE ---")

    total_deliveries = len(storage.delivery_records)
    delivered = sum(1 for d in storage.delivery_records if d["status"].lower() == "delivered")
    in_transit = total_deliveries - delivered

#dito naman sa function nato syempre cocount natin yung transit tsaka delivered, i can add the pending pero kayo bahala if gusto nyo kasali pa pending
    print("\n--- DELIVERY PERFORMANCE ---")
    print(f"Total Deliveries: {total_deliveries}")
    print(f"Delivered: {delivered}")
    print(f"In Transit: {in_transit}\n")

    rows = [["Total Deliveries", total_deliveries],
            ["Delivered", delivered],
            ["In Transit", in_transit]]
    save_csv("delivery_performance.csv", ["Metric", "Count"], rows)



########FOUR########
# Show all product locations
def display_warehouse():
    print("\n--- WAREHOUSE LAYOUT ---")
    if not storage.warehouse:#dito if walang naka store kahit isa edi wala sya ipprint pag meron naman proceed sa baba
        print("No items stored yet.\n")
        return
    rows = []
#dito ipprint lang natin yung name tsaka location ng product
    for item in storage.warehouse:
        print(f"{item['name']} → {item['location']}")
        rows.append([item["name"], item["location"]])

    save_csv("warehouse_layout.csv", ["Item Name", "Location"], rows)


############ONE#############
#View Inventory
def view_inventory():
    print("\n--- CURRENT INVENTORY ---")
    rows = []

    for item in storage.inventory:
        print(f"{item['name']} - Price: {item['price']} Stock: {item['stock']} (Reorder level: {item['reorder_level']})")
        rows.append([item["name"], item["price"], item["stock"], item["reorder_level"]])

    save_csv("current_inventory.csv", ["Item Name", "Price", "Stock", "Reorder Level"], rows)


#pprint lang natin yung inventory dito



############TWO#############
# Display all orders
def view_orders():
    print("\n--- ALL ORDERS ---")
    rows = []

    if not storage.orders:
        print("No orders found.\n")
        return#pag walang laman ang order edi wala

    for order in storage.orders:
        print(f"\nOrder ID: {order['id']}")
        print(f"Customer: {order['customer']}")
        print(f"Status: {order['status']}")
        print("Items:")
        for item in order["items"]:
            print(f"  - {item['item']} x {item['qty']} @ {item['price']} each = {item['cost']}")
            rows.append([order["id"], order["customer"], order["status"], item["item"], item["qty"], item["price"],
                         item["cost"]])
        print(f"Total Cost: {order['total_cost']}")
        print("-----------------------------")

    save_csv("all_orders.csv", ["Order ID", "Customer", "Status", "Item", "Qty", "Price", "Cost"], rows)


#dito naman ipprint lang natin yung customer or yung mga order na ginawa natin


###########THREE###########
# View delivery records
def view_deliveries():
    print("\n--- DELIVERY RECORDS ---")
    if not storage.delivery_records:
        print("No deliveries found.\n")
        return
    rows = []
    for d in storage.delivery_records:
        print(f"Delivery {d['delivery_id']} | Order {d['order_id']} | Driver: {d['driver']} | Vehicle: {d['vehicle']} | ETA: {d['eta']} | Status: {d['status']}")
        rows.append([d['delivery_id'], d['order_id'], d['driver'], d['vehicle'], d['eta'], d['status']])

    save_csv("delivery_records.csv", ["Delivery ID", "Order ID", "Driver", "Vehicle", "ETA", "Status"], rows)
#dito naman pprint lang yung deliver records



# MAIN ANALYTICS MENU
def six():
    while True:
        print("=== ANALYTICS & REPORTING ===")
        print("1. Total Orders Processed")
        print("2. Top-Selling Items")
        print("3. Inventory Value")
        print("4. Supplier Activity Reports")
        print("5. Delivery Performance")
        print("6. Warehouse Items")
        print("7. View Inventory")
        print("8. View Orders")
        print("9. View deliveries")
        print("10. Back")

        while True:
            try:
                choice = int(input("Choose an option: "))
                break
            except ValueError:
                print("Invalid Choice. input numbers only")

        if choice == 1:
            report_total_orders()
        elif choice == 2:
            report_top_selling_items()
        elif choice == 3:
            report_inventory_value()
        elif choice == 4:
            report_supplier_activity()
        elif choice == 5:
            report_delivery_performance()
        elif choice == 6:
            display_warehouse()
        elif choice == 7:
            view_inventory()
        elif choice == 8:
            view_orders()
        elif choice == 9:
            view_deliveries()
        elif choice == 10:
            print("Exiting Analytics & Reporting Module...")
            break
        else:
            print("Invalid option.\n")
