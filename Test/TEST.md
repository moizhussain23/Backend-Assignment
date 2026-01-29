# 🧪 **Complete Postman Testing Guide - Credit Approval System**

## 📋 **Overview**

This guide provides comprehensive instructions for testing the Credit Approval System APIs using Postman. The system includes 5 main API endpoints that handle customer registration, loan eligibility checks, loan creation, and loan viewing.

---

## 🚀 **Pre-Testing Setup**

### **1. Start the System**
```bash
# Start Docker containers
docker-compose up --build --no-cache

# Wait for all services to start and data to load
# You should see: "Development server is running at http://0.0.0.0:8000/"
```

### **2. Verify System Status**
- **Django API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/ (admin/admin123)
- **Database**: PostgreSQL with 300 customers + 753 loans loaded

### **3. Open Postman**
- Install Postman from https://www.postman.com/downloads/
- Create a new collection called "Credit Approval System"

---

## 🔧 **Environment Setup in Postman**

### **Create Environment Variables:**
1. Click **Environment** → **Create Environment**
2. Name: "Credit Approval Local"
3. Add variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `customer_id` | `1` | Test customer ID |
| `loan_id` | `7798` | Test loan ID |

---

## 📊 **API Endpoint Testing**

### **1️⃣ Customer Registration API**

**Endpoint**: `POST {{base_url}}/register/`

#### **✅ Test Case 1: Successful Registration**

**Request:**
- **Method**: `POST`
- **URL**: `{{base_url}}/register/`
- **Headers**: 
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
  ```json
  {
      "first_name": "John",
      "last_name": "Doe",
      "age": 30,
      "phone_number": 9876543210,
      "monthly_income": 50000
  }
  ```

**Expected Response** (201 Created):
```json
{
    "customer_id": 301,
    "name": "John Doe",
    "age": 30,
    "monthly_income": "50000.00",
    "approved_limit": 1800000,
    "phone_number": 9876543210
}
```

**Validation Points:**
- ✅ Status Code: `201`
- ✅ Response contains `customer_id`
- ✅ Approved limit = monthly_income × 36
- ✅ Name formatted correctly

#### **❌ Test Case 2: Duplicate Phone Number**

**Request:**
- Same as above but use phone number: `9629317944` (existing customer)

**Expected Response** (400 Bad Request):
```json
{
    "error": "Customer with this phone number already exists"
}
```

#### **❌ Test Case 3: Missing Required Fields**

**Request:**
```json
{
    "first_name": "Jane",
    "age": 25
}
```

**Expected Response** (400 Bad Request):
```json
{
    "last_name": ["This field is required."],
    "phone_number": ["This field is required."],
    "monthly_income": ["This field is required."]
}
```

#### **❌ Test Case 4: Invalid Data Types**

**Request:**
```json
{
    "first_name": "Test",
    "last_name": "User", 
    "age": "invalid",
    "phone_number": 1234567890,
    "monthly_income": -5000
}
```

**Expected Response** (400 Bad Request):
- Age validation error
- Negative income validation error

---

### **2️⃣ Check Loan Eligibility API**

**Endpoint**: `POST {{base_url}}/check-eligibility/`

#### **✅ Test Case 1: Eligible Customer**

**Request:**
- **Method**: `POST`
- **URL**: `{{base_url}}/check-eligibility/`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
      "customer_id": 1,
      "loan_amount": 100000,
      "interest_rate": 10,
      "tenure": 12
  }
  ```

**Expected Response** (200 OK):
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": "10.00",
    "corrected_interest_rate": "10.00",
    "tenure": 12,
    "monthly_installment": "8792.59"
}
```

#### **✅ Test Case 2: High Risk Customer (Rate Correction)**

**Request:**
```json
{
    "customer_id": 2,
    "loan_amount": 200000,
    "interest_rate": 8,
    "tenure": 24
}
```

**Expected Response**: 
- `approval: true`
- `corrected_interest_rate` may be higher than requested rate
- Interest rate adjustment based on credit score

#### **❌ Test Case 3: Loan Amount Too High**

**Request:**
```json
{
    "customer_id": 1,
    "loan_amount": 5000000,
    "interest_rate": 10,
    "tenure": 12
}
```

**Expected Response**:
```json
{
    "customer_id": 1,
    "approval": false,
    "interest_rate": "10.00",
    "corrected_interest_rate": "0.00",
    "tenure": 12,
    "monthly_installment": "0.00"
}
```

#### **❌ Test Case 4: Non-Existent Customer**

**Request:**
```json
{
    "customer_id": 9999,
    "loan_amount": 100000,
    "interest_rate": 10,
    "tenure": 12
}
```

**Expected Response** (404 Not Found):
```json
{
    "error": "Customer not found"
}
```

