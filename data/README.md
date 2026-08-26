# Air Pollution Dataset Documentation

## Source File: `ap_air_pollution_2021_2023.csv`

This dataset contains real air quality monitoring observations from the **Central Pollution Control Board (CPCB) National Air Quality Monitoring Programme (NAMP)** across major urban centers in **Andhra Pradesh, India** for the reporting years **2021** and **2023**.

### Fields & Data Dictionary

| Field Name | Type | Description | Example Values |
| :--- | :--- | :--- | :--- |
| `country` | String | Country of observation | `India` |
| `state` | String | State administrative division | `Andhra Pradesh` |
| `city` | String | Urban center / municipal corporation | `Amaravati`, `Visakhapatnam`, `Vijayawada`, `Tirupati`, `Guntur` |
| `station_id` | String | Unique monitoring station identifier | `AP_AMARAVATI_INTEGRATED`, `AP_VISAKHAPATNAM_INTEGRATED` |
| `station_type` | String | Monitoring station classification | `Integrated city-level NAMP record` |
| `pollutant` | String | Atmospheric pollutant code | `PM10`, `PM2.5`, `NO2`, `SO2` |
| `observation_date` | ISO-8601 | Timestamp of record | `2021-12-31T23:59:59`, `2023-12-31T23:59:59` |
| `year` | Integer | Observation calendar year | `2021`, `2023` |
| `value` | Float | Measured concentration value | `55`, `28`, `14`, `103`, `129` |
| `unit` | String | Unit of measurement | `µg/m³` (micrograms per cubic meter) |
| `measurement_type` | String | Aggregation method | `Annual Average` |
| `frequency` | String | Sampling frequency | `Annual` |
| `source` | String | Official data publisher | `CPCB NAMP Ambient Air Quality Status` |

### Knowledge Graph Entity Mapping

- **State Node**: `(:State {name: row.state})`
- **City Node**: `(:City {name: row.city})`
- **MonitoringStation Node**: `(:MonitoringStation {station_id: row.station_id, station_type: row.station_type})`
- **Reading Node**: `(:Reading {value: toFloat(row.value), unit: row.unit, measurement_type: row.measurement_type, frequency: row.frequency, year: toInteger(row.year)})`
- **Pollutant Node**: `(:Pollutant {name: row.pollutant})`
- **DateTime Node**: `(:DateTime {value: row.observation_date})`

### Relationship Graph

```
(State)-[:HAS_CITY]->(City)
(City)-[:HAS_STATION]->(MonitoringStation)
(MonitoringStation)-[:HAS_READING]->(Reading)
(Reading)-[:MEASURES]->(Pollutant)
(Reading)-[:RECORDED_AT]->(DateTime)
```
