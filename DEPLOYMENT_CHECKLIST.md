# 📋 Deployment Checklist - Customer Purchase Flow Fixes

## Pre-Deployment Validation ✅

### Code Quality
- [ ] All Python files pass syntax check
- [ ] No import errors
- [ ] Database migrations ready
- [ ] Configuration files updated

### Testing
- [ ] Run: `python test_critical_fixes.py`
  - Expected: All tests PASSED
- [ ] Manual smoke test: Visit home page
- [ ] Manual smoke test: Add item to cart
- [ ] Manual smoke test: Complete checkout as guest

### Security Review
- [ ] Reviewed PURCHASE_FLOW_FIXES_SUMMARY.md
- [ ] Understand all 7 fixes implemented
- [ ] Confirmed token generation for guest orders
- [ ] Verified payment method whitelist
- [ ] Checked input validation regexes

---

## Staging Deployment

### 1. Environment Setup
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/semira_staging"
export FLASK_ENV="production"
export SECRET_KEY="your-secret-key-here"
export WHATSAPP_NUMBER="251987957957"
```

### 2. Database
```bash
# Backup current data
pg_dump semira_production > backup_$(date +%s).sql

# Initialize staging database
python -c "from app import create_app; from database.db import init_db; app = create_app(); app.app_context().push(); init_db()"
```

### 3. Deploy Code
```bash
# Copy files to staging
cp routes/cart_routes.py /staging/routes/
cp routes/customer_routes.py /staging/routes/

# Or use git
git commit -m "Fix critical purchase flow issues"
git push origin develop
```

### 4. Start Application
```bash
# Using Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()

# Or development server
python app.py
```

### 5. Immediate Testing
- [ ] Homepage loads: `curl http://localhost:5000/`
- [ ] Can add item to cart: 
  ```bash
  curl -b cookies.txt -c cookies.txt \
    http://localhost:5000/cart/go/add/1?qty=1
  ```
- [ ] Checkout form loads: `curl http://localhost:5000/cart/checkout`
- [ ] Invalid payment method rejected:
  ```bash
  curl -X POST http://localhost:5000/cart/place-order \
    -d "payment_method=invalid_xyz" \
    -d "customer_name=Test" \
    ...
  ```

### 6. Monitor (First 24 Hours)
```bash
# Watch logs
tail -f /var/log/gunicorn.log
tail -f /var/log/flask.log

# Check for errors
grep -i error /var/log/*.log

# Monitor database
psql semira_staging -c "SELECT COUNT(*) FROM orders"
```

### 7. Load Test (If Available)
```bash
# Simple concurrent test
ab -n 100 -c 10 http://localhost:5000/

# Or use Apache Bench
apachebench -c 20 -n 1000 http://localhost:5000/
```

---

## Staging Validation Tests

### Test Case 1: Guest Order with Token
```
1. Visit http://staging.example.com/
2. Add item to cart
3. Go to checkout
4. Fill form:
   - Name: "Test Customer"
   - Address: "Test Address 12345"
   - Phone: "0987654321"
   - Payment: "cash"
5. Submit
6. Verify:
   - Order confirmation page shows
   - No errors in logs
   - session['guest_order_token'] exists (admin check)
7. Try to access other order ID directly
   - Should be denied/redirected
```

### Test Case 2: Payment Method Validation
```
1. Try to submit checkout with payment_method="crypto_moon"
2. Verify error message shown
3. Check database - no order created
```

### Test Case 3: Phone Format Validation
```
Valid formats:
- 0987654321 (09XXXXXXXX)
- 0787654321 (07XXXXXXXX)
- 251987654321 (2519XXXXXXX)

Invalid formats should be rejected:
- "invalid phone"
- "1234567890" (wrong prefix)
- "088888888" (wrong format)
```

### Test Case 4: Duplicate Order Prevention
```
1. Add item to cart
2. Submit order
3. Note order number from confirmation
4. Go back to checkout page
5. Add same item again
6. Submit order immediately (same data)
7. Verify:
   - Redirected to previous order confirmation
   - No new order created
   - Flash message about duplicate
```

