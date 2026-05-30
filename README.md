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
1. Record Break: A record break event is triggered when a new extreme is observed for a given city and month, compared to the last 5 years of historical data.

This includes:
new monthly maximum temperature
new monthly minimum temperature

These events are notable because they represent conditions that exceed known historical boundaries for that location and time of year.

2. Historical Anomaly: A historical anomaly event is triggered when a reading falls in the extreme tail of the historical distribution for a given city and month. This is defined using percentile-based thresholds (e.g. outside the 5th or 95th percentile).

These events capture conditions that are statistically rare for that location and season, even if they are not absolute records.

3. Sudden tempreature change: This event is triggered when there is an abrupt change in temperature over a short period of time (within the last 24 hours), exceeding a threshold based on recent variability. The threshold is derived from the rolling standard deviation of recent temperature readings.

These events represent sudden changes in thermal conditions, which may indicate instability in local weather patterns.

4. Sudden wind change: This event follows a similar approach to temperature changes, but applied to wind speed. A sudden wind change is triggered when wind speed deviates significantly from recent values, based on a rolling mean and standard deviation over the last 24 hours.

These events represent sudden changes in atmospheric conditions affecting local weather stability.

5. Precipitation change: A precipitation event is triggered when there is a change in precipitation state.

This includes:
precipitation starting (transition from 0 → > 0)
precipitation stopping (transition from > 0 → 0)

These events are important because they represent meaningful transitions in weather conditions that directly affect real-world perception and impact.
