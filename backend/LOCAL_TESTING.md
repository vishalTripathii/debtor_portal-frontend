# Local Testing Instructions for Bulk Delete/Update

## Setup

1. **Start MongoDB** (if running locally)
   - Or make sure you can connect to MongoDB Atlas

2. **Start Django Development Server**
   ```bash
   cd E:\Collections_Debtor_page\Collections_Debtor_page\backend
   python manage.py runserver
   ```

3. **Get Admin Token**
   - Login to admin portal
   - Open browser DevTools (F12)
   - Go to Application > Local Storage
   - Copy the 'token' value

## Test Bulk Delete

Create a test Excel file `test_bulk_delete.xlsx` with:
```
Account Number
20220380242631
20191200000482
20210200095310
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/api/admin/debtors/bulk-delete-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@test_bulk_delete.xlsx"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Deleted 3 accounts from Excel file",
  "deleted_count": 3,
  "not_found_count": 0,
  "total_in_excel": 3
}
```

## Test Bulk Update

Create a test Excel file `test_bulk_update.xlsx` with:
```
Account Number | Name | Phone | Outstanding Balance
20220380242631 | Updated Name 1 | 0123456789 | 15000.00
20191200000482 | Updated Name 2 | 0987654321 | 25000.00
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/api/admin/debtors/bulk-update-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@test_bulk_update.xlsx"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Updated 2 accounts from Excel file",
  "updated_count": 2,
  "not_found_count": 0,
  "total_in_excel": 2
}
```

## Frontend Testing

1. Build frontend: `npm run build`
2. Serve locally: `npm run preview` or use local dev server
3. Test with Upload Mode dropdown
4. Select "bulkDelete" or "bulkUpdate" and upload Excel file

## What to Check

✅ Bulk Delete:
- All matching Account Numbers are deleted from MongoDB
- Non-existing account numbers are counted in not_found_count
- Response shows correct counts

✅ Bulk Update:
- All matching Account Numbers are updated in MongoDB
- Only provided fields are updated (doesn't overwrite other fields)
- Non-existing account numbers are counted in not_found_count
- Response shows correct counts

✅ Normal Upload (no mode selected):
- Still works as before (adds/updates normally)
- No interference with bulk operations
