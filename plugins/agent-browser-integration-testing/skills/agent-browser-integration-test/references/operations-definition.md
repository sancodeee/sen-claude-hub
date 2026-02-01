# Test Operations Definition

This document defines the four test operation types and their specific test scenarios.

## Operation Types

### CREATE

Tests for data creation and form submission functionality.

**Test Scenarios:**
1. Form accessibility - Can the form be accessed and loaded?
2. Form field validation - Do validation rules work correctly?
3. Required fields - Are required fields properly enforced?
4. Form submission - Does submit action work?
5. Success verification - Is success message/page shown?
6. Data persistence - Is created data retrievable?

**Common CREATE patterns:**
- Registration forms
- Contact forms
- Data entry forms
- Comment submissions
- File uploads

**Example agent-browser commands:**
```bash
agent-browser open <form_url>
agent-browser snapshot -i                    # Analyze form structure
agent-browser fill @e1 "test@example.com"    # Fill email
agent-browser fill @e2 "Test User"           # Fill name
agent-browser check @e3                      # Check agreement
agent-browser click @e4                      # Submit
agent-browser wait --text "Success"          # Verify success
```

---

### READ

Tests for page navigation, content retrieval, and data display.

**Test Scenarios:**
1. Page accessibility - Does the page load without errors?
2. Content display - Is all expected content visible?
3. Navigation links - Do all links work?
4. Media loading - Do images/videos load correctly?
5. Data retrieval - Can data be read from the page?
6. SEO elements - Are meta tags present?

**Common READ patterns:**
- Product page viewing
- Article/blog reading
- Dashboard display
- Search results
- Profile viewing

**Example agent-browser commands:**
```bash
agent-browser open <page_url>
agent-browser wait 2000        # Wait for full load
agent-browser get title                      # Get page title
agent-browser get text "body"                # Get all text
agent-browser get count "a"                  # Count links
agent-browser get count "img"                # Count images
agent-browser console                        # Check for errors
```

---

### UPDATE

Tests for data modification and editing functionality.

**Test Scenarios:**
1. Edit access - Can edit form/page be accessed?
2. Pre-population - Is existing data loaded correctly?
3. Field modification - Can fields be modified?
4. Validation updates - Does validation work on edits?
5. Save action - Does save/update action work?
6. Change verification - Are changes persisted?

**Common UPDATE patterns:**
- Profile editing
- Settings updates
- Content editing
- Cart modifications
- Data corrections

**Example agent-browser commands:**
```bash
agent-browser open <edit_page_url>
agent-browser snapshot -i                    # Analyze edit form
agent-browser get value @e1                  # Check current value
agent-browser fill @e1 "Updated Value"       # Modify field
agent-browser click @e2                      # Save
agent-browser wait --text "saved"            # Verify save
agent-browser get value @e1                  # Confirm new value
```

---

### DELETE

Tests for data removal and deletion functionality.

**Test Scenarios:**
1. Delete access - Can delete action be accessed?
2. Delete button - Is delete button visible/clickable?
3. Confirmation dialog - Does confirmation appear?
4. Deletion execution - Does deletion complete?
5. Post-delete state - Is item removed from list?
6. Permanent removal - Is data truly deleted?

**Common DELETE patterns:**
- Item deletion from lists
- Account deletion
- Comment removal
- File deletion
- Cart item removal

**Example agent-browser commands:**
```bash
agent-browser open <item_page_url>
agent-browser snapshot -i                    # Find delete button
agent-browser click @e1                      # Click delete
agent-browser wait --text "Are you sure"     # Wait for confirmation
agent-browser dialog accept                  # Accept deletion
agent-browser wait 2000        # Wait for completion
agent-browser get text ".item-count"         # Verify count decreased
```

---

### ALL

Comprehensive test covering all operation types (CREATE, READ, UPDATE, DELETE).

**Execution Order:**
1. READ - Verify page accessibility and structure
2. CREATE - Create test data
3. READ - Verify created data exists
4. UPDATE - Modify created data
5. READ - Verify updated data
6. DELETE - Remove test data
7. READ - Verify data is deleted

**Report Sections:**
- Full test cycle results
- CRUD operation validation
- End-to-end workflow verification
- Complete evidence collection

---

## Operation Selection Matrix

| User Need | Recommended Operation |
|-----------|---------------------|
| "Check if page works" | READ |
| "Test the contact form" | CREATE |
| "Verify editing works" | UPDATE |
| "Test deletion" | DELETE |
| "Full testing" | ALL |
| unspecified | ALL (default) |

---

## Test Scenarios by Page Type

| Page Type | Primary Operations |
|-----------|-------------------|
| Home/Landing | READ |
| Login | CREATE (session) |
| Registration | CREATE |
| Profile | READ, UPDATE |
| Settings | UPDATE |
| Shopping Cart | READ, UPDATE, DELETE |
| Checkout | CREATE |
| Product Listing | READ |
| Product Details | READ |
| Admin Dashboard | READ, UPDATE, DELETE |
| Search Results | READ |
| Contact Form | CREATE |
