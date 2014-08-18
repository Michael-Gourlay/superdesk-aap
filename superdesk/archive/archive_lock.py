from superdesk.base_model import BaseModel
from components.item_lock import ItemLock
from models.io.eve import Eve
from flask import request
from superdesk.archive.common import get_user


class ArchiveLockModel(BaseModel):
    endpoint_name = 'archive_lock'
    url = 'archive/<regex("[a-zA-Z0-9:\\-\\.]+"):item_id>/lock'
    schema = {'lock_user': {'type': 'string'}}
    datasource = {'backend': 'custom'}
    resource_methods = ['GET', 'POST']
    resource_title = endpoint_name

    def on_create(self, docs):
        docs.clear()
        user = get_user(required=True)
        c = ItemLock(Eve())
        c.lock({'_id': request.view_args['item_id']}, user['_id'], None)


class ArchiveUnlockModel(BaseModel):
    endpoint_name = 'archive_unlock'
    url = 'archive/<regex("[a-zA-Z0-9:\\-\\.]+"):item_id>/unlock'
    schema = {'lock_user': {'type': 'string'}}
    datasource = {'backend': 'custom'}
    resource_methods = ['GET', 'POST']
    resource_title = endpoint_name

    def on_create(self, docs):
        docs.clear()
        user = get_user(required=True)
        c = ItemLock(Eve())
        c.unlock({'_id': request.view_args['item_id']}, user['_id'], None)
