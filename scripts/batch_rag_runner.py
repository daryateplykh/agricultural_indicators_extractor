import yaml
import re
import os
from datetime import datetime
from src.rag_core.rag_answer import query_rag
import pandas as pd
import logging

def format_number_with_commas(value, column_name=""):
    if column_name.lower() in ['year', 'год', 'year_']:
        return value
    
    if isinstance(value, str):
        cleaned = re.sub(r'[,\s]', '', value)
        try:
            num = float(cleaned)
            if num.is_integer():
                return f"{int(num):,}".replace(",", " ")
            else:
                return f"{num:,.2f}".replace(",", " ")
        except ValueError:
            return value
    return value

class BatchRAGRunner:
    def __init__(self, config_path):
        config_path = os.path.join('scripts', config_path)
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.queries = self.config["queries"]
        self.indicator_groups = self.config["indicator_groups"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"rag_outputs/rag_output_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        for q in self.queries:
            country = q["country"]
            years_config = q["years"]
            
            years = [yc["year"] for yc in years_config]
            output_years_map = {yc["year"]: yc.get("output_year") for yc in years_config}

            for group in self.indicator_groups:
                category = group["category"]
                indicators = group.get("indicators")
                if not indicators:
                    continue
                for indicator in indicators:
                    if indicator is None or not indicator.strip():
                        continue
                    
                    years_for_filename = [str(y) for y in years]

                    if len(years_for_filename) == 1:
                        question = f"What is the {indicator} in {country} in {years_for_filename[0]}?"
                        filename_suffix = f"{years_for_filename[0]}"
                    else:
                        years_str = " and ".join(years_for_filename)
                        question = f"What are the {indicator} data for {country} across {years_str}? Please provide all available data for both years, including any differences in parameters between the years."
                        filename_suffix = "_".join(years_for_filename)
                    
                    print(f"\n=== Question: {question}")
                    
                    first_year = years[0]
                    
                    answer = query_rag(question, country, first_year, save_csv=False)
                    print(f"RAG Answer for '{indicator}':\n{answer}")
                    
                    safe_country = re.sub(r"[^\w\-]", "_", country)
                    safe_indicator = re.sub(r"[^\w\-]", "_", indicator)

                    safe_indicator = safe_indicator[:80]

                    filename = os.path.join(self.output_dir, f"output_{category}_{safe_country}_{filename_suffix}_{safe_indicator}.csv")
                    table_lines = [line for line in answer.splitlines() if "|" in line]
                    table_lines = [line for line in table_lines if not re.match(r"^\s*\|?\s*-+\s*\|", line)]
                    if len(table_lines) >= 2:
                        headers = [cell.strip() for cell in table_lines[0].split("|") if cell.strip()]
                        rows = []
                        for row_line in table_lines[1:]:
                            row = [cell.strip() for cell in row_line.split("|") if cell.strip()]
                            if len(row) != len(headers):
                                if len(row) > len(headers):
                                    row = row[:len(headers)]
                                else:
                                    while len(row) < len(headers):
                                        row.append("")
                            rows.append(row)
                        import pandas as pd
                        df = pd.DataFrame(rows, columns=headers)
                        
                        year_col = next((col for col in df.columns if col.lower() in ['year', 'год']), None)
                        if year_col:
                            df[year_col] = df[year_col].apply(lambda y: output_years_map.get(int(y), y) if y.isdigit() else y)

                        for column in df.columns:
                            df[column] = df[column].apply(lambda x: format_number_with_commas(x, column))
                        
                        df.to_csv(filename, index=False)
                        print(f"Successfully created CSV: {filename}")
                    else:
                        print(f"Table not found in RAG answer, CSV not created for indicator: {indicator}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runner = BatchRAGRunner("queries.yaml")
    runner.run() 