#STORAGE FOR ALL PARTS

#main
accounts = {"admin": "Admin@123"}
#1
inventory = [
    {"name": "paper","price": 5, "stock": 5, "reorder_level": 10, "reorder_amount": 10},
    {"name": "ink","price": 10, "stock": 2, "reorder_level": 5, "reorder_amount": 5}, #wag mo mind tong product naka fixed na muna yan jan para may product na nakalagay pero pwede mo burahin yan tas mag add ka nalang ng product naka store naman yan as whole sa storage na file
    {"name": "pens","price": 20, "stock": 50, "reorder_level": 20, "reorder_amount": 20} #yang reorder amount sa shipping sa suppier sa PROCUREMENT.py
]

drivers = [
    {"name": "Portillo", "availability": "available"},
    {"name": "Preligera", "availability": "available"},
    {"name": "Tuason", "availability": "available"},
    {"name": "Lata", "availability": "available"},
    {"name": "Almodiel", "availability": "available"}
]

#2
orders = []
#3
delivery_records = []
#4
warehouse = []
#5
suppliers = []
purchase_orders = []
#
messages = []