from collections import UserList
from collections.abc import Iterable
from datetime import datetime
from functools import reduce
from mage_ai.api.operations.constants import READ
from mage_ai.api.resources.BaseResource import BaseResource
from mage_ai.orchestration.db.models.base import BaseModel
from mage_ai.shared.hash import merge_dict
import importlib
import inspect


class BasePresenter():
    all_attributes_attr = {}
    all_formats_attr = {}
    default_attributes = []

    def __init__(self, resource, current_user, **kwargs):
        self.current_user = current_user
        self.options = kwargs
        self.resource = resource

    @classmethod
    def all_attributes(cls):
        if not cls.all_attributes_attr.get(cls.__name__):
            cls.all_attributes_attr[cls.__name__] = {}
        return cls.all_attributes_attr[cls.__name__]

    @classmethod
    def all_formats(cls):
        if not cls.all_formats_attr.get(cls.__name__):
            cls.all_formats_attr[cls.__name__] = {'default': cls.default_attributes}
        return cls.all_formats_attr[cls.__name__]

    @classmethod
    def formats(cls, format_arg):
        if format_arg and cls.all_formats().get(format_arg, None) is not None:
            return cls.all_formats()[format_arg]
        else:
            return cls.all_formats()['default']

    @classmethod
    def register_attributes(cls, keys, klass_symbol_or_lambda):
        for key in keys:
            cls.all_attributes()[key] = klass_symbol_or_lambda

    @classmethod
    def register_format(cls, format_arg, keys):
        cls.all_formats()[format_arg] = keys

    @classmethod
    def register_formats(cls, formats, keys):
        arr = formats if isinstance(formats, list) else [formats]
        for format_arg in arr:
            cls.register_format(format_arg, keys)

    @classmethod
    async def present_resource(self, resource, user, **kwargs):
        async def present_lambda(r):
            if r and inspect.isawaitable(r):
                r = await r

            results = r.__class__.presenter_class()(
                r,
                user,
                **kwargs,
            ).present(
                **kwargs,
            )

            if results and inspect.isawaitable(results):
                results = await results

            return results

        if isinstance(resource, Iterable):
            return [await present_lambda(r) for r in resource]
        else:
            return await present_lambda(resource)

    @classmethod
    def present_model(cls, model, resource_class, user, **kwargs):
        if model:
            return cls.present_resource(
                resource_class(model, user, **kwargs), user, **kwargs
            )

    @classmethod
    def present_models(cls, models, resource_class, user, **kwargs):
        return cls.present_resource(
            resource_class.build_result_set(models, user, **kwargs), user, **kwargs
        )

    async def present(self, **kwargs):
        def _build(obj, key):
            value = getattr(self, key)
            if callable(value):
                value = value(**kwargs)
            self.__validate_attribute_type(key, value)
            if issubclass(
                    value.__class__,
                    list) or issubclass(
                    value.__class__,
                    UserList):
                obj[key] = [
                    self.__transform_value(
                        key, v, **kwargs) for v in value]
            else:
                obj[key] = self.__transform_value(key, value, **kwargs)
            return obj

        format_to_present = kwargs.get('format', None)
        if format_to_present and self.options.get('from_resource'):
            from_resource_name = self.options['from_resource'].resource_name_singular(
            )
            format_to_present = f'{from_resource_name}/{format_to_present}'

        return reduce(_build, self.__class__.formats(format_to_present), {})

    def __transform_value(self, key, value, **kwargs):
        klass_symbol_or_lambda = self.__class__.all_attributes().get(key, None)

        if issubclass(value.__class__, BaseModel):
            resource_class_name = f'{value.__class__.__name__}Resource'
            resource_class = getattr(importlib.import_module(
                f'mage_ai.api.resources.{resource_class_name}'), resource_class_name, )
            value = resource_class(value, self.current_user, **kwargs)

        if isinstance(value, datetime):
            return str(value)
        elif klass_symbol_or_lambda is float:
            return float(value)
        elif klass_symbol_or_lambda is int:
            return int(value)
        elif issubclass(value.__class__, BaseResource):
            opts = self.options.copy()
            opts['from_resource'] = self.resource
            data = value.presenter_class().present_resource(
                value,
                self.current_user,
                **merge_dict(kwargs, opts),
            )

            if not kwargs.get('ignore_permissions'):
                policy = value.policy_class()(value, self.current_user, **opts)
                policy.authorize_attributes(
                    READ,
                    data.keys(),
                    **opts,
                )

            return data
        else:
            return value

    def __validate_attribute_class(self, klass_symbol, value):
        pass

    def __validate_attribute_type(self, key, value):
        pass

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            val = getattr(self.resource, name)
            return val(*args, **kwargs) if callable(val) else val

        return _missing()
