#PROCUREMENT MODULE
import storage


# Supplier Functions
def add_supplier():
    name = input("Enter supplier name: ")
    while True:
        contact = input("Enter contact number (11 digits): ")

        # Check if numeric and exactly 11 digits
        if contact.isdigit() and len(contact) == 11:
            break
        else:
            print("Invalid input! Contact number must be exactly 11 digits.\n")

#dito mag aadd tayo ng supplier natin gets naman yan so di ko na kailangan i explain pa
    supplier = {
        "id": len(storage.suppliers) + 1,
        "name": name,
        "contact": contact
    }

    storage.suppliers.append(supplier)#dito append the supplier dict to suppliers list
    print("Supplier added!\n")




def view_suppliers():
    print("\n--- Supplier List ---")
    for s in storage.suppliers:
        print(f"{s['id']}. {s['name']} - {s['contact']}")
    print()
#dito naman i lilist natin yung mga supplier natin



# Purchase Orders
def create_purchase_orders():
    low_stock_items = []#ito dito natin istore yung low stock na item na nasa inventory which is less than to their order level

    for item in storage.inventory:
        if item["stock"] < item["reorder_level"]:
            low_stock_items.append(item)
#dito naman if may low stock then i store dun sa low_stock_items na list sa taas
    if not low_stock_items:
        print("No low-stock items.\n")#pag wala siyang makita edi wala return agad sa main
        return

    print("\nLow Stock Items:")
    for item in low_stock_items:
        print(f"- {item['name']} (stock: {item['stock']})")
#dito naman sa low stock ipprint nya tapos i store yan sa po na dict sa baba tapos i append natin sya sa purchase_orderds na list

    print("\nSelect supplier for this purchase order:\n")
    view_suppliers()

    while True:
        try:
            supID = int(input("Enter supplier ID: "))
            if supID < 0:
                print("Supplier ID cannot be negative!\n")
                continue#dito din para ma prevent yung pag negative ng value
            break
        except ValueError:
            print("Invalid input! Please enter numbers only.\n")

    supplierName = None
    for s in storage.suppliers:
        if s["id"] == supID:
            supplierName = s["name"]#dito naman ichecheck nya yung id na tinype natin if existing yung id na yun with supplier if not then wala syang supplier
            break

    if supplierName is None:
        print("No supplier with that supplier ID.\n")
        return#pag yung id is walang supplier edi wala syang supplier na i aasign sa low stock babalik lang sya sa main

    # check nito if yung po is existing sa suppliername na yan
    existingPo = None
    for po in storage.purchase_orders:
        if po["supplier"] == supplierName and po["status"] != "Removed":
            existingPo = po
            break
            # if yung po natin is na assign na sa isang supplier so i checheck nya if yung supplier pwede na ba ulit mag supply ng mga things

    if existingPo:
        # Reset status to pending and update items
        existingPo["items"] = low_stock_items
        existingPo["status"] = "Pending"
        print(f"\nPurchase Order {existingPo['id']} updated and status set to Pending.\n")
        return


    po = {
        "id": len(storage.purchase_orders) + 1,
        "supplier": supplierName,
        "items": low_stock_items,
        "status": "Pending",
        "shipmentCount": 0
    }

    storage.purchase_orders.append(po)
    print(f"\nPurchase Order {po['id']} created!\n")



