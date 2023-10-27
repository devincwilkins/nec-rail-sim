# WorcesterSim (aka Woosta)
__Author:__ Devin Wilkins

## Folder Structure:
    .
    |- analysis/
    |    |- utils/
    |    |    |- processPTIS.py
    |    |    |- .py
    |    |- data/
    |    |    |- PTIS Triggerbox Data/
    |    |    |- Ridership Data/
    |    |    |- TRMS Reports/
    |    |    |- WML PTIS Arrival Times/
    |    |    |- static/
    |    |    |    |- Station_Coords.csv
    |    |- Analysis.ipynb
    |    |- Dwell Model.ipynb
    |    |- Ridership Analysis.ipynb
    |    |- Plots.ipynb
    |- scenarios/
    |- schedules/
    |- scheduling/
    |- simulation/
    |- outputs/



# Documentation

### __Data sources:__
1. GTFS
2. PTIS AVL when arrives at station

    Overrepresents dwell time because of the location of Trigger boxes outside the station (before, and after).
    To correct Dwell time I used CleanTrigger methods, based on 
3. PTIS_Triggerbox_Location.xlsx

    Triggers

4. WML every 30 seconds pings 
5. Ridership data (used into Dwell Model)
6. TRMS089 reports how many train cars and conductors

### __Files__

* processPTIS.py:

    All functions to process PTIS data, that then will be used int trips-plots and Dwell Model, and -maybe- GPS_pings.

* trips-plots (original is backed up in *copy)
* DWELL_MODEL (original is backed up in *copy)
    When processing AVL data, I realized I need the function clwanTriggers
    

* ServicePatterns.ipynb
* ServicePatterns.py

* ParseAVL.ipynb
* ParseAVL.py
* ParseGTFS
* GPS_Pings