---

### **3️⃣ Create Loan API**

**Endpoint**: `POST {{base_url}}/create-loan/`

#### **✅ Test Case 1: Successful Loan Creation**

**Request:**
- **Method**: `POST`
- **URL**: `{{base_url}}/create-loan/`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
      "customer_id": 1,
      "loan_amount": 75000,
      "interest_rate": 8,
      "tenure": 10
  }
  ```

**Expected Response** (200 OK):
```json
{
    "loan_id": 7799,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved successfully",
    "monthly_installment": "9107.25"
}
```

**Validation Points:**
- ✅ Status Code: `200`
- ✅ `loan_approved: true`
- ✅ Valid `loan_id` returned
- ✅ Calculated `monthly_installment`

#### **❌ Test Case 2: Loan Rejection (High Risk)**

**Request:**
```json
{
    "customer_id": 50,
    "loan_amount": 800000,
    "interest_rate": 5,
    "tenure": 60
}
```

**Expected Response** (200 OK):
```json
{
    "loan_id": null,
    "customer_id": 50,
    "loan_approved": false,
    "message": "Loan not approved due to high risk",
    "monthly_installment": "0.00"
}
```

#### **❌ Test Case 3: EMI Limit Exceeded**

**Request:**
```json
{
    "customer_id": 1,
    "loan_amount": 1000000,
    "interest_rate": 15,
    "tenure": 12
}
```

**Expected Response**:
- `loan_approved: false`
- Message about EMI exceeding 50% of salary

---

### **4️⃣ View Loan Details API**

**Endpoint**: `GET {{base_url}}/view-loan/{loan_id}/`

#### **✅ Test Case 1: Existing Loan**

**Request:**
- **Method**: `GET`
- **URL**: `{{base_url}}/view-loan/7798/`
- **Headers**: None required

**Expected Response** (200 OK):
```json
{
    "loan_id": 7798,
    "customer": {
        "customer_id": 1,
        "first_name": "Aaron",
        "last_name": "Garcia",
        "phone_number": 9629317944,
        "age": 63
    },
    "loan_amount": "900000.00",
    "interest_rate": "17.92",
    "monthly_repayment": "39978.00",
    "tenure": 138
}
```

#### **❌ Test Case 2: Non-Existent Loan**

**Request:**
- **Method**: `GET`
- **URL**: `{{base_url}}/view-loan/99999/`

**Expected Response** (404 Not Found):
```json
{
    "error": "Loan not found"
}
```

---

### **5️⃣ View Customer Loans API**

**Endpoint**: `GET {{base_url}}/view-loans/{customer_id}/`

#### **✅ Test Case 1: Customer with Active Loans**

**Request:**
- **Method**: `GET`
- **URL**: `{{base_url}}/view-loans/1/`
- **Headers**: None required

**Expected Response** (200 OK):
```json
[
    {
        "loan_id": 7798,
        "loan_amount": "900000.00",
        "interest_rate": "17.92",
        "monthly_installment": "39978.00",
        "repayments_left": 52
    }
]
```

#### **✅ Test Case 2: Customer with No Active Loans**

**Request:**
- **Method**: `GET`
- **URL**: `{{base_url}}/view-loans/200/`

**Expected Response** (200 OK):
```json
[]
```

#### **❌ Test Case 3: Non-Existent Customer**

**Request:**
- **Method**: `GET`
- **URL**: `{{base_url}}/view-loans/9999/`

**Expected Response** (404 Not Found):
```json
{
    "error": "Customer not found"
}
```

---

## 🔄 **Complete Workflow Testing**

### **Scenario 1: New Customer Complete Journey**

**Step 1: Register New Customer**
```json
POST {{base_url}}/register/
{
    "first_name": "Test",
    "last_name": "User",
    "age": 35,
    "phone_number": 9999999999,
    "monthly_income": 60000
}
```
*Save the returned `customer_id` for next steps*

**Step 2: Check Eligibility**
```json
POST {{base_url}}/check-eligibility/
{
    "customer_id": [customer_id_from_step1],
    "loan_amount": 150000,
    "interest_rate": 10,
    "tenure": 18
}
```

**Step 3: Create Loan**
```json
POST {{base_url}}/create-loan/
{
    "customer_id": [customer_id_from_step1],
    "loan_amount": 150000,
    "interest_rate": 10,
    "tenure": 18
}
```
*Save the returned `loan_id` for next steps*

**Step 4: View Loan Details**
```
GET {{base_url}}/view-loan/[loan_id_from_step3]/
```

**Step 5: View Customer's All Loans**
```
GET {{base_url}}/view-loans/[customer_id_from_step1]/
```

### **Scenario 2: Existing Customer Testing**

Use these existing customers for quick testing:
- **Customer ID 1**: Aaron Garcia (has existing loans)
- **Customer ID 2**: Abbie Rodrigues (high income)
- **Customer ID 3**: Abby Fernandez (different credit profile)

---

## 📝 **Postman Collection Setup**

### **Create Collection Structure:**
```
📁 Credit Approval System
├── 📁 1. Customer Registration
│   ├── ✅ Successful Registration
│   ├── ❌ Duplicate Phone Number
│   ├── ❌ Missing Required Fields
│   └── ❌ Invalid Data Types
├── 📁 2. Check Eligibility
│   ├── ✅ Eligible Customer
│   ├── ✅ High Risk Customer
│   ├── ❌ Amount Too High
│   └── ❌ Customer Not Found
├── 📁 3. Create Loan
│   ├── ✅ Successful Creation
│   ├── ❌ Loan Rejection
│   └── ❌ EMI Limit Exceeded
├── 📁 4. View Loan
│   ├── ✅ Existing Loan
│   └── ❌ Non-Existent Loan
├── 📁 5. View Customer Loans
│   ├── ✅ Customer with Loans
│   ├── ✅ Customer with No Loans
│   └── ❌ Non-Existent Customer
└── 📁 6. Complete Workflows
    ├── 🔄 New Customer Journey
    └── 🔄 Existing Customer Testing
