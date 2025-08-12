import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_core.rag_answer import query_rag

def normalize_number(text: str) -> str:
    return ''.join(c for c in text if c.isdigit())

def query_and_validate(question: str, expected_response: str) -> tuple[bool, str]:
    expected_normalized = normalize_number(expected_response)
    
    response_content = query_rag(question, save_csv=False)
    
    actual_normalized = normalize_number(response_content)

    if expected_normalized in actual_normalized:
        return True, response_content
    else:
        return False, response_content

def run_all_tests():
    tests = [
 ("What was the total number of holdings in Peru in 1960?", "869 945"),
("What was the total area of owned holdings by land utilization in Peru in 1960?", "1 440 068"),
("How many holdings reported wheat in Peru in 1960?", "203 045"),
("How many hectares of cotton were reported in Peru in 1960?", "243 276"),
("How many hectares of pineapples were reported in Peru in 1960?", "1 452"),
("What was the total number of horses reported in Peru in 1960?", "1 907 009"),
("How many holdings reported cattle in Peru in 1960?", "481 138"),
("How many tractors owned solely by the holder were reported in Peru in 1960?", "3 422"),
("What was the total number of holdings in the Philippines in 1960?", "2 166 216"),
("How many hectares of arable land (owned holdings) were reported in the Philippines in 1960?", "2 410 743"),
("How many hectares of arable land rented from others for a fixed amount of produce were reported in the Philippines in 1960?", "68 113"),
("What was the total production of rice in metric tons in the Philippines in 1960?", "3 255 589"),
("How many hectares of maize were reported in the Philippines in 1960?", "1 902 038"),
("What was the total number of pigs reported in the Philippines in 1960?", "13 455 743"),
("What was the total number of ducks in the Philippines in 1960?", "1 752 165"),
("How many holdings were provided with irrigation facilities in the Philippines in 1960?", "374 405"),
("How many holdings reported using chemical fertilizers in the Philippines in 1960?", "227 778"),
#1950
("What was the total number of holdings in American Samoa in 1950?", "1 490"),
("What was the total number of breadfruit reported in American Samoa in 1950?", "637 408"),
("What was the total number of pigs in American Samoa in 1950?", "9 080"),
("How many holdings reported pigs in American Samoa in 1950?", "1 201"),
("How many holdings reported wheat in Australia in 1950?", "51 961"),
("What was the total area of wheat in hectares in Australia in 1950?", "4 953 407"),
("What was the total production of wheat in metric tons in Australia in 1950?", "5 939 106"),
("How many hectares of peas were reported in Australia in 1950?", "19 403"),
("How many hectares of sugar cane (total) were reported in Australia in 1950?", "161 153"),
("How many hectares of tobacco were reported in Australia in 1950?", "1 855"),
("What was the total production of apples in metric tons in Australia in 1950?", "175 747"),
("How many hectares of pears were reported in Australia in 1950?", "8 733"),
("What was the total production of pineapples in metric tons in Australia in 1950?", "45 984"),
("How many holdings reported pigs in Australia in 1950?", "52 978"),
("What was the total number of cattle in Australia in 1950?", "13 371 981"),
("What was the total number of holdings in Austria in 1950?", "432 848"),
("How many holdings reported wheat in Austria in 1950?", "247 618"),
("How many holdings reported horses in Austria in 1950?", "136 807"),
("What was the total area of potatoes in hectares in Austria in 1950?", "382 670"),
#1930
("What was the total number of occupied farms in Canada in 1931?", "728 623"),
("What was the total farm area of farms between 51 and 100 acres in Canada in 1931?", "12 866 488 acres"),
("What was the total improved area of field crops in Canada in 1931?", "57 925 483 acres"),
("How many farms reported winter wheat in Canada in 1931?", "54 080"),
("How many farms reported potatoes in Canada in 1931?", "505 057"),
("What was the total value of oats produced in Canada in 1930?", "75 602 772 dollars"),
("What was the quantity of oats harvested in Canada in 1930?", "10 164 042 thousand lb."),
("What was the absolute number of farms reporting alfalfa in Canada in 1931?", "52,601"),
("What was the absolute area of crop failure for wheat in Canada in 1930?", "3,816,741 acres"),
("What was the absolute number of farms reporting orchards in Canada in 1931?", "222,712"),
        
    ]

    passed, failed = 0, 0
    failed_tests = []

    for i, (question, expected) in enumerate(tests, 1):
        print(f"--- Test {i}/{len(tests)} ---")
        print(f"Question: {question}")
        result, actual_response = query_and_validate(question, expected)
        if result:
            passed += 1
            print("Result: Passed")
        else:
            failed += 1
            failed_tests.append((question, expected, actual_response))
            print("Result: Failed")
        print("-" * (len(f"--- Test {i}/{len(tests)} ---")))


    print("\n--- Test Summary ---")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed_tests:
        print("\n--- Failed Tests ---")
        for q, expected, actual in failed_tests:
            print(f"- Question: {q}")
            print(f"  Expected: {expected}")
            print(f"  Actual: {actual}")
            print()

if __name__ == "__main__":
    run_all_tests()
