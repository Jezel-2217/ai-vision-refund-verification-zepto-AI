# AI Vision Refund Verification System

An AI-powered refund verification system that uses **Gemini Vision, AWS S3, image preprocessing, Python business rules, and PostgreSQL** to automatically verify product-damage refund claims.

## 📌 Project Overview

When a customer reports that a product was damaged, the system analyzes the uploaded image instead of relying completely on manual verification.

For example:

**Customer Claim:** Milk packet is leaking

The AI Vision system analyzes the image and returns:

```text
Product      : Milk Packet
Damage       : Leak Detected
Confidence   : 98%
Recommendation: Approve Refund
```

The refund rules engine then converts the AI confidence score into a final business decision.

## 🎯 Objectives

* Analyze customer-uploaded product images
* Identify the product and visible damage
* Generate a confidence score
* Store uploaded images securely
* Validate the AI response
* Automatically approve, reject, or send claims for manual review
* Maintain an audit record for every refund claim

## 🔄 Project Workflow

```text
Customer Uploads Image
          ↓
Image Preprocessing
          ↓
AWS S3 Storage
          ↓
Gemini Vision API
          ↓
Structured JSON Response
          ↓
Response Validation
          ↓
Refund Rules Engine
          ↓
 ┌────────┼─────────┐
 ↓        ↓         ↓
Approve  Review    Reject
          ↓
   PostgreSQL Audit
```

## 🧠 AI Vision

Gemini Vision analyzes the uploaded product image and identifies:

* Product category
* Damage type
* Affected area
* Confidence score
* Recommended action

### Supported Damage Types

* Broken
* Cracked
* Leaking
* Expired
* Rotten
* Spoiled
* Missing item
* Wrong product
* Torn package
* Opened package
* Wet packaging
* Crushed product

### Supported Product Categories

* Vegetables
* Fruits
* Milk and dairy
* Eggs
* Snacks
* Packaged groceries
* Beverages
* Frozen foods
* Household products

## ⚙️ Refund Decision Rules

| Vision Confidence | Decision      | Action                          |
| ----------------- | ------------- | ------------------------------- |
| Above 95%         | Auto Approve  | Refund can be processed         |
| 70%–95%           | Manual Review | Human agent reviews the claim   |
| Below 70%         | Reject        | Customer can resubmit the claim |

The thresholds are configurable rather than hardcoded so that operations teams can change them when required.

## ☁️ AWS S3

Customer images are stored in AWS S3 using an organized structure:

```text
/refunds/{user_id}/{claim_id}/
```

This keeps images associated with the appropriate customer and refund claim.

## 🖼️ Image Preprocessing

The project uses:

* Pillow
* OpenCV

Preprocessing can include:

* Image resizing
* Image compression
* Format handling
* EXIF metadata removal
* Preparing images for Vision analysis

## 🤖 Prompt Engineering

The Gemini Vision prompt is designed to produce structured JSON instead of unrestricted text.

Example:

```json
{
  "product": "Milk Packet",
  "damage_type": "Leak Detected",
  "affected_area": "Bottom portion",
  "confidence": 98,
  "recommendation": "Approve Refund"
}
```

The response is parsed and validated before it reaches the refund rules engine.

## 🛡️ Response Validation

The system validates the Gemini response before making a refund decision.

If the response is malformed or does not match the expected structure:

```text
Gemini Response
      ↓
JSON Parsing
      ↓
Schema Validation
      ↓
Valid? ── No ──> Retry / Reject
  │
 Yes
  ↓
Rules Engine
```

This prevents invalid AI output from directly triggering a refund decision.

## 🗄️ PostgreSQL

Every refund claim is recorded for auditing.

Typical information includes:

```text
Claim ID
Customer ID
Order ID
S3 Image Key
Product
Damage Type
Confidence
Refund Decision
Timestamp
```

SQLAlchemy is used as the database layer.

## 🔌 API Endpoints

### Analyse Damage

```http
POST /analyse-damage
```

Returns:

```text
Product
Damage Type
Confidence
```

### Refund Decision

```http
POST /refund-decision
```

Returns the final business decision after applying the configured refund rules.

## 🛠️ Technologies Used

| Technology             | Purpose                |
| ---------------------- | ---------------------- |
| Python                 | Backend/service logic  |
| Gemini Vision API      | Image understanding    |
| Prompt Engineering     | Structured AI output   |
| Pillow                 | Image preprocessing    |
| OpenCV                 | Image processing       |
| AWS S3                 | Image storage          |
| PostgreSQL             | Refund audit database  |
| SQLAlchemy             | Database ORM           |
| JSON Schema/Validation | AI response validation |

## 📁 Project Structure

```text
src/
├── config.py
├── db.py
├── storage.py
├── image_preprocessing.py
├── vision.py
├── rules_engine.py
└── pipeline.py
```

### Module Responsibilities

**config.py**

* Application configuration
* API settings
* Database configuration
* Refund thresholds

**storage.py**

* AWS S3 image upload
* S3 path management

**image_preprocessing.py**

* Resize images
* Compress images
* Prepare images for AI analysis

**vision.py**

* Gemini Vision integration
* Prompt handling
* AI response parsing

**rules_engine.py**

* Apply confidence thresholds
* Approve, review, or reject claims

**db.py**

* PostgreSQL connection
* Store refund audit records
* Read/update refund thresholds

**pipeline.py**

* Connect the complete workflow together

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/ai-vision-refund-verification.git
cd ai-vision-refund-verification
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 🔐 Environment Variables

Create a `.env` file using `.env.example`.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
S3_BUCKET_NAME=your_bucket_name

DATABASE_URL=postgresql://username:password@localhost:5432/refund_verifications
```

**Never upload your real `.env` file or API keys to GitHub.**

## ▶️ Running the Project

After configuring the environment variables:

```bash
python app/app.py
```

The application can then accept a customer refund image and process it through the verification pipeline.

## 🧪 Example

### Input

```text
Customer reports:
"Milk packet is leaking"
```

### AI Analysis

```text
Product: Milk Packet
Damage: Leak Detected
Confidence: 98%
```

### Rules Engine

```text
98% > 95%
```

### Final Decision

```text
AUTO APPROVE
```

The claim is then recorded in PostgreSQL for auditing.

## 📊 Key Learning Outcomes

Through this project, I learned:

* AI Vision and multimodal AI concepts
* Gemini Vision API integration
* Prompt engineering
* Structured JSON output
* Image preprocessing
* AWS S3 integration
* Python backend development
* Business rules implementation
* PostgreSQL database integration
* SQLAlchemy
* API workflow design
* AI response validation
* Building an end-to-end AI application

## ⚠️ Important Note

This project is a learning/prototype implementation. AI-generated visual assessments should be validated against real business requirements before being used for automated financial decisions.

## 👩‍💻 Author

**Joice J**

AI / Data Science Project

---

⭐ If you find this project useful, consider giving the repository a star.
