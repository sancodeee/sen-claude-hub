# Test Scenarios Guide

This guide provides detailed test scenarios for common web application patterns.

## E-Commerce Scenarios

### Product Listing Page (READ)

**Test Steps:**
1. Navigate to product listing URL
2. Verify page loads within 3 seconds
3. Check product cards display correctly
4. Verify all product images load
5. Test pagination (if exists)
6. Test sorting/filtering options
7. Verify product links work

**Expected Results:**
- All products visible
- No broken images
- Filters work correctly
- Pagination works

**Assertions:**
```javascript
// Product count matches expected
document.querySelectorAll('.product-card').length > 0

// Images loaded
Array.from(document.querySelectorAll('img')).every(img => img.complete && img.naturalHeight !== 0)
```

---

### Product Detail Page (READ)

**Test Steps:**
1. Click product from listing
2. Verify detail page loads
3. Check all product information displays
4. Verify image gallery works
5. Test add to cart button
6. Check related products section

**Expected Results:**
- All product details visible
- Images can be zoomed/viewed
- Add to cart button works
- Price displays correctly

---

### Add to Cart (CREATE)

**Test Steps:**
1. Navigate to product page
2. Select quantity
3. Select options (size, color, etc.)
4. Click add to cart
5. Verify cart counter updates
6. Verify success message

**Expected Results:**
- Item added to cart
- Cart count increases
- Success notification shown

---

### Cart Management (UPDATE, DELETE)

**Test Steps (UPDATE):**
1. Open cart page
2. Change item quantity
3. Verify total updates
4. Save changes

**Test Steps (DELETE):**
1. Open cart page
2. Click remove item
3. Confirm removal
4. Verify item removed
5. Verify total updated

**Expected Results:**
- Quantities update correctly
- Totals recalculate
- Items remove cleanly

---

## Form Scenarios

### Contact Form (CREATE)

**Test Steps:**
1. Navigate to contact page
2. Leave all fields empty, submit
3. Verify validation errors
4. Fill required fields only
5. Submit and verify success
6. Fill all fields
7. Submit and verify success
8. Check for confirmation message/email

**Test Cases:**
| Input | Expected Result |
|-------|-----------------|
| Empty form | Validation errors |
| Invalid email | Email format error |
| Valid data | Success message |

---

### Registration Form (CREATE)

**Test Steps:**
1. Navigate to registration page
2. Test password validation (weak/strong)
3. Test email validation
4. Test duplicate email (if applicable)
5. Verify terms checkbox enforcement
6. Submit valid registration
7. Verify email sent/account created

**Validation Tests:**
- Required fields
- Email format
- Password strength
- Password confirmation match
- Terms acceptance

---

### Login Form (CREATE Session)

**Test Steps:**
1. Navigate to login page
2. Test invalid credentials
3. Test empty fields
4. Test valid credentials
5. Verify redirect after login
6. Verify session established

**Test Cases:**
| Input | Expected Result |
|-------|-----------------|
| No credentials | Validation error |
| Wrong password | Error message |
| Valid credentials | Redirect to dashboard |

---

## Dashboard Scenarios

### Dashboard Display (READ)

**Test Steps:**
1. Login (if required)
2. Navigate to dashboard
3. Verify all widgets load
4. Check data displays correctly
5. Verify charts/graphs render
6. Test date range filters
7. Verify data exports work

**Expected Results:**
- All widgets visible
- No data errors
- Charts render correctly
- Filters work

---

### Settings Update (UPDATE)

**Test Steps:**
1. Navigate to settings
2. Modify profile information
3. Change password
4. Update preferences
5. Save changes
6. Logout and login
7. Verify changes persisted

**Expected Results:**
- All fields editable
- Changes save correctly
- Data persists across sessions

---

## Content Management Scenarios

### Article Creation (CREATE)

**Test Steps:**
1. Navigate to new article page
2. Enter title
3. Enter content
4. Upload featured image
5. Select category/tags
6. Save as draft
7. Publish article
8. Verify article appears on site

**Expected Results:**
- All fields work
- Image uploads succeed
- Draft saves correctly
- Publishing works

---

### Article Editing (UPDATE)

**Test Steps:**
1. Open existing article
2. Modify title/content
3. Replace image
4. Update categories
5. Save changes
6. View updated article
7. Verify changes visible

**Expected Results:**
- Original data loads
- Edits apply correctly
- Updates reflect immediately

---

### Article Deletion (DELETE)

**Test Steps:**
1. Navigate to article list
2. Find article to delete
3. Click delete
4. Confirm deletion
5. Verify article removed from list
6. Attempt to access deleted article URL

**Expected Results:**
- Confirmation dialog appears
- Article removed from list
- Deleted URL returns 404/redirect

---

## Search Scenarios

### Search Functionality (READ)

**Test Steps:**
1. Enter search query
2. Submit search
3. Verify results display
4. Check result relevance
5. Test no results scenario
6. Test pagination
7. Test filters/sorting

**Test Cases:**
| Query | Expected Result |
|-------|-----------------|
| Valid keyword | Relevant results |
| No matches | "No results" message |
| Empty query | All items or prompt |

---

## Authentication Scenarios

### Logout (DELETE Session)

**Test Steps:**
1. Ensure logged in
2. Click logout
3. Verify redirect to login/home
4. Attempt to access protected page
5. Verify redirected to login
6. Verify session cleared

**Expected Results:**
- Clean logout
- Session destroyed
- Protected pages inaccessible

---

## Error Handling Scenarios

### 404 Page Not Found (READ)

**Test Steps:**
1. Navigate to non-existent URL
2. Verify 404 page displays
3. Check helpful message shown
4. Verify navigation options available

**Expected Results:**
- Custom 404 page
- Clear error message
- Navigation options

---

### Server Error (READ)

**Test Steps:**
1. Navigate to page that causes error (if available)
2. Verify error page displays
3. Check error is logged
4. Verify user-friendly message

**Expected Results:**
- Error handled gracefully
- No sensitive data exposed
- Recovery options shown

---

## Mobile/Responsive Scenarios

### Mobile Viewport (READ)

**Test Steps:**
1. Set viewport to mobile size
2. Navigate to page
3. Verify mobile layout
4. Test touch interactions
5. Verify mobile menu works
6. Check content is readable

**Expected Results:**
- Responsive design works
- Touch targets adequate size
- No horizontal scroll
- Content accessible

---

## Performance Scenarios

### Page Load Performance (READ)

**Test Steps:**
1. Navigate to page
2. Measure load time
3. Check resource sizes
4. Verify lazy loading works
5. Test with slow network

**Performance Thresholds:**
| Metric | Target | Acceptable |
|--------|--------|------------|
| First Contentful Paint | <1s | <2s |
| Time to Interactive | <3s | <5s |
| Page Size | <2MB | <5MB |
| Requests | <50 | <100 |

---

## Test Scenario Template

Use this template to document new test scenarios:

```markdown
### [Scenario Name]

**Operation Type:** CREATE / READ / UPDATE / DELETE

**Description:**
Brief description of what is being tested.

**Prerequisites:**
- User must be logged in
- Test data must exist
- Specific page state required

**Test Steps:**
1. Step one
2. Step two
3. Step three

**Expected Results:**
- Expected outcome one
- Expected outcome two

**Assertions:**
```javascript
// JavaScript assertions
```

**Evidence to Collect:**
- Screenshots
- Console logs
- Network requests
```