```

---

## 🎯 **Testing Best Practices**

### **1. Pre-Request Scripts**
Add to collection/request level:
```javascript
// Set timestamp for unique data
pm.globals.set("timestamp", Date.now());

// Generate unique phone number
const uniquePhone = 9000000000 + Math.floor(Math.random() * 999999);
pm.globals.set("unique_phone", uniquePhone);
```

### **2. Response Validation Tests**
Add to Tests tab:
```javascript
// Test status code
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test response structure
pm.test("Response has required fields", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('customer_id');
    pm.expect(jsonData).to.have.property('name');
});

// Save response data for next requests
pm.test("Save customer_id", function () {
    const jsonData = pm.response.json();
    pm.globals.set("test_customer_id", jsonData.customer_id);
});
```

### **3. Environment Variables Usage**
Use variables in requests:
```json
{
    "customer_id": "{{test_customer_id}}",
    "phone_number": "{{unique_phone}}",
    "loan_amount": 100000
}
```

---

## 🔍 **Troubleshooting**

### **Common Issues & Solutions**

**Issue: Connection Refused**
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```
**Solution**: 
- Check if Docker containers are running: `docker-compose ps`
- Restart containers: `docker-compose up`

**Issue: 500 Internal Server Error**
**Solution**:
- Check container logs: `docker-compose logs web`
- Verify request format and required fields

**Issue: Empty Database**
**Solution**:
- Check if data ingestion completed in container logs
- Manually run: `docker-compose exec web python manage.py ingest_data`

**Issue: Invalid JSON Format**
**Solution**:
- Ensure `Content-Type: application/json` header is set
- Validate JSON syntax in request body

---

## 📊 **Expected Test Results Summary**

| API Endpoint | Total Tests | Pass | Fail | Coverage |
|-------------|-------------|------|------|----------|
| **Customer Registration** | 4 | 1 | 3 | Success & validation scenarios |
| **Check Eligibility** | 4 | 2 | 2 | Approval & rejection logic |
| **Create Loan** | 3 | 1 | 2 | Loan creation & risk assessment |
| **View Loan** | 2 | 1 | 1 | Data retrieval & error handling |
| **View Customer Loans** | 3 | 2 | 1 | List operations & filtering |
| **TOTAL** | **16** | **7** | **9** | **Complete API coverage** |

---

## 🎉 **Validation Checklist**

After running all tests, verify:

- [ ] ✅ Customer registration works with valid data
- [ ] ✅ Duplicate prevention works for phone numbers  
- [ ] ✅ Loan eligibility correctly calculates credit scores
- [ ] ✅ Interest rates adjust based on risk assessment
- [ ] ✅ EMI limits prevent over-borrowing (50% salary rule)
- [ ] ✅ Loan creation generates proper loan IDs
- [ ] ✅ Loan viewing shows complete customer and loan details
- [ ] ✅ Customer loan lists show only active loans
- [ ] ✅ Error handling returns proper 404/400 status codes
- [ ] ✅ All API responses follow consistent JSON structure

---

## 📞 **Support & Documentation**

- **API Documentation**: Available in the system
- **Admin Panel**: http://localhost:8000/admin/ for data verification
- **Container Logs**: `docker-compose logs web` for debugging
- **Database Verification**: Use admin panel to check created records

**The Credit Approval System is now fully testable with comprehensive Postman test scenarios!** 🚀