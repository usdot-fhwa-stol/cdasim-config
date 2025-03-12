#!/bin/bash
#This script will generate random traffic to be used in Sumo-carla co simulation for a any Sumo Network File given the simulation duration, number of vehicles and a random number seed
# This script requires  installation of Sumo tools randomTrips.py and Python

#Usage:
# 1. Run with arguments:
#    ./generate_background_traffic.sh  <duration> <num_vehicles> <random_seed>
#    Example: ./generate_traffic.sh  600 50 42
# 2. Or run interactively by omitting arguments:
#    ./generate_traffic.sh

# Checking for missing arguments 
if [ "$#" -lt 3 ]; then
    echo "Missing arguments. You need to provide:"
    echo "1. Duration of the Simulation"
    echo "2. Number of Vehicles"
    echo "3. Random Number Seed"

    # Prompting for missing inputs

    echo "Enter Duration of the Simulation:"
    read sim_duration

    echo "Enter the Number of Vehicles:"
    read veh_number

    echo "Enter Random Number Seed (Different Seed will generate different traffic):"
    read seed
else
    # Assigning inputs from command-line arguments
    sim_duration=$1
    veh_number=$2
    seed=$3
fi


# Calculate the rate of vehicle generation
rate=$(echo "$sim_duration / $veh_number" | bc -l)


# Run the Python script with the provided inputs
python3 /usr/share/sumo/tools/randomTrips.py -n Town05.net.xml -r Town05.rou.xml  -e $sim_duration -p $rate --vehicle-class passenger --validate --random --seed $seed --min-distance 300 --random-depart --fringe-factor 10 --allow-fringe --remove-loops --weights-prefix "weights"

#Changing vehicle Types matching pasenger car of CARLA 
# List of Passenger vehicle classes in CARLA 

vehicle_classes=(
  "vehicle.audi.a2"
  "vehicle.audi.tt"
  "vehicle.jeep.wrangler_rubicon"
  "vehicle.chevrolet.impala"
  "vehicle.mini.cooperst"
  "vehicle.mercedes-benz.coupe"
  "vehicle.bmw.grandtourer"
  "vehicle.citroen.c3"
  "vehicle.mustang.mustang"
  "vehicle.lincoln.mkz2017"
  "vehicle.seat.leon"
  "vehicle.nissan.patrol"
  "vehicle.nissan.micra"
)

temp_file="temp.xml"
out_file="Town05.rou.xml"
# Read the generated route file line by line
while IFS= read -r line; do
  if [[ "$line" == *'type="passenger"'* ]]; then
    # Select a random vehicle class
    random_vehicle=${vehicle_classes[$RANDOM % ${#vehicle_classes[@]}]}
    # Replace type="passenger" with the random vehicle class
    line=$(echo "$line" | sed "s/type=\"passenger\"/type=\"$random_vehicle\"/")
  fi
  # Write the updated line to a temporary file
  echo "$line" >> "$temp_file"
done < "$out_file"

# Replace the original file with the updated file
mv "$temp_file" "$out_file"
rm trips.trips.xml
echo "Route file Town05.rou.xml successfully generated"


