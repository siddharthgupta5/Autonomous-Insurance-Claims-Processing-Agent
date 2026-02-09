# Implementation Guide

## Development Setup

### 1. Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd claims_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

### 2. Project Structure

```
claims_agent/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── models.py            # Data structures (128 lines)
│   ├── extractor.py         # Field extraction (354 lines)
│   ├── router.py            # Routing logic (173 lines)
│   └── processor.py         # Orchestration (160 lines)
├── tests/
│   ├── __init__.py
│   └── test_processor.py    # Unit tests (200+ lines)
├── docs/
│   ├── ARCHITECTURE.md      # Design decisions
│   └── IMPLEMENTATION.md    # This file
├── samples/
│   ├── sample_claim_collision.txt
│   ├── sample_claim_bodily_injury.txt
│   ├── sample_claim_water_damage.txt
│   ├── sample_fraud_test.txt
│   └── sample_missing_fields.txt
├── cli.py                   # Command-line interface
├── requirements.txt         # Dependencies
├── README.md                # User documentation
└── .gitignore              # Git ignore rules
```

### 3. Component Details

#### models.py (Data Structures)
- **PolicyInfo**: Policy details (policy_number, policyholder_name, dates)
- **IncidentInfo**: Loss details (date, time, location, description)
- **AssetDetails**: Property/vehicle info (type, ID, damage amount)
- **InvolvedParty**: People information (name, relationship, contact)
- **ClaimData**: Complete claim structure
- **ClaimRoute**: Routing destination enum (5 options)
- **ClaimProcessingResult**: Final output structure

**Extensibility**: Add new fields by extending dataclasses with `@dataclass` decorator.

#### extractor.py (Field Extraction)
- **FieldExtractor**: Main extraction class
- **_extract_field()**: Generic regex-based extraction with confidence
- **_extract_policy_info()**: Policy fields
- **_extract_incident_info()**: Incident fields
- **_extract_asset_details()**: Asset fields
- **_extract_parties()**: Involved people
- **_calculate_confidence_scores()**: Field-level confidence

**Pattern Additions**:
```python
# Add new extraction pattern in PATTERNS dict
PATTERNS = {
    "field_name": [
        r"pattern1",
        r"pattern2",
    ],
}

# Add extraction method
def _extract_field_name(self, text: str) -> Optional[str]:
    value, conf = self._extract_field(text, self.PATTERNS["field_name"])
    return value
```

#### router.py (Routing Logic)
- **ClaimRouter**: Routes claims to appropriate queues
- **_identify_missing_fields()**: Checks mandatory field presence
- **_check_fraud_indicators()**: Detects fraud keywords
- **_route_by_damage()**: Damage threshold-based routing
- **_determine_route()**: Priority-based final routing (4.4 → 4.3 → 4.2 → 4.1)

**Configurable Parameters**:
```python
FAST_TRACK_THRESHOLD = 25000        # $25k for fast-track routing
FRAUD_KEYWORDS = [...]              # Keywords to flag for investigation
```

**Routing Priority**:
1. Bodily injury → SPECIALIST_QUEUE (Rule 4.4)
2. Fraud keywords → INVESTIGATION_FLAG (Rule 4.3)
3. Missing fields → MANUAL_REVIEW (Rule 4.2)
4. Damage < $25k → FAST_TRACK (Rule 4.1)
5. Default → STANDARD_PROCESSING

#### processor.py (Orchestration)
- **ClaimProcessor**: Main entry point
- **process_document()**: Process text directly
- **process_file()**: Process file (handles PDF, TXT, etc.)
- **process_batch()**: Process multiple files
- **export_result()**: Format output (JSON or dict)

**PDF Support**:
- Primary: `pdfplumber` (better text extraction)
- Fallback: `PyPDF2`

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_processor.py::TestClaimRouter::test_fast_track_routing_low_damage

# Run verbose
pytest -v tests/
```

### Test Categories

1. **Extraction Tests** (test_processor.py)
   - Policy number extraction
   - Date extraction
   - Amount extraction
   - Claim type classification

2. **Routing Tests** (test_processor.py)
   - Fast-track routing
   - Manual review routing
   - Specialist queue routing
   - Fraud detection

3. **Integration Tests** (test_processor.py)
   - Full document processing
   - JSON output formatting
   - Batch processing

### Adding Tests

```python
def test_new_extraction(self):
    """Test new field extraction."""
    text = "Your test text with field data"
    claim_data = self.extractor.extract_from_text(text)
    self.assertEqual(claim_data.field_name, expected_value)
```

## Command Line Usage

### Basic Commands

```bash
# Single file
python cli.py --file document.txt

# Multiple files
python cli.py --folder ./claims/

# With output
python cli.py --file claim.pdf --output result.json

