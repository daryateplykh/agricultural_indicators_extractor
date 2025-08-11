import time
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pdf2image import convert_from_path
from PIL import Image

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scan_extractor_mistral import ScannedExtractorMistral
from paddle_comparison.scan_extractor_paddle import extract_text_paddle
from paddleocr import PaddleOCR
from config import Configuration


@dataclass
class PerformanceMetrics:
    processing_time: float
    text_length: int
    word_count: int
    char_count: int
    success_rate: float


class PerformanceComparator:
    
    def __init__(self):
        self.mistral_extractor = ScannedExtractorMistral()
        self.paddle_ocr = PaddleOCR(lang="en", use_textline_orientation=True)
        self.results = {}
        
    def compare_single_pdf(self, pdf_path: str, dpi: int = 200) -> Dict[str, PerformanceMetrics]:
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            return {}
            
        results = {}
        
        mistral_metrics = self._test_mistral(images)
        results['mistral'] = mistral_metrics
        
        paddle_metrics = self._test_paddle(images)
        results['paddle'] = paddle_metrics
        
        return results
    
    def _test_mistral(self, images: List[Image.Image]) -> PerformanceMetrics:
        start_time = time.time()
        total_text = ""
        successful_pages = 0
        
        for i, image in enumerate(images):
            try:
                extracted_text = self.mistral_extractor.extract_text_mistral(image, i)
                if extracted_text.strip():
                    total_text += extracted_text + "\n"
                    successful_pages += 1
            except Exception as e:
                continue
        
        processing_time = time.time() - start_time
        success_rate = successful_pages / len(images) if images else 0.0
        
        return PerformanceMetrics(
            processing_time=processing_time,
            text_length=len(total_text),
            word_count=len(total_text.split()),
            char_count=len(total_text),
            success_rate=success_rate
        )
    
    def _test_paddle(self, images: List[Image.Image]) -> PerformanceMetrics:
        start_time = time.time()
        total_text = ""
        successful_pages = 0
        
        for i, image in enumerate(images):
            try:
                extracted_text = extract_text_paddle(self.paddle_ocr, image)
                
                if extracted_text:
                    total_text += extracted_text + "\n"
                    successful_pages += 1
            except Exception as e:
                continue
        
        processing_time = time.time() - start_time
        success_rate = successful_pages / len(images) if images else 0.0
        
        return PerformanceMetrics(
            processing_time=processing_time,
            text_length=len(total_text),
            word_count=len(total_text.split()),
            char_count=len(total_text),
            success_rate=success_rate
        )
    
    def compare_all_pdfs(self, dpi: int = 200) -> Dict[str, Dict[str, PerformanceMetrics]]:
        Configuration.initialize()
        
        if not os.path.exists(Configuration.DATA_PATH):
            return {}
        
        pdf_files = [f for f in os.listdir(Configuration.DATA_PATH) if f.lower().endswith(".pdf")]
        
        if not pdf_files:
            return {}
        
        all_results = {}
        
        for filename in pdf_files:
            filepath = os.path.join(Configuration.DATA_PATH, filename)
            results = self.compare_single_pdf(filepath, dpi)
            if results:
                all_results[filename] = results
        
        return all_results
    
    def generate_report(self, results: Dict[str, Dict[str, PerformanceMetrics]]) -> str:
        if not results:
            return "No data for the report"
        
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE COMPARISON REPORT: MISTRAL vs PADDLEOCR")
        report.append("=" * 80)
        report.append("")
        
        total_mistral_time = 0
        total_paddle_time = 0
        total_mistral_text = 0
        total_paddle_text = 0
        total_mistral_success = 0
        total_paddle_success = 0
        
        for filename, file_results in results.items():
            report.append(f"FILE: {filename}")
            report.append("-" * 60)
            
            if 'mistral' in file_results:
                m = file_results['mistral']
                total_mistral_time += m.processing_time
                total_mistral_text += m.text_length
                total_mistral_success += m.success_rate
                
                report.append(f"MISTRAL:")
                report.append(f"Time: {m.processing_time:.2f} sec")
                report.append(f"Characters: {m.char_count:,}")
                report.append(f" Words: {m.word_count:,}")
                report.append(f"Success: {m.success_rate*100:.1f}%")
            
            if 'paddle' in file_results:
                p = file_results['paddle']
                total_paddle_time += p.processing_time
                total_paddle_text += p.text_length
                total_paddle_success += p.success_rate
                
                report.append(f"PADDLEOCR:")
                report.append(f"Time: {p.processing_time:.2f} sec")
                report.append(f"Characters: {p.char_count:,}")
                report.append(f"Words: {p.word_count:,}")
                report.append(f"Success: {p.success_rate*100:.1f}%")
            
            if 'mistral' in file_results and 'paddle' in file_results:
                m = file_results['mistral']
                p = file_results['paddle']
                
                time_diff = m.processing_time - p.processing_time
                text_diff = m.text_length - p.text_length
                
                report.append(f"COMPARISON:")
                if time_diff > 0:
                    report.append(f"PaddleOCR is faster by {time_diff:.2f} sec")
                else:
                    report.append(f"Mistral is faster by {abs(time_diff):.2f} sec")
                
                if text_diff > 0:
                    report.append(f"Mistral extracted {text_diff:,} more characters")
                else:
                    report.append(f"PaddleOCR extracted {abs(text_diff):,} more characters")
            
            report.append("")
        
        num_files = len(results)
        report.append("=" * 80)
        report.append("FINAL STATISTICS")
        report.append("=" * 80)
        
        if total_mistral_time > 0 and total_paddle_time > 0:
            speed_ratio = total_paddle_time / total_mistral_time
            report.append(f"PaddleOCR is {speed_ratio:.2f}x {'faster' if speed_ratio < 1 else 'slower'} than Mistral")
        
        report.append(f"Files processed: {num_files}")
        report.append(f"Total time Mistral: {total_mistral_time:.2f} sec")
        report.append(f"Total time PaddleOCR: {total_paddle_time:.2f} sec")
        report.append(f"Total text volume Mistral: {total_mistral_text:,} characters")
        report.append(f"Total text volume PaddleOCR: {total_paddle_text:,} characters")
        
        return "\n".join(report)
    
    def run_comparison(self, dpi: int = 200) -> str:
        results = self.compare_all_pdfs(dpi)
        report = self.generate_report(results)
        
        report_path = os.path.join(Configuration.OUTPUT_PATH, "performance_comparison_report.txt")
        os.makedirs(Configuration.OUTPUT_PATH, exist_ok=True)
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
        except Exception as e:
            pass
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance comparison of Mistral vs PaddleOCR")
    parser.add_argument('--dpi', type=int, default=200, help='DPI for PDF conversion')
    args = parser.parse_args()
    
    comparator = PerformanceComparator()
    report = comparator.run_comparison(dpi=args.dpi)
    

if __name__ == "__main__":
    main()
