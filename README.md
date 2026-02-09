# Insurance Claims Processing Agent

An autonomous AI-powered agent that extracts key fields from First Notice of Loss (FNOL) documents, validates data completeness, classifies claims, and intelligently routes them to appropriate processing queues.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Routing Rules](#routing-rules)
- [Field Extraction](#field-extraction)
- [Usage Examples](#usage-examples)
- [Sample Documents](#sample-documents)
- [Output Format](#output-format)
- [Testing & Verification](#testing--verification)
- [Project Structure](#project-structure)
- [Approach & Design](#approach--design)

---

## 🎯 Overview

This autonomous agent processes insurance claim documents (FNOL - First Notice of Loss) by:
1. **Extracting** structured data from unstructured text documents
2. **Identifying** missing or incomplete mandatory fields
3. **Classifying** the type of claim (collision, bodily injury, property damage, etc.)
4. **Routing** claims to appropriate processing queues based on business rules
5. **Providing** clear reasoning for all routing decisions

**Supported Document Formats:**
- Plain text (.txt)
- PDF documents (.pdf) - via pdfplumber/PyPDF2
- ACORD form structure
- Standard claim format

---

## ✨ Key Features

- ✅ **Comprehensive Field Extraction** - Extracts 20+ fields including policy info, incident details, parties involved, and asset information
- ✅ **Intelligent Routing** - Priority-based routing rules ensure claims reach the right queue
- ✅ **Missing Field Detection** - Automatically identifies incomplete claims
- ✅ **Fraud Detection** - Flags suspicious claims containing fraud-related keywords
- ✅ **JSON Output** - Structured output format for easy integration
- ✅ **CLI Interface** - Process single files, folders, or batch operations
- ✅ **High Confidence Scoring** - Provides extraction confidence scores
- ✅ **Professional ACORD Support** - Handles industry-standard ACORD forms

---

## 💻 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM
- **Storage**: 50MB for application and dependencies

---

## 🚀 Installation

### Step 1: Clone or Download the Project

```bash
git clone https://github.com/siddharthgupta5/Autonomous-Insurance-Claims-Processing-Agent.git
```

### Step 2: Create Virtual Environment in the project (Recommended)

```bash
# Create virtual environment
python -m venv myenv

# Activate virtual environment
# On Windows:
.\myenv\Scripts\Activate.ps1
# On macOS/Linux:
source myenv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- `pdfplumber` - PDF text extraction
- `PyPDF2` - Fallback PDF processor

---

## 🏃 Quick Start

### Process a Single Claim

```bash
python cli.py --file samples/sample_claim_collision.txt --display
```

### Process All Claims in a Folder

```bash
python cli.py --folder samples --display --format pretty
```

### Save Results to JSON File

```bash
python cli.py --file samples/sample_claim_bodily_injury.txt --output result.json
```

### Batch Processing

```bash
python cli.py --folder samples --output batch_results.json
```

---

## 📊 Routing Rules

The agent uses **priority-based routing** to determine the appropriate processing queue:

### Priority Order: 4.4 → 4.3 → 4.2 → 4.1 → Default

| Priority | Rule | Condition | Route Destination |
|----------|------|-----------|-------------------|
| **1st** | **Rule 4.4** | Claim Type = Bodily Injury | `SPECIALIST_QUEUE` |
| **2nd** | **Rule 4.3** | Description contains fraud keywords<br>("fraud", "inconsistent", "staged") | `INVESTIGATION_FLAG` |
| **3rd** | **Rule 4.2** | Any mandatory field is missing | `MANUAL_REVIEW` |
| **4th** | **Rule 4.1** | Estimated damage < $25,000 | `FAST_TRACK` |
| **Default** | - | No rules match | `STANDARD_PROCESSING` |

### Routing Logic Examples

**Example 1: Bodily Injury with Low Damage**
- Damage: $15,000 (< $25k)
- Claim Type: Bodily Injury
- **Result**: `SPECIALIST_QUEUE` (Rule 4.4 takes priority over 4.1)

**Example 2: Fraud Keywords with Missing Fields**
- Missing Fields: Yes
- Keywords: "staged accident"
- **Result**: `INVESTIGATION_FLAG` (Rule 4.3 takes priority over 4.2)

**Example 3: Complete Claim with High Damage**
- Damage: $50,000 (> $25k)
- All fields present, no fraud, not injury
- **Result**: `STANDARD_PROCESSING` (Default route)

---

## 📝 Field Extraction

### Required Fields Extracted

#### 1. Policy Information
- Policy Number
- Policyholder Name
- Effective Date
- Expiration Date

#### 2. Incident Information
- Date of Loss
- Time of Loss
- Location of Loss
- Incident Description

#### 3. Involved Parties
- Claimant Name
- Claimant Contact (Phone, Email)
- Third Party Name
- Third Party Contact

#### 4. Asset Details
- Asset Type (Vehicle Make/Model or Property Type)
- Asset ID (VIN or Property ID)
- Estimated Damage Amount

#### 5. Other Mandatory Fields
- Claim Type (Collision, Bodily Injury, Property Damage, etc.)
- Attachments (List of supporting documents)
- Initial Estimate

---

## 📖 Usage Examples

### Example 1: Basic Processing

```bash
python cli.py --file samples/sample_claim_collision.txt --display --format pretty
```

**Output:**
```
Recommended Route: FAST_TRACK
Confidence Score: 95.0%
Reasoning: Estimated damage ($18,500.00) qualifies for fast-track processing

Extracted Fields Summary:
  Policy: POL-2024-001234
  Policyholder: John David Smith
  Incident Date: January 15, 2024
  Estimated Damage: $18,500.00
```

### Example 2: JSON Output

```bash
python cli.py --file samples/sample_claim_bodily_injury.txt --format json --display
```

**Output:**
```json
{
  "extractedFields": {
    "policy_info": {
      "policy_number": "POL-2024-003415",
      "policyholder_name": "Patricia Ellen Martinez",
      ...
    },
    ...
  },
  "missingFields": [],
  "recommendedRoute": "specialist_queue",
  "reasoning": "Bodily injury claims require specialist review"
}
```

### Example 3: Batch Processing Multiple Files

```bash
python cli.py --folder samples --output all_results.json
```

Processes all documents in the `samples/` folder and saves combined results.

---

## 📂 Sample Documents

The project includes **5 sample documents** demonstrating all routing rules:

### 1. **sample_claim_collision.txt** - Fast-track Route
- **Policy**: POL-2024-001234
- **Damage**: $18,500
- **Route**: `FAST_TRACK` (Rule 4.1: Damage < $25k)
- **Description**: Standard collision claim with complete information

### 2. **sample_claim_bodily_injury.txt** - Specialist Queue
- **Policy**: POL-2024-003415
- **Damage**: $35,000
- **Route**: `SPECIALIST_QUEUE` (Rule 4.4: Bodily injury)
- **Description**: Rear-end collision with passenger injuries requiring medical treatment

### 3. **sample_claim_water_damage.txt** - Standard Processing
- **Policy**: POL-2024-002856
- **Damage**: $47,300
- **Route**: `STANDARD_PROCESSING` (No rules match)
- **Description**: Property damage from burst pipe, all fields complete, high damage amount

### 4. **sample_fraud_test.txt** - Investigation Flag
- **Policy**: POL-2024-TEST123
- **Damage**: $15,000
- **Route**: `INVESTIGATION_FLAG` (Rule 4.3: Fraud keywords detected)
- **Description**: Contains suspicious keywords: "staged", "inconsistent", "fraud"

### 5. **sample_missing_fields.txt** - Manual Review
- **Policy**: POL-2024-INCOMPLETE
- **Damage**: Missing
- **Route**: `MANUAL_REVIEW` (Rule 4.2: Missing mandatory field)
- **Description**: Incomplete claim missing estimated damage amount

---

## 📤 Output Format

### JSON Structure

```json
{
  "extractedFields": {
    "policy_info": {
      "policy_number": "POL-2024-001234",
      "policyholder_name": "John David Smith",
      "policy_effective_date": "06/15/2023",
      "policy_expiration_date": "06/15/2024",
      "insurance_company": null
    },
    "incident_info": {
      "incident_date": "January 15, 2024",
      "incident_time": "2:30 PM",
      "incident_location": "Intersection of Main Street and Oak Avenue",
      "incident_description": "Vehicle struck by third-party...",
      "weather_conditions": null
    },
    "involved_parties": [
      {
        "name": "John David Smith",
        "relationship": "claimant",
        "contact_phone": "555-0123",
        "contact_email": "jsmith@email.com",
        "address": null
      }
    ],
    "asset_details": {
      "asset_type": "2020 Honda Accord",
      "asset_id": "1HGCV1F30MA123456",
      "estimated_damage": 18500.0
    },
    "claim_type": "collision",
    "initial_estimate": 18500.0,
    "attachments": ["Photos", "Police Report #SPD-2024-00145", "Repair estimate"]
  },
  "missingFields": [],
  "recommendedRoute": "fast_track",
  "reasoning": "Estimated damage ($18,500.00) qualifies for fast-track processing",
  "flags": [],
  "confidenceScore": 0.95,
  "processingTimestamp": "2026-02-09T16:15:00.000000"
}
```

---

## 🧪 Testing & Verification

### Run All Sample Tests

```bash
python cli.py --folder samples --display --format pretty
```

**Expected Output**: All 5 samples process successfully with correct routing

### Run Unit Tests

**Option 1: Using Built-in unittest (No additional dependencies)**
```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_processor -v
```

**Option 2: Using pytest (Optional - Better output)**
```bash
# Install pytest first
pip install pytest

# Run all tests
python -m pytest tests/ -v
```

**Tests Include:**
- Field extraction for all 20+ fields
- All 4 routing rules with priority order (4.4 > 4.3 > 4.2 > 4.1)
- Edge cases and default routing
- PDF processing functionality

### Expected Test Results

All 5 sample documents should process successfully:
- ✅ Fast-track route (Rule 4.1)
- ✅ Manual review route (Rule 4.2)
- ✅ Investigation flag route (Rule 4.3)
- ✅ Specialist queue route (Rule 4.4)
- ✅ Standard processing (Default)

---

## 📁 Project Structure

```
claims_agent/
├── src/                          # Core application 
│   ├── __init__.py               # Package initialization
│   ├── models.py                 # Data models & enums 
│   ├── extractor.py              # Field extraction logic 
│   ├── router.py                 # Routing rules engine 
│   └── processor.py              # Main orchestrator 
├── samples/                      # Sample documents 
│   ├── sample_claim_collision.txt      # Fast-track scenario
│   ├── sample_claim_bodily_injury.txt  # Specialist queue scenario
│   ├── sample_claim_water_damage.txt   # Standard processing scenario
│   ├── sample_fraud_test.txt           # Investigation flag scenario
│   └── sample_missing_fields.txt       # Manual review scenario
├── tests/                        # Testing
│   ├── __init__.py               # Test package init
│   └── test_processor.py         # comprehensive tests 
├── docs/                         # Technical documentation 
│   ├── ARCHITECTURE.md          
│   └── IMPLEMENTATION.md         
├── cli.py                        # Command-line interface 
├── requirements.txt              # Dependencies 
├── .gitignore                    # Git ignore rules
└── README.md                     # Complete user guide 
```

---

## 🧠 Approach & Design

### Architecture Overview

The system follows a **clean, modular pipeline architecture** with minimal dependencies:

```
┌─────────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐
│   Input     │───►│ Extractor │───►│  Router  │───►│   Output   │
│  Document   │    │ (Patterns)│    │ (Rules)  │    │   (JSON)   │
└─────────────┘    └───────────┘    └──────────┘    └────────────┘
      │                   │                │                │
   Text/PDF        Field Extraction   Priority Logic    Structured
                   20+ Fields         4 Rules + Default    Data
```

### Core Components

#### 1. **Extraction Layer** (`extractor.py`)
- **Regex Patterns**: Optimized for ACORD forms and plain text formats
- **Multi-Pattern Strategy**: 2-3 fallback patterns per field for robustness
- **Line Break Preservation**: Maintains structure critical for form parsing
- **Confidence Scoring**: Tracks extraction reliability (0.0-1.0 per field)
- **Smart Normalization**: Cleans text while preserving meaningful structure

**Key Fields Extracted:**
- Policy info (number, holder, dates)
- Incident details (date, time, location, description)
- Involved parties (claimant, third parties, contacts)
- Asset details (type, ID/VIN, damage estimates)
- Claim metadata (type, attachments, estimates)

#### 2. **Data Layer** (`models.py`)
- **Type Safety**: Python dataclasses with complete type hints
- **7 Enums**: ClaimType (COLLISION, BODILY_INJURY, etc.)
- **5 Routes**: ClaimRoute (FAST_TRACK, MANUAL_REVIEW, etc.)
- **Hierarchical Structure**: Policy → Incident → Parties → Assets → Output
- **JSON Serialization**: Native conversion to/from dictionaries

#### 3. **Routing Layer** (`router.py`)
- **Priority-Based Logic**: Explicit precedence (4.4 → 4.3 → 4.2 → 4.1 → Default)
- **Flag System**: FRAUD_FLAG, MISSING_MANDATORY_FIELDS, SPECIALIZATION_REQUIRED
- **Mandatory Field Validation**: Checks 8 critical fields
- **Fraud Detection**: 3 keywords ("fraud", "staged", "inconsistent")
- **Reasoning Engine**: Generates human-readable explanations

**Routing Priority Order:**
```
1. Bodily Injury        → SPECIALIST_QUEUE     (Rule 4.4)
2. Fraud Keywords       → INVESTIGATION_FLAG   (Rule 4.3)
3. Missing Fields       → MANUAL_REVIEW        (Rule 4.2)
4. Damage < $25k        → FAST_TRACK           (Rule 4.1)
5. No Match             → STANDARD_PROCESSING  (Default)
```

#### 4. **Processing Layer** (`processor.py`)
- **Orchestration**: Chains extractor → router → formatter
- **Multi-Format Support**: Text files + PDF 
- **Batch Processing**: Process entire folders efficiently
- **Error Handling**: Graceful degradation for malformed inputs
- **Output Formats**: JSON (structured) or Pretty (human-readable)


### Key Design Decisions

#### 1. Pattern Matching Over ML/AI
**Why:** Fast, deterministic, no API costs, fully transparent
- Regex patterns process documents in very less time
- No network calls, no rate limits
- Easy to debug and customize patterns
- Can enhance with AI later if needed

#### 2. Priority-Based Routing
**Why:** Eliminates ambiguity when multiple rules match
- Medical safety first (bodily injury → specialists)
- Risk mitigation second (fraud → investigation)
- Data completeness third (missing fields → manual)
- Cost optimization last (low damage → fast-track)

#### 3. ACORD Form Optimization
**Why:** Industry-standard insurance form format
- Patterns recognize "label\n  value" structure
- Preserves line breaks during normalization
- Multiple fallback patterns for variations

#### 4. Modular Architecture
**Why:** Each layer has single responsibility
- Easy to test components independently
- Can swap extraction methods (regex → ML → LLM)
- Can add new routes without touching extraction
- Can change output format without changing logic

---