### Test Case 5: Concurrent Orders
```
If you have multiple test accounts:
1. Account A: Add item, start checkout
2. Account B: Add item, start checkout (same product)
3. Account A: Submit order (5 units)
4. Account B: Submit order (5 units) - same product, only 8 in stock
5. Verify:
   - Account A succeeds
   - Account B gets "insufficient stock" error
   - Total stock becomes 0, not negative
```

---

## If Issues Occur During Staging

### Issue: "Invalid guest order token"
**Cause**: session['guest_order_token'] mismatch
**Fix**: 
1. Check browser cookies are enabled
2. Clear browser cache
3. Restart browser session
4. Check SECRET_KEY is same between requests

### Issue: Coupons not working
**Cause**: Atomic update may have failed
**Fix**:
1. Check coupon table exists
2. Verify usage_limit is set
3. Check coupons were NOT used beyond limit
4. View logs for UPDATE errors

### Issue: Orders not created
**Cause**: Validation errors
**Fix**:
1. Check server logs for validation errors
2. Verify all required fields provided
3. Check phone number format is correct
4. Verify payment_method is in whitelist

### Issue: High database load
**Cause**: Missing indexes
**Fix**:
```sql
CREATE INDEX IF NOT EXISTS idx_orders_user_created 
  ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_phone_created 
  ON orders(shipping_phone, created_at DESC);
```

---

## Final Sign-Off Checklist

### Technical
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Database queries optimized
- [ ] Backup restored and verified

### Functionality
- [ ] Guest can place order
- [ ] Logged-in user can place order
- [ ] Notifications sent properly
- [ ] Order tracking works

### Security
- [ ] Invalid payment methods rejected
- [ ] Phone format validated
- [ ] Email format validated
- [ ] Duplicate orders prevented
- [ ] Stock never goes negative

### Operations
- [ ] Logs being collected
- [ ] Alerts configured
- [ ] Monitoring active
- [ ] Support team briefed

### Performance
- [ ] Page load times acceptable
- [ ] No slow queries
- [ ] No memory leaks
- [ ] Database connections healthy

---

## Production Deployment

### Schedule
- [ ] Pick low-traffic time (off-peak hours)
- [ ] Inform customer support team
- [ ] Have rollback plan ready
- [ ] Set up on-call rotation

### Deployment
```bash
# 1. Final database backup
pg_dump semira_production > final_backup_$(date +%s).sql

# 2. Deploy code to production
git push origin main
# OR manual deployment

# 3. Verify app starts
curl -I http://production.example.com/

# 4. Monitor first hour
watch tail -f /var/log/production.log
```

### Monitoring (First 48 Hours)
- [ ] Check error rates (should be normal)
- [ ] Monitor order completion rate
- [ ] Watch for failed payments
- [ ] Check customer support tickets
- [ ] Verify notifications are working

### Success Criteria
- ✅ No increase in error rate
- ✅ Orders completing normally
- ✅ Customer complaints not increased
- ✅ Performance metrics stable
- ✅ Security alerts not triggered

---

## Rollback Plan (If Needed)

```bash
# 1. Stop application
systemctl stop gunicorn

# 2. Revert code
git revert HEAD
# OR restore from backup

# 3. Restore database (if needed)
psql semira_production < backup_XXXX.sql

# 4. Restart application
systemctl start gunicorn

# 5. Verify
curl -I http://production.example.com/
```

---

## Post-Deployment

### First Week
- [ ] Daily log review
- [ ] Customer complaint tracking
- [ ] Performance monitoring
- [ ] Security incident response

### First Month
- [ ] Run full test suite
- [ ] Load testing with real data
- [ ] Security penetration test
- [ ] Customer satisfaction survey

### Ongoing
- [ ] Weekly log review
- [ ] Monthly performance analysis
- [ ] Quarterly security audit
- [ ] Continuous monitoring

---

## Questions & Support

**For technical issues:**
- Check: PURCHASE_FLOW_FIXES_SUMMARY.md
- Check: CUSTOMER_PURCHASE_FLOW_REPORT.md
- Review logs for specific errors
- Run test_critical_fixes.py for diagnostics

**For business questions:**
- Impact of fixes documented in report
- Revenue protection measures explained
- Customer experience improvements listed
- ROI of security fixes quantified

---

**Checklist Created**: 2026-06-28
**Version**: 1.0
**Next Review**: After production deployment
