# PyFlora Plant Care App

## General Info
As part of my final thesis for a Python Developer education course, I have developed PyFlora, an app dedicated to plant care.  

## App Overview
PyFlora's primary objective is to effectively manage plant health through the monitoring of essential parameters such as light exposure, soil moisture, soil pH, and current temperature. The app comes with a built-in collection of 10 plants. Similar to real-life scenarios, users are advised to place their chosen plant in a pot. Once the plant is in the pot, users can access sensor readings specific to the plant and perform watering as necessary. Each monitored parameter is supported by an associated script that effectively emulates its behavior, enhancing the overall realism of the user experience.

## App Video Preview
Watch a brief visual demonstration of PyFlora's key features and functionality:
https://drive.google.com/file/d/1tXN5rbwL8N9swd5Am1zC1FYZoj5WSN1T/view?usp=sharing

## Technologies 
For the app development, following technologies were used:

    python             3.11.0
    beautifulsoup4     4.11.1
    pyparsing          3.0.9
    PyQt5              5.15.9
    pyqt5-plugins      5.15.9.2.3
    PyQt5-Qt5          5.15.2
    PyQt5-sip          12.11.1
    pyqt5-tools        5.15.9.3.3
    pyqtgraph          0.13.3
    qt5-applications   5.15.2.2.3
    qt5-tools          5.15.2.1.3
    requests           2.28.2
    soupsieve          2.3.2.post1
    SQLAlchemy         2.0.0

## Installation
Download PyFlora folder and open it using your preferred IDE.  
Open _**1_pyflora_main.py**_ file and run it.  
** for sensor readings to work open _**openweather_temp.py**_ file and replace **"YOUR_API_KEY"** with your OpenWeather API key and **"YOUR_CITY"** with the city for which you want to retrieve weather data.

## Features 
* Profile management (edit name, username and password)
* Plant Management (search, add, remove and update plants in your collection)
* Pot Management (search, add, remove and update pots in your collection)
* Sensor Readings (collect sensor readings for plants in pots, including light exposure, soil moisutre, soil ph and temperature)
* Data Visualisation (sensor readings for every pot are presented in the visual format)
* Water plants (water plants in pots, ensuring proper hydration)

## Contributions
All contributions are warmly welcomed! If you have any questions, suggestions, or feedback regarding the PyFlora app, please feel free to reach out. I value collaboration and look forward to engaging in 
discussions about the code and any potential improvements.


#### Thank you for taking the time to explore my PyFlora app! Happy plant care!
