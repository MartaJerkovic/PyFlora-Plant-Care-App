
def initial_soil_moisture(moisture_option):

    if moisture_option == "Wet":
        initial_moisture = 10

    elif moisture_option == "Normal":
        initial_moisture = 7

    elif moisture_option == "Dry":
        initial_moisture = 3

    else:
        initial_moisture = 10

    return initial_moisture

def measure_soil_moisture(moisture_option, current_temperature, current_light_intensity, time_delta):

    temperature_coefficient = current_temperature/100
    light_coefficient = current_light_intensity/10000

    temperature_weight = 0.6 
    light_intensity_weight = 0.4  
    moisture_decrease_rate = 0.01 #per hour

    moisture_decrease = temperature_coefficient * temperature_weight + light_coefficient * light_intensity_weight + moisture_decrease_rate * time_delta

    initial_moisture = initial_soil_moisture(moisture_option)

    moisture = initial_moisture - moisture_decrease

    moisture = max(1, min(10, moisture))

    if moisture > 10:
        moisture = 10
    
    elif moisture < 1:
        moisture = 1

    return round(moisture, 2)




    