# Receiving Shipments
def record_shipment():
    while True:
        try:
            po_id = int(input("Enter PO ID to receive: "))
            if po_id < 0:#dito para ma prevent ulit yung negative na valueeee
                print("PO ID cannot be negative!\n")
                continue
            break
        except ValueError:
            print("Invalid input! ID must be a number.\n")

    #dito naman kukunin natin yung id ng po sa taas para magkaroon ng stock ulit
    po = next((order for order in storage.purchase_orders if order["id"] == po_id), None)#dito kukunin natin yung id ng po sa taas tas i store natin sya sa po na variable

    if po is None:#dito naman if wala edi return sa main
        print("Purchase order not found.\n")
        return

    if po["status"] == "Removed":
        print(f"Purchase Order {po_id} has been removed and cannot be received.\n")
        return

    # Ensure PO has items
    if not po["items"]:
        print("This purchase order has no items to receive.\n")
        return

    # pag receieved na yung status di na sya makakapag record ulit, until we do the transaction again for the supplier can supply the low stock again
    if po["status"] == "Received":
        print("This purchase order has already been received.\n")
        return

    for received_item in po["items"]:
        for inv_item in storage.inventory:
            if inv_item["name"] == received_item["name"]:#dito naman if yung item is pending then dadagdagan natin sya ng stock and after that yung status is magiging received para mawala na sya sa lowstock na product
                inv_item["stock"] += inv_item["reorder_amount"]

    # After updating PO status
    po["status"] = "Received"
    po["shipmentCount"] += 1  # increment PO's shipment count

    # Increment cumulative supplier shipment count
    for s in storage.suppliers:
        if s["name"] == po["supplier"]:
            if "shipmentCount" not in s:#ito yung shipment count for analytics and reports para ma store yung
                s["shipmentCount"] = 0
            s["shipmentCount"] += 1
            break

    print(f"Shipment for Purchase Order {po_id} received. Inventory updated!\n")

#inventory
def inventories():
    print("\nInventory:")
    for item in storage.inventory:#dito naman pprint lang natin yung name tsaka stock kasi yan lang muna pero pwede naman as whole detail ng product if gusto nyo
        print(f"{item['name']} - {item['stock']} units")
    print()



#managing the purchase order like a history and deleting the purchase order
def manage_purchase_orders():
    if not storage.purchase_orders:
        print("No purchase orders available.\n")
        return

    while True:
        print("\n--- Existing Purchase Orders ---")
        for po in storage.purchase_orders:
            print(f"PO {po['id']} - Supplier: {po['supplier']} | Status: {po['status']}")
        print()

        print("Options:")
        print("1. Remove a Pending Purchase Order")
        print("2. Return\n")

        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input! Numbers only.\n")
            continue

        if choice == 1:
            try:
                po_id = int(input("Enter PO ID to remove: "))
            except ValueError:
                print("Invalid input! Numbers only.\n")
                continue

            po_to_remove = None
            for po in storage.purchase_orders:
                if po["id"] == po_id:
                    po_to_remove = po#to hahanapin nya lang yung po id na may supplier na ininput natin
                    break

            if po_to_remove is None:
                print("Purchase Order not found.\n")
                continue

            if po_to_remove["status"] != "Pending":#dito hahanapin nya yung pending na status if pending yung status edi iseset nya ng removed para di na magamit sa shipment record
                print(f"Purchase Order {po_id} is not pending and cannot be removed.\n")
                continue

            # Mark as removed instead of deleting
            po_to_remove["status"] = "Removed"
            print(f"Purchase Order {po_id} has been removed from pending orders.\n")

        elif choice == 2:
            print("Returning to Procurement Module...\n")
            break
        else:
            print("Invalid choice. Please select 1 or 2.\n")




# Main Menu
def five():
    while True:
        print("==============================")
        print("=====PROCUREMENT MODULE=====\n")
        print("==============================")
        print("1. Add Supplier")
        print("2. View Suppliers")
        print("3. Create Purchase Orders (Low Stock)")
        print("4. Receive Shipment")
        print("5. View Inventory")
        print("6. View Purchase Orders")
        print("7. Back")

        while True:
            try:
                choice = int(input("Choose an option: "))
                break
            except ValueError:
                print("Invalid input! Please enter numbers only.\n")

        if choice == 1:
            add_supplier()
        elif choice == 2:
            view_suppliers()
        elif choice == 3:
            create_purchase_orders()
        elif choice == 4:
            record_shipment()
        elif choice == 5:
            inventories()
        elif choice == 6:
            manage_purchase_orders()
        elif choice == 7:
            print("Exiting Procurement Module...")
            break
        else:
            print("Invalid choice!\n")
