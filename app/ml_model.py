from osm_service import get_location_info
from catboost import CatBoostRegressor
import joblib
import pandas as pd
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import StandardScaler
# from sklearn.decomposition import PCA
# from sklearn.cluster import KMeans
import pickle
cat_model = CatBoostRegressor()
cat_model.load_model('/app/models/catboost_model1.cbm')

xg_model = joblib.load('/app/models/xgboost_model.pkl')

lr_model = joblib.load('/app/models/linreg_model.pkl')


with open('/app/models/clustering_pipeline.pkl', 'rb') as f:
    pipeline_loaded = pickle.load(f)


async def predict_value(latitude: float, longitude: float, address: str, model_name: str, atm_group: float) -> float:
    """
    Заглушка функции для ML модели.
    В реальном приложении здесь будет код для предсказания значения
    на основе координат и адреса.
    
    Args:
        latitude: Широта точки
        longitude: Долгота точки
        address: Адрес выбранной точки
    
    Returns:
        float: Предсказанное значение
    """
    # Здесь будет логика ML модели
    result = await get_location_info(lat=latitude, lon=longitude)
    print(result)
    result = pd.DataFrame([result])
    print(result.columns)
    result['atm_count'] = 1
    print(result.columns)
    result['population'] = 0
    result =  result.drop(columns=['address'])
    result['lat'] = latitude
    result['lon'] = longitude
    result['atm_group'] = atm_group
    print(result.columns)
    desired_columns = ['atm_group', 'lat', 'lon'] + \
                    [col for col in result.columns if col not in ['atm_group', 'lat', 'lon', 'population', 'atm_count']] + \
                    ['population', 'atm_count']

    result = result[desired_columns]
    print(result)
    result['cluster'] = pipeline_loaded.predict(result)
    print(result)

    if model_name == 'catboost':
        prediction = cat_model.predict(result)
    elif model_name == 'xgboost':
        prediction = xg_model.predict(result)
    elif model_name == 'linereg':
        prediction = lr_model.predict(result)
    elif model_name == 'ansamble':
        pred_cat = cat_model.predict(result)
        pred_xgb = xg_model.predict(result)
        prediction = (pred_cat + pred_xgb) / 2

    return round(prediction[0], 4) 