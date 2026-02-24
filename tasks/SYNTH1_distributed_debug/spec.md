# SYNTH1: Distributed Debugging

## Goal
Fix 3 reported bugs in the web application so the test suite passes.

## Bug Report 1: "Users can't update their email"
- **Symptom**: PUT /users/123 returns 200 but email doesn't change
- **Steps to reproduce**: Send PUT request with `{"email": "new@example.com"}` to /users/123
- **Server logs**: Request received, handler completes with 200 status, no errors
- **Expected**: Email field should be updated to the new value
- **Root cause hint**: The handler is reading the wrong field from the request body. Check which JSON key is being used to extract the email value.

## Bug Report 2: "Order totals are wrong after applying discounts"
- **Symptom**: Order for 3 x $10 items with 20% discount shows $30 instead of $24
- **Steps to reproduce**: Create order, apply 20% discount, check total
- **Server logs**: Cache hit rate is 95%, response times normal
- **Monitoring data**: Cache is returning stale values
- **Expected**: Total after 20% discount on $30 should be $24
- **Root cause hint**: The root cause is NOT in orders.py — check the caching layer in utils/cache.py. The cache stores the pre-discount total and returns it on subsequent calls.

## Bug Report 3: "Monthly reports show dates in wrong timezone"
- **Symptom**: Report shows "2025-01-01" for event that happened "2024-12-31 at 11pm EST"
- **Steps to reproduce**: Create event at 2024-12-31 23:00 EST, generate report
- **Server logs**: Date formatting uses UTC
- **Expected**: Dates in reports should be in local timezone (US/Eastern)
- **Root cause hint**: Check utils/formatter.py — it formats dates in UTC without converting to local timezone first.

## Summary of Fixes
1. `app/routes/users.py`: Change `request.json.get('username')` to `request.json.get('email')`
2. `app/utils/cache.py`: Invalidate cache after discount application, or compute total after discount
3. `app/utils/formatter.py`: Apply timezone conversion before formatting dates

## Deliverables
- Fix all 3 bugs (minimal changes)
- All 8 tests in test_app.py must pass
- Total diff < 25 lines
