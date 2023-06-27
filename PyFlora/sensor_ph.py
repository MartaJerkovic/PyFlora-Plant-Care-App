import random

def measure_soil_ph(soil_ph_range):

    range_values = soil_ph_range.split("-")
    min_value = float(range_values[0].strip())
    max_value = float(range_values[1].strip())

    soil_ph = random.uniform(min_value, max_value)
    
    return round(soil_ph, 2)



