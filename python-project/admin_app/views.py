from sqladmin import ModelView

# Importing app.models ensures all model modules are loaded and mapped.
import app.models as models


def _iter_model_classes():
    model_classes = [mapper.class_ for mapper in models.Base.registry.mappers]
    return sorted(model_classes, key=lambda model_cls: model_cls.__name__)


def _build_admin_view(model_cls):
    class AutoModelView(ModelView, model=model_cls):
        pass

    AutoModelView.__name__ = f"{model_cls.__name__}Admin"
    return AutoModelView


def register_admin_views(admin) -> None:
    for model_cls in _iter_model_classes():
        admin.add_view(_build_admin_view(model_cls))
