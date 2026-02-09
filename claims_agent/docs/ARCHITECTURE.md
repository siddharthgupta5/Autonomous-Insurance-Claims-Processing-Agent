# Architecture Decision Records

## ADR-001: Python for Core Implementation

**Status**: Accepted

**Context**: 
The claims processing agent needed a programming language that supports rapid development, has strong text processing capabilities, and integrates well with popular ML/AI frameworks.

**Decision**: 
Use Python 3.8+ as the primary implementation language.

**Consequences**:
- ✓ Rapid development cycle
- ✓ Extensive regex and NLP libraries available
- ✓ Easy integration with OpenAI/Anthropic APIs
- ✓ Strong data processing ecosystem (pandas, etc.)
- ✗ Runtime performance slightly slower than compiled languages
- ✗ Requires Python environment setup

---

## ADR-002: Regex-Based Field Extraction

**Status**: Accepted

**Context**:
Multiple approaches were considered for extracting fields from unstructured documents:
1. Simple regex patterns
2. Machine learning models
3. Large language models (GPT-4)
4. Hybrid approach

**Decision**:
Implement regex-based extraction as primary method, with extensible architecture for ML/LLM alternatives.

**Rationale**:
- Regex approach: Fast, deterministic, low cost, no API dependencies
- ML models: Slower development, requires training data
- LLMs: High cost per API call, but highest accuracy

**Consequences**:
- ✓ Fast extraction (50-100ms per document)
- ✓ No external dependencies or API costs
- ✓ Transparent extraction (easy to debug)
- ✗ Lower accuracy on varied document formats
- → Documents can be enhanced with AI when accuracy is critical

---

## ADR-003: Modular Routing Engine

**Status**: Accepted

**Context**:
Different insurance companies have different routing rules. The system needed to be flexible for company-specific requirements.

**Decision**:
Implement a modular routing architecture with configurable rules and clear priorities.

**Rule Priority Order**:
1. **Rule 4.4**: Bodily injury claims → Specialist Queue (highest priority)
2. **Rule 4.3**: Fraud indicators → Investigation Flag
3. **Rule 4.2**: Missing mandatory fields → Manual Review
4. **Rule 4.1**: Damage < $25,000 → Fast-track
5. **Default**: Standard Processing

**Consequences**:
- ✓ Easy to customize for different companies
- ✓ Clear, auditable decision logic
- ✓ Extensible for additional rule types
- ✗ May need database for complex rules

---

## ADR-004: JSON Output Format

**Status**: Accepted

**Context**:
Results needed to integrate with downstream systems and be easily parseable by various tools.

**Decision**:
Use JSON as the standard output format with consistent field naming.

**Consequences**:
- ✓ Language-agnostic format
- ✓ Easy integration with web services
- ✓ Human-readable and machine-readable
- ✓ Standard parsing libraries available everywhere

---

## ADR-005: Confidence Scoring

**Status**: Accepted

**Context**:
Users need to understand how reliable the extraction is for each field.

**Decision**:
Include confidence scores (0-1.0) for each extracted field and routing decision.

**Methodology**:
- Field extraction: 0.95 if found, 0.0 if missing
- Routing decision: 0.80-0.95 based on rule certainty
- Overall: Weighted average of component scores

**Consequences**:
- ✓ Users can threshold on confidence
- ✓ Low-confidence extractions can trigger manual review
- ✓ Enables active learning for ML enhancement
- ✗ Scoring tuning required for accuracy

---

## ADR-006: CLI First, API Layer Second

**Status**: Accepted

**Context**:
The system needed to be usable both from command line and as a library.

**Decision**:
Implement core as importable Python modules, with CLI as a wrapper using argparse.

**Consequences**:
- ✓ Flexible usage (CLI, Python API, REST API, etc.)
- ✓ Single implementation, multiple interfaces
- ✓ Easy to add REST endpoint using Flask/FastAPI
- ✓ Core logic independent of interface

---

## ADR-007: Test Coverage Strategy

**Status**: Accepted

**Context**:
Given this is a production system, tests needed to cover the critical paths.

**Decision**:
Implement unit tests for:
- Field extraction (individual field patterns)
- Routing logic (each routing rule)
- End-to-end processing

**Target Coverage**: 80%+ for critical paths

**Consequences**:
- ✓ Confidence in core functionality
- ✓ Easier to refactor without breaking changes
- ✗ Requires ongoing maintenance

---

## Future Enhancements

See README.md "Enhancement Opportunities" section for planned improvements:
- AI-powered extraction using LLMs
- Multi-format support (PDF, Word, HTML)
- Custom rules engine
- Database integration
- Audit trail and analytics
