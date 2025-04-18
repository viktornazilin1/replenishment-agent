import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

def get_engine():
    url = URL.create(
        "hana",
        username="E8C9162F35F6403E99A4B521A2E5FA9D_A4FSPBMXXEJ4YR17W1506L51Q_RT",
        password="Op1Vo._15g7W397M10xHQaTC.OvQUxggkl_rmeoJXIMgR3uaVtWVdH21Q9I9Rwyw5TkgEvqn2FhS4_04QwM.AB5wKie6ReZnIHHUqrnjgxRTkY6nN2DStw8gwGd_4syk",
        host="c83497f7-be93-4ba7-929e-ff8f92a611b6.hana.trial-us10.hanacloud.ondemand.com",
        port=443,
    )
    return create_engine(url)


def load_data_from_hana():
    engine = get_engine()
    sales = pd.read_sql("SELECT * FROM SALES_ORDERS", engine)
    inventory = pd.read_sql("SELECT * FROM INVENTORY", engine)
    materials = pd.read_sql("SELECT * FROM MATERIALS", engine)
    stores = pd.read_sql("SELECT * FROM STORES", engine)
    holidays = pd.read_sql("SELECT * FROM HOLIDAYS", engine)
    promotions = pd.read_sql("SELECT * FROM PROMOTIONS", engine)
    return sales, inventory, materials, stores, holidays, promotions