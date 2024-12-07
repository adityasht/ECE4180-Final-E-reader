from datetime import datetime, timedelta
import time
import requests

API_KEY = '67165e9a733df491e5ed1242fa0362fb'


class WeatherData():
    def __init__(self, location):
        self.location = location
        self.weather_api_key = API_KEY
        self.weather_cache = None
        self.weather_cache = None
        self.last_weather_update = None
        self.WEATHER_UPDATE_INTERVAL = 3600 


    def get_weather(self):
        current_time = time.time()
        
        if (self.weather_cache is not None and 
            self.last_weather_update is not None and 
            current_time - self.last_weather_update < self.WEATHER_UPDATE_INTERVAL):
            return self.weather_cache

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.location['lat']}&lon={self.location['lon']}&appid={self.weather_api_key}&units=imperial"
            response = requests.get(url)
            data = response.json()
            
            weather_data = []
            if 'list' in data:
                current_date = datetime.now().date()
                daily_temps = {}
                
                # First, collect all temperatures for each day
                for item in data['list']:
                    forecast_date = datetime.fromtimestamp(item['dt']).date()
                    if forecast_date > current_date:
                        if forecast_date not in daily_temps:
                            daily_temps[forecast_date] = {
                                'temps': [],
                                'description': item['weather'][0]['main'],
                                'precipitation': []  # Added precipitation array
                            }
                        daily_temps[forecast_date]['temps'].append({
                            'temp': item['main']['temp'],
                            'temp_min': item['main']['temp_min'],
                            'temp_max': item['main']['temp_max']
                        })
                        # Get precipitation probability (convert from 0-1 to percentage)
                        pop = item.get('pop', 0) * 100
                        daily_temps[forecast_date]['precipitation'].append(pop)

                # Process each day's data
                for date in sorted(daily_temps.keys())[:5]:  # Get first 5 days
                    day_temps = daily_temps[date]['temps']
                    
                    # Calculate statistics
                    min_temp = min(t['temp_min'] for t in day_temps)
                    max_temp = max(t['temp_max'] for t in day_temps)
                    avg_temp = sum(t['temp'] for t in day_temps) / len(day_temps)
                    avg_precip = sum(daily_temps[date]['precipitation']) / len(daily_temps[date]['precipitation'])
                    
                    weather_data.append({
                        'date': date,
                        'temp': round(avg_temp),
                        'temp_min': round(min_temp),
                        'temp_max': round(max_temp),
                        'description': daily_temps[date]['description'],
                        'precipitation': round(avg_precip),  # Added precipitation percentage
                        'sunrise': data['city']['sunrise'],
                        'sunset': data['city']['sunset']
                    })
                
                self.weather_cache = weather_data
                self.last_weather_update = current_time
                
                return weather_data
                
        except Exception as e:
            print(f"Weather API error: {str(e)}")
            if self.weather_cache is not None:
                return self.weather_cache
            
            # Fallback data with precipitation
            return [
                {'date': datetime.now().date(), 'temp': 68, 'temp_min': 60, 'temp_max': 75, 'description': 'Clear', 'precipitation': 10, 'sunrise': int(time.time()), 'sunset': int(time.time()) + 43200},
                {'date': datetime.now().date() + timedelta(days=1), 'temp': 65, 'temp_min': 58, 'temp_max': 72, 'description': 'Clouds', 'precipitation': 30},
                {'date': datetime.now().date() + timedelta(days=2), 'temp': 70, 'temp_min': 62, 'temp_max': 78, 'description': 'Clear', 'precipitation': 0},
                {'date': datetime.now().date() + timedelta(days=3), 'temp': 72, 'temp_min': 63, 'temp_max': 81, 'description': 'Rain', 'precipitation': 80},
                {'date': datetime.now().date() + timedelta(days=4), 'temp': 69, 'temp_min': 61, 'temp_max': 77, 'description': 'Clouds', 'precipitation': 20}
            ]
    
    def weather_cache(self):
        return self.weather_cache
    
if __name__ == "__main__":
    api = WeatherData({'lat': 40.7128, 'lon': -74.0060, 'city': 'New York'})
    data = api.get_weather()
    print(data)
