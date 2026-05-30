# watchagent-challenge
Build a service that monitors live weather across three cities, decides when something worth noticing has happened, and exposes that information through an API. 

## 1. Events Definition
The first step to solve this challenge was thinking deeply, what does an event (defined as "when something worth noticing has happened" in the challenge) mean?

Comparing weather data withing the same day, or even week, might not be enough to identify events, since for cities with extreme weather like Ottawa, a drop of 10º C from midday to midnight can be considered normal, while this same drop in Vancouver can be considered extreme. This is why our events will be partially based on historical data.

### Historical Data
Due to time constraints, I have decided to limit the historical data to the last 5 years' data for each city proposed in the challenge (Ottawa, Toronto, Vancouver). Historical data will be used to establish monthly baseline distributions for temperature, precipitation, and wind speed. These distributions will be used to identify readings that are statistically unusual for a given city and month.

This data is considered relevant for event detection, given that in months like October, or November, where the transition from summer to winter (autumn) can experience more drastic wheather changes compared to more stable weather months such as June and July. Therefore, a 15º C change from Monday to Friday in October might not be as relevant as the same change in July.

Finally, if historically the coldest temperature for summer has been 23º C, and a reading in summer comes as 22º, this breaks a historical local minimum, which can be considered an event. Such events are notable because they represent conditions that fall outside the historical range observed for that city and season.

Historical data will be used to establish baselines and thresholds, but live event detection will not depend on querying historical APIs during normal operation. Baselines will be precomputed and stored locally to keep event detection deterministic and efficient.

### 24H Data
Even though historical data can contribute to define relevant events, relying only on the latter can lead to an underestimation of events. This is why I will be using the last 24 hours weather data for each city, which will allow the system to identify sudden weather changes within the last 24 hours.

### Events
1. Record Break: Whether a month has experienced a colder/warmer temperature compared to the last 5 years data for that same month.
2. Historical Anomaly: If the readings for a given city, and month fall in the extreme 5% of the readings in the last 5 years.
3. Sudden tempreature change: For each city, a threshold will be calculated using the last 24 hours based on standard deviations. If there is a temperature change that exceeds the threshold, it will be considered a sudden temperature change.
4. Sudden wind change: Similar to sudden temperature change, a wind speed rolling mean will be calculated, and compared to a calculated threshold using the last 24 hours available data. If the wind change goes over the threshold, it will be considered a sudden wind change.
5. Precipitation change: Will represent a change in the precipitation readings.
