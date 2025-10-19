import os
from collections import defaultdict

def find_parameters_in_chunks():
    crop_parameters = [
        "Wheat", "Winter Wheat", "Spring Wheat", "Rye", "Rice", "Millet and Sorghum",
        "Millet", "Sorghum", "Maize", "Barley", "Oats", "Spelt", "Maslin",
        "Other mixed grains", "Soybean", "All dry beans and peas",
        "Edible dry beans", "Lentils", "Chickpeas", "Edible dry peas",
        "Potatoes", "Manioc", "Arrowroot", "Sweet potates", "Yams",
        "Sugar Cane", "Sugar Beets", "Cotton", "Flax", "Hemp", "Groundnuts",
        "Linseed", "Hempseed", "Castor beans", "Rapeseed", "Colza", "Sesame",
        "Sunflower", "Tobacco", "Coffee", "Tea", "Cacao", "Coconut",
        "Oil Plams", "Rubber", "Beans", "Dry beans", "Sweet potatoes", "Other cereals harversted for grain"
    ]

    machinery_parameters = [
        "Tractors", "Plows", "Iron plows", "Disk plows", "wood plows", "ridging plows",
        "tine harrows", "Rotary tillers", "Disk harrows", "cultivators", "hoes", "seed drills",
        "sprayers", "dusters", "mowers", "rakes", "reapers", "binders", "combines(harvest-threshers)",
        "corn pickers", "potato-harvesting machinery", "sugar-beet harvesting machinery", "threshers",
        "hay balers", "sugarcane crushers", "carts", "jeeps", "Station wagons", "trucks", "Automobiles",
        "Ploughs", "Harrows", "Rollers", "Fertilizer Distributors", "Mechanical hoes", "Grain harvesters",
        "Tedders", "Potato lifters", "Cleaners and sorters", "Hay and forage presses", "Maize shredders",
        "Chaffcutters", "Rootcutters", "Grinders", "Crushers", "Shedders"
    ]

    # Add general parameters that could be in any category but shouldn't be categorized as crops or machinery
    general_parameters = ["Number of holdings reporting", "Hectares", "Metric tons"]

    all_parameters = {
        "Crops": {p.strip().lower() for p in crop_parameters if p.strip()},
        "Machinery": {p.strip().lower() for p in machinery_parameters if p.strip()},
        "General": {p.strip().lower() for p in general_parameters if p.strip()}
    }

    chunks_dir = 'output_chunks'
    country_parameters = defaultdict(lambda: defaultdict(set))

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
                
                for category, params in all_parameters.items():
                    for param in params:
                        if param in content:
                            country_parameters[country][category].add(param)

    except Exception as e:
        return

    if country_parameters:
        print("\n--- Found Matching Parameters by Country ---")
        for country in sorted(country_parameters.keys()):
            print(f"\n{country.replace('-', ' ').title()}:")
            country_data = country_parameters[country]
            
            for category in ["Crops", "Machinery", "General"]:
                if country_data[category]:
                    print(f"  {category}:")
                    for param in sorted(list(country_data[category])):
                        print(f"    - {param.title()}")
    else:
        print("\nNo matching parameters were found in any of the chunk files.")

if __name__ == '__main__':
    find_parameters_in_chunks()
