import importlib
import pkgutil

from flask import Blueprint


def register_blueprints(app):
    package_name = __name__
    package_path = __path__

    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        if is_pkg:
            # Exemplo: admin, database, default
            subpackage = f"{package_name}.{module_name}"
            submodule = importlib.import_module(subpackage)
            if hasattr(submodule, 'register_blueprints'):
                submodule.register_blueprints(app)
        else:
            # Raiz direta — geralmente não há, mas suportado
            full_module_name = f"{package_name}.{module_name}"
            module = importlib.import_module(full_module_name)
            if hasattr(module, 'bp') and isinstance(module.bp, Blueprint):
                if module.bp.name not in app.blueprints:
                    app.register_blueprint(module.bp)
