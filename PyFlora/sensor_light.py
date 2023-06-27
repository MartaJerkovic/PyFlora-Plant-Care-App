import random
import datetime as dt

def measure_light_intensity(option):
    current_time = dt.datetime.now().time()
    intensity = calculate_intensity(option, current_time)
    return round(intensity, 2)

def calculate_intensity(option, time):

    if option == "Shade":
        if time >= dt.time(6) and time < dt.time(9):
            return random.uniform(100, 400)  
        elif time >= dt.time(9) and time < dt.time(17):
            return random.uniform(400, 1000)  
        elif time >= dt.time(17) and time < dt.time(19):
            return random.uniform(100, 400)  
        else:
            return random.uniform(10, 100)  
        
    elif option == "Indirect sunlight":
        if time >= dt.time(6) and time < dt.time(9):
            return random.uniform(400, 1000)  
        elif time >= dt.time(9) and time < dt.time(17):
            return random.uniform(1000, 2000)  
        elif time >= dt.time(17) and time < dt.time(19):
            return random.uniform(400, 1000)  
        else:
            return random.uniform(10, 100)  
        
    elif option == "Strong light":
        if time >= dt.time(6) and time < dt.time(9):
            return random.uniform(400, 2000)  
        elif time >= dt.time(9) and time < dt.time(17):
            return random.uniform(2000, 5000)  
        elif time >= dt.time(17) and time < dt.time(19):
            return random.uniform(400, 2000)  
        else:
            return random.uniform(10, 100) 
        
    elif option == "Full sun":
        if time >= dt.time(6) and time < dt.time(9):
            return random.uniform(400, 5000)  
        elif time >= dt.time(9) and time < dt.time(17):
            return random.uniform(5000, 10000)  
        elif time >= dt.time(17) and time < dt.time(19):
            return random.uniform(400, 5000)  
        else:
            return random.uniform(10, 100) 
        
    else:
        return 0.0

# option = input("Enter option:")
# intensity = measure_light_intensity(option)
# current_time = dt.datetime.now().time().strftime("%H:%M:%S")
# print(f"Time: {current_time}, Light Intensity: {intensity:.2f} LUX")
