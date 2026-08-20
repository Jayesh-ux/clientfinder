import sqlite3

DB_PATH = 'crm.db'

updates = {
    "Eva Esthetic": "+919538984780",
    "Root 32": "+916364444636",
    "Dental Den": "+919591788667",
    "The Dental Lounge": "+919207069900"
}

def update_phones():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for name, phone in updates.items():
        cursor.execute("UPDATE leads SET whatsapp_number = ?, public_business_phone = ? WHERE business_name LIKE ?", (phone, phone, f"%{name}%"))
        print(f"Updated {name} with phone {phone}")
        
    # Remove National Dental Care as it was a false positive
    cursor.execute("DELETE FROM leads WHERE business_name LIKE '%National Dental Care%'")
    print("Removed National Dental Care (Not in HRBR)")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_phones()
