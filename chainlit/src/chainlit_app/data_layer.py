import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit_app.config import DATABASE_URL


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=DATABASE_URL)