# Pretty display
python cli.py --file claim.txt --display --format pretty
```

### Output Examples

**JSON Format** (default):
```json
{
  "extractedFields": {...},
  "missingFields": [],
  "recommendedRoute": "fast_track",
  ...
}
```

**Pretty Format**:
```
Recommended Route: FAST_TRACK
Confidence Score: 95.0%
Reasoning: Estimated damage ($28,500) qualifies for fast-track processing
```

## Python API Examples

### Basic Processing

```python
from src.processor import ClaimProcessor

processor = ClaimProcessor()

# Process text
result = processor.process_document(text)
print(result.recommended_route)
print(result.routing_reasoning)
```

### File Processing

```python
# Single file
result = processor.process_file("claim.pdf")

# Multiple files
results = processor.process_batch([
    "claim1.pdf",
    "claim2.txt",
    "claim3.pdf"
])

# Save results
for i, result in enumerate(results):
    processor.export_to_file(result, f"output/claim_{i}.json")
```

### Accessing Extracted Data

```python
result = processor.process_document(text)

# Access extracted fields
fields = result.extracted_fields
policy_num = fields['policy_info']['policy_number']
damage = fields['asset_details']['estimated_damage']
claim_type = fields['claim_type']

# Check completeness
missing = result.missing_fields
if missing:
    print(f"Missing: {missing}")

# Check flags
if 'FRAUD_FLAG' in result.flags:
    print("Fraud investigation required")
```

## Integration Patterns

### REST API (Flask)

```python
from flask import Flask, request, jsonify
from src.processor import ClaimProcessor

app = Flask(__name__)
processor = ClaimProcessor()

@app.route('/claim/process', methods=['POST'])
def process_claim():
    text = request.json.get('document_text')
    result = processor.process_document(text)
    return jsonify(result.to_json_dict())

if __name__ == '__main__':
    app.run(port=5000)
```

### Message Queue (Celery)

```python
from celery import Celery
from src.processor import ClaimProcessor
import redis

app = Celery('claims_agent', broker='redis://localhost:6379')
processor = ClaimProcessor()

@app.task
def process_claim_async(file_path: str):
    result = processor.process_file(file_path)
    # Store in database
    store_result(result)
    return result.to_json_dict()
```

### Database Integration

```python
from sqlalchemy import create_engine, Column, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ClaimResult(Base):
    __tablename__ = 'claim_results'
    
    id = Column(String, primary_key=True)
    extracted_fields = Column(JSON)
    recommended_route = Column(String)
    missing_fields = Column(JSON)
    confidence_score = Column(Float)

# Usage
engine = create_engine('postgresql://user:pass@localhost/claims')
Session = sessionmaker(bind=engine)
session = Session()

result = processor.process_file('claim.pdf')
db_record = ClaimResult(
    id=generate_id(),
    extracted_fields=result.extracted_fields,
    recommended_route=result.recommended_route,
    missing_fields=result.missing_fields,
    confidence_score=result.confidence_score
)
session.add(db_record)
session.commit()
```

## Debugging

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add to components
logger.debug(f"Extracted: {value}")
logger.warning(f"Low confidence: {field}")
```

### Inspection Tools

```python
from src.processor import ClaimProcessor
from src.extractor import FieldExtractor

processor = ClaimProcessor()
result = processor.process_document(text)

# Inspect extraction confidence
print(result.extracted_fields['extraction_confidence'])

# Inspect routing decision
print(f"Route: {result.recommended_route}")
print(f"Confidence: {result.confidence_score}")
print(f"Flags: {result.flags}")
```

## Performance Optimization

### Extraction Speed
- Typical: 50-100ms per document
- Acceptable for real-time processing
- Batch processing can process 10 documents/second

### Memory Usage
- Per document: ~1-2 MB
- For 1000 documents: 1-2 GB
- Suitable for serverless (256MB+ allowed)

### Scaling Recommendations
- **Scale-up**: Use process pools or async workers
- **Scale-out**: Use message queue (Celery + Redis)
- **Cache**: Cache extraction patterns if documents are similar

## Deployment

### Local Testing
```bash
python cli.py --folder samples/ --display
```

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "cli.py"]
```

### Serverless (AWS Lambda)
- Keep dependencies minimal
- Use lazy imports for optional features
- Package as zip with requirements
- Set memory to 512MB+

## Troubleshooting

### Issue: PDF extraction fails
**Solution**: Install pdfplumber
```bash
pip install pdfplumber
```

### Issue: Low confidence scores
**Solution**: 
1. Check document format
2. Ensure fields follow standard formats
3. Add new regex patterns if needed

### Issue: Incorrect routing
**Solution**:
1. Check missing fields
2. Verify fraud keywords
3. Adjust thresholds in ClaimRouter

## Contributing

1. Add tests for new features
2. Maintain 80%+ coverage
3. Follow PEP 8 style guide
4. Update documentation
5. Test with sample documents

---

**See README.md for user documentation and architecture overview.**
