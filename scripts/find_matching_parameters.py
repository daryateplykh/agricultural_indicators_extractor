import os
from collections import defaultdict

def find_parameters_in_chunks():
    parameters_to_find = [
        "Wheat", "Number of holdings reporting", "Hectares", "Metric tons",
        "Winter Wheat", "Spring Wheat", "Rye", "Rice", "Millet and Sorghum",
        "Millet", "Sorghum", "Maize", "Barley", "Oats", "Spelt", "Maslin",
        "Other mixed grains", "Soybean", "All dry beans and peas",
        "Edible dry beans", "Lentils", "Chickpeas", "Edible dry peas",
        "Potatoes", "Manioc", "Arrowroot", "Sweet potates", "Yams",
        "Sugar Cane", "Sugar Beets", "Cotton", "Flax", "Hemp", "Groundnuts",
        "Linseed", "Hempseed", "Castor beans", "Rapeseed", "Colza", "Sesame",
        "Sunflower", "Tobacco", "Coffee", "Tea", "Cacao", "Coconut",
        "Oil Plams", "Rubber", "Beans", "Dry beans", "Sweet potatoes", "Other cereals harversted for grain", 
    ]
    
    normalized_params = {p.strip().lower() for p in parameters_to_find if p.strip()}

    chunks_dir = 'output_chunks'
    country_parameters = defaultdict(set)

    try:
        if not os.path.exists(chunks_dir) or not os.listdir(chunks_dir):
            return

        files = [f for f in os.listdir(chunks_dir) if f.endswith('.txt')]
        
        for filename in files:
            try:
                country = filename.split('_')[0]
            except IndexError:
                continue

            filepath = os.path.join(chunks_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
                for param in normalized_params:
                    if param in content:
                        country_parameters[country].add(param)

    except Exception as e:
        return

    if country_parameters:
        print("\n--- Found Matching Parameters by Country ---")
        for country in sorted(country_parameters.keys()):
            print(f"\n{country.replace('-', ' ').title()}:")
            for param in sorted(list(country_parameters[country])):
                print(f"  - {param.title()}")
    else:
        print("\nNo matching parameters were found in any of the chunk files.")

if __name__ == '__main__':
    find_parameters_in_chunks()
