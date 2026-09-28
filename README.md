# BijliSaarthi – Clean Streamlit Release

### Changes made
- Removed the **bill photo upload/file-uploader** from the Streamlit app.
- Removed the **OCR scanning code** and OCR dependencies.
- Kept manual entry for the bill values: previous reading, current reading, units used, bill amount, billing days and days until next bill.
- Kept the **one-time household setup** and saved household profile.
- Removed the consumer-entered **electricity rate (₹/kWh)** field.
- The app now calculates an **automatic effective bill-based rate = bill amount ÷ units used**. This avoids asking the consumer to guess a tariff. This is a planning rate, not an official tariff.
- Fixed the logo structure: `bijlisaarthi_logo.png` is in the **same folder as `app.py`**.
- Kept the budget estimate, appliance profile, saving plan and Saarthi chat.

### Why there is no single universal electricity rate
Electricity tariffs are not one fixed India-wide number. They vary by DISCOM, state, consumer category and consumption slab. MSEDCL/Maharashtra, for example, uses slab-based residential charges. Therefore this version does not hard-code a misleading universal tariff; it derives a practical effective rate from the user's own bill.

### Streamlit deployment
Upload the contents of this folder to a **new GitHub repository**. Keep these files together:

- `app.py`
- `bijlisaarthi_logo.png`
- `requirements.txt`
- `README.md`

Then deploy with:
- Branch: `main`
- Main file path: `app.py`
