import aiohttp
from typing import Dict, List, Tuple, Any

class OSMService:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org/reverse"
    
    async def get_location_info(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Получение информации о локации по координатам.
        
        Args:
            lat: Широта
            lon: Долгота
            
        Returns:
            Словарь с информацией о локации
        """
        # Создаем результирующий словарь
        result = {}
        
        # Асинхронно выполняем все запросы
        async with aiohttp.ClientSession() as session:
            # Получаем данные для радиуса 300 метров
            radius_300_data = await self._get_objects_in_radius(session, lat, lon, 300)
            
            # Получаем данные для радиуса 100 метров
            radius_100_data = await self._get_objects_in_radius(session, lat, lon, 100)
            
            # Получаем данные для радиуса 50 метров (только торговые центры)
            radius_50_data = await self._get_mall_in_radius(session, lat, lon, 50)
            
            # Получаем адрес
            address = await self._get_address(session, lat, lon)
            
        # Парсим полученные данные и заполняем результат
        result["address"] = address
        
        # Парсим данные для радиуса 300 метров
        result.update(self._parse_radius_data(radius_300_data, 300))
        
        # Парсим данные для радиуса 100 метров
        result.update(self._parse_radius_data(radius_100_data, 100))
        
        # Парсим данные для радиуса 50 метров (только торговые центры)
        result.update(self._parse_mall_data(radius_50_data))
        
        return result
    
    async def _get_objects_in_radius(self, session: aiohttp.ClientSession, lat: float, lon: float, radius: int) -> Dict:
        """
        Получение объектов в заданном радиусе от координат.
        
        Args:
            session: HTTP сессия
            lat: Широта
            lon: Долгота
            radius: Радиус в метрах
            
        Returns:
            Данные из Overpass API
        """
        # Формируем запрос к Overpass API
        query = f"""
        [out:json];
        (
          // Жилые дома
          node["building"="residential"](around:{radius},{lat},{lon});
          way["building"="residential"](around:{radius},{lat},{lon});
          relation["building"="residential"](around:{radius},{lat},{lon});
          node["building"="apartments"](around:{radius},{lat},{lon});
          way["building"="apartments"](around:{radius},{lat},{lon});
          relation["building"="apartments"](around:{radius},{lat},{lon});
          
          // Нежилые дома
          node["building"]["building"!="residential"]["building"!="apartments"](around:{radius},{lat},{lon});
          way["building"]["building"!="residential"]["building"!="apartments"](around:{radius},{lat},{lon});
          relation["building"]["building"!="residential"]["building"!="apartments"](around:{radius},{lat},{lon});
          
          // Банкоматы
          node["amenity"="atm"](around:{radius},{lat},{lon});
          
          // Банковские отделения
          node["amenity"="bank"](around:{radius},{lat},{lon});
          way["amenity"="bank"](around:{radius},{lat},{lon});
          
          // Салоны сотовой связи
          node["shop"="mobile_phone"](around:{radius},{lat},{lon});
          way["shop"="mobile_phone"](around:{radius},{lat},{lon});
          
          // Парковки
          node["amenity"="parking"](around:{radius},{lat},{lon});
          way["amenity"="parking"](around:{radius},{lat},{lon});
          
          // Аптеки
          node["amenity"="pharmacy"](around:{radius},{lat},{lon});
          
          // Кафе
          node["amenity"="cafe"](around:{radius},{lat},{lon});
          node["amenity"="restaurant"](around:{radius},{lat},{lon});
          
          // Магазины
          node["shop"](around:{radius},{lat},{lon});
          way["shop"](around:{radius},{lat},{lon});
          
          // Торговые центры
          node["shop"="mall"](around:{radius},{lat},{lon});
          way["shop"="mall"](around:{radius},{lat},{lon});
          node["building"="mall"](around:{radius},{lat},{lon});
          way["building"="mall"](around:{radius},{lat},{lon});
          
          // Офисы
          node["office"](around:{radius},{lat},{lon});
          way["office"](around:{radius},{lat},{lon});
          node["building"="office"](around:{radius},{lat},{lon});
          way["building"="office"](around:{radius},{lat},{lon});
        );
        out body;
        """
        
        async with session.post(self.overpass_url, data={"data": query}) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Ошибка при получении данных из Overpass API: {response.status}")
    
    async def _get_address(self, session: aiohttp.ClientSession, lat: float, lon: float) -> str:
        """
        Получение адреса по координатам.
        
        Args:
            session: HTTP сессия
            lat: Широта
            lon: Долгота
            
        Returns:
            Полный адрес одной строкой
        """
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        
        async with session.get(self.nominatim_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if "display_name" in data:
                    return data["display_name"]
                else:
                    return "Адрес не найден"
            else:
                raise Exception(f"Ошибка при получении адреса: {response.status}")
    
    def _parse_radius_data(self, data: Dict, radius: int) -> Dict[str, int]:
        """
        Парсинг данных для заданного радиуса.
        
        Args:
            data: Данные из Overpass API
            radius: Радиус в метрах
            
        Returns:
            Словарь с количеством объектов каждого типа
        """
        result = {}
        
        if "elements" not in data:
            return {
                f"residential_buildings_{radius}": 0,
                f"non_residential_buildings_{radius}": 0,
                f"atms_{radius}": 0,
                f"banks_{radius}": 0,
                f"mobile_shops_{radius}": 0,
                f"parkings_{radius}": 0,
                f"pharmacies_{radius}": 0,
                f"cafes_{radius}": 0,
                f"shops_{radius}": 0,
                f"malls_{radius}": 0,
                f"offices_{radius}": 0
            }
        
        # Счетчики для различных типов объектов
        residential_buildings = set()
        non_residential_buildings = set()
        atms = set()
        banks = set()
        mobile_shops = set()
        parkings = set()
        pharmacies = set()
        cafes = set()
        shops = set()
        malls = set()
        offices = set()
        
        for element in data["elements"]:
            element_id = element["id"]
            tags = element.get("tags", {})
            
            # Проверяем тип здания
            if "building" in tags:
                building_type = tags["building"]
                if building_type in ["residential", "apartments"]:
                    residential_buildings.add(element_id)
                else:
                    non_residential_buildings.add(element_id)
            
            # Проверяем amenity
            if "amenity" in tags:
                amenity = tags["amenity"]
                if amenity == "atm":
                    atms.add(element_id)
                elif amenity == "bank":
                    banks.add(element_id)
                elif amenity == "parking":
                    parkings.add(element_id)
                elif amenity == "pharmacy":
                    pharmacies.add(element_id)
                elif amenity in ["cafe", "restaurant"]:
                    cafes.add(element_id)
            
            # Проверяем shop
            if "shop" in tags:
                shop_type = tags["shop"]
                if shop_type == "mall":
                    malls.add(element_id)
                elif shop_type == "mobile_phone":
                    mobile_shops.add(element_id)
                else:
                    shops.add(element_id)
            
            # Проверяем office
            if "office" in tags or (tags.get("building") == "office"):
                offices.add(element_id)
        
        # Заполняем результат
        result[f"residential_buildings_{radius}"] = len(residential_buildings)
        result[f"non_residential_buildings_{radius}"] = len(non_residential_buildings)
        result[f"atms_{radius}"] = len(atms)
        result[f"banks_{radius}"] = len(banks)
        result[f"mobile_shops_{radius}"] = len(mobile_shops)
        result[f"parkings_{radius}"] = len(parkings)
        result[f"pharmacies_{radius}"] = len(pharmacies)
        result[f"cafes_{radius}"] = len(cafes)
        result[f"shops_{radius}"] = len(shops)
        result[f"malls_{radius}"] = len(malls)
        result[f"offices_{radius}"] = len(offices)
        
        return result

    async def _get_mall_in_radius(self, session: aiohttp.ClientSession, lat: float, lon: float, radius: int) -> Dict:
        """
        Получение информации о торговых центрах в заданном радиусе.
        
        Args:
            session: HTTP сессия
            lat: Широта
            lon: Долгота
            radius: Радиус в метрах
            
        Returns:
            Данные из Overpass API
        """
        query = f"""
        [out:json];
        (
          // Торговые центры
          node["shop"="mall"](around:{radius},{lat},{lon});
          way["shop"="mall"](around:{radius},{lat},{lon});
          node["building"="mall"](around:{radius},{lat},{lon});
          way["building"="mall"](around:{radius},{lat},{lon});
        );
        out body;
        """
        
        async with session.post(self.overpass_url, data={"data": query}) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Ошибка при получении данных из Overpass API: {response.status}")

    def _parse_mall_data(self, data: Dict) -> Dict[str, int]:
        """
        Парсинг данных о торговых центрах.
        
        Args:
            data: Данные из Overpass API
            
        Returns:
            Словарь с флаговым значением наличия торгового центра
        """
        if "elements" not in data or not data["elements"]:
            return {"mall_50m": 0}
        
        return {"mall_50m": 1}


service = OSMService()

async def get_location_info(lat: float, lon: float) -> Dict[str, Any]:
    """
    Удобная функция для получения информации о локации по координатам.
    
    Args:
        lat: Широта
        lon: Долгота
        
    Returns:
        Словарь с информацией о локации
    """
    try:
        return await service.get_location_info(lat, lon)
    except:
        return None