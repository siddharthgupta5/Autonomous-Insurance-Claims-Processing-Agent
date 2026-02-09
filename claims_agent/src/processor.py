"""Main claim processing orchestrator."""

import json
from typing import Dict, Union
from pathlib import Path

from .models import ClaimProcessingResult, ClaimData
from .extractor import FieldExtractor
from .router import ClaimRouter


class ClaimProcessor:
    """Orchestrates the full claim processing pipeline."""

    def __init__(self):
        """Initialize the processor with extractor and router."""
        self.extractor = FieldExtractor()
        self.router = ClaimRouter()

    def process_document(self, text: str) -> ClaimProcessingResult:
        """
        Process a claim document from text.

        Args:
            text: Raw text from FNOL document

        Returns:
            ClaimProcessingResult with extraction, routing, and reasoning
        """
        # Step 1: Extract claim information
        claim_data = self.extractor.extract_from_text(text)

        # Step 2: Determine routing
        routing_decision = self.router.route_claim(claim_data)

        # Step 3: Identify missing fields
        missing_fields = self.router._identify_missing_fields(claim_data)

        # Step 4: Build result
        result = ClaimProcessingResult(
            extracted_fields=claim_data.to_dict(),
            missing_fields=missing_fields,
            recommended_route=routing_decision.recommended_route.value,
            routing_reasoning=routing_decision.reasoning,
            flags=routing_decision.flags,
            confidence_score=routing_decision.confidence_score,
        )

        return result

    def process_file(self, file_path: str) -> ClaimProcessingResult:
        """
        Process a claim document from a file.

        Args:
            file_path: Path to the document file

        Returns:
            ClaimProcessingResult
        """
        path = Path(file_path)
        
        # For PDF files, we would typically use a PDF library
        # For now, this handles plain text files
        if path.suffix.lower() == ".pdf":
            text = self._extract_text_from_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        return self.process_document(text)

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Requires: pip install PyPDF2 or pdfplumber
        """
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                
                text = ""
                with open(file_path, "rb") as f:
                    pdf_reader = PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                return text
            except ImportError:
                raise ImportError(
                    "Please install PyPDF2 or pdfplumber for PDF support: "
                    "pip install PyPDF2 pdfplumber"
                )

    def process_batch(self, file_paths: list) -> list:
        """
        Process multiple claim documents.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of ClaimProcessingResult objects
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing {file_path}: {str(e)}")
                continue
        return results

    def export_result(
        self, result: ClaimProcessingResult, format: str = "json"
    ) -> Union[str, Dict]:
        """
        Export processing result in specified format.

        Args:
            result: ClaimProcessingResult to export
            format: Export format ('json' or 'dict')

        Returns:
            Formatted result
        """
        if format == "json":
            return json.dumps(result.to_json_dict(), indent=2)
        elif format == "dict":
            return result.to_json_dict()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_to_file(
        self, result: ClaimProcessingResult, output_path: str
    ) -> None:
        """
        Export result to JSON file.

        Args:
            result: ClaimProcessingResult to export
            output_path: Path to output file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.export_result(result, format="json"))
