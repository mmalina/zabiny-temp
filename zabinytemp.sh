#!/bin/bash

# Parse arguments
OUTPUT_FILE=""
while getopts "o:" opt; do
    case $opt in
        o)
            OUTPUT_FILE="$OPTARG"
            ;;
        \?)
            echo "Usage: $0 [-o output_json_file]"
            exit 1
            ;;
    esac
done

# Fetch station data
response=$(curl -s --location --request POST 'https://data-provider.chmi.cz/api/navigation/data/stanice' \
    --header 'Content-Type: application/json' \
    --data-raw '{"paging":{"start":0,"size":12},"search":{"groupItemIds":["meteo"],"regionId":999,"text":"žabovřesky"}}')

# Parse station ID from URL
station_id=$(echo "$response" | jq -r '.data[0].url' | awk -F'/' '{print $NF}' | awk -F'-' '{print $1}')

if [ -z "$station_id" ]; then
    echo "Error: Could not find station ID"
    exit 1
fi

# Convert to uppercase for API
station_id_upper=$(echo "$station_id" | tr '[:lower:]' '[:upper:]')

# Fetch temperature data
temp_data=$(curl -s "https://data-provider.chmi.cz/api/graphs/graf.meteo-stanice.teplota-10m/${station_id_upper}")

# Extract last data point
last_temp=$(echo "$temp_data" | jq -r '.dataPoints[-1].values.T')
last_timestamp=$(echo "$temp_data" | jq -r '.dataPoints[-1].timestamp')

# Convert ISO timestamp to Unix epoch seconds (handles both GNU and BSD date)
timestamp_sec=$(date -d "$last_timestamp" '+%s' 2>/dev/null || \
                date -j -f '%Y-%m-%dT%H:%M:%SZ' "$last_timestamp" '+%s' 2>/dev/null)

# Generate ISO time in Europe/Prague timezone
isotime=$(TZ="Europe/Prague" date -d "$last_timestamp" '+%Y-%m-%dT%H:%M:%S%:z' 2>/dev/null || \
          TZ="Europe/Prague" date -r "$timestamp_sec" '+%Y-%m-%dT%H:%M:%S%z' 2>/dev/null | sed 's/\(..\)$/:\1/')

echo "Temperature: ${last_temp}°C"
echo "Timestamp: $last_timestamp"

# Output to JSON file if specified
if [ -n "$OUTPUT_FILE" ]; then
    jq -n \
        --arg isotime "$isotime" \
        --argjson timestamp "$timestamp_sec" \
        --argjson temp "$last_temp" \
        '{"isotime": $isotime, "timestamp": $timestamp, "temp": $temp}' > "$OUTPUT_FILE"
    echo "JSON written to: $OUTPUT_FILE"
fi
