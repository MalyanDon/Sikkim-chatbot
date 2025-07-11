#!/usr/bin/env python3
"""Fix column name issues in the bot code"""

# Read the bot file
with open('comprehensive_smartgov_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix homestay column names
content = content.replace("self.homestay_df['place']", "self.homestay_df['Place']")
content = content.replace("row['name']", "row['HomestayName']")
content = content.replace("row['price_per_night']", "row['PricePerNight']")
content = content.replace("row['contact']", "row['ContactNumber']")
content = content.replace("self.homestay_df[self.homestay_df['place'] == place]", "self.homestay_df[self.homestay_df['Place'] == place]")
content = content.replace("row['rating']", "row['Rating']")
content = content.replace("['rating']", "['Rating']")

# Fix CSC column names
content = content.replace("row['operator_name']", "row['CSC_Operator_Name']")
content = content.replace("row['gpu']", "row['GPU']")
content = content.replace("self.csc_df[self.csc_df['gpu'] == message.strip()]", "self.csc_df[self.csc_df['GPU'] == message.strip()]")

# Write back the fixed content
with open('comprehensive_smartgov_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all column names:")
print("  Homestay data:")
print("    - 'place' → 'Place'")
print("    - 'name' → 'HomestayName'")
print("    - 'price_per_night' → 'PricePerNight'")
print("    - 'contact' → 'ContactNumber'")
print("    - 'rating' → 'Rating'")
print("  CSC data:")
print("    - 'operator_name' → 'CSC_Operator_Name'")
print("    - 'gpu' → 'GPU'") 