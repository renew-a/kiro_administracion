from sqlalchemy.exc import IntegrityError
from flask import Blueprint, jsonify, request

from auth.password_hasher import PasswordHasher
from auth.repository import UserRepository
from auth.schemas import LoginSchema, RegisterSchema, UpdateUserSchema
from auth.register_service import RegisterService
from auth.login_service import LoginService
from auth.update_user_service import UpdateUserService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_SERVER_ERROR = {"errors": {"server": "Error interno del servidor."}}


def _deps():
    return UserRepository(), PasswordHasher()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    try:
        schema = RegisterSchema.from_dict(data)
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 422

    repo, hasher = _deps()
    try:
        user = RegisterService(repo, hasher).execute(schema)
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 409
    except IntegrityError:
        return jsonify({"errors": {"server": "El registro falló."}}), 409
    except Exception:
        return jsonify(_SERVER_ERROR), 500

    return jsonify({"message": "Usuario registrado.", "id": user.id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    try:
        schema = LoginSchema.from_dict(data)
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 422

    repo, hasher = _deps()
    try:
        user = LoginService(repo, hasher).execute(schema)
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 401
    except Exception:
        return jsonify(_SERVER_ERROR), 500

    return jsonify({"message": "Login exitoso.", "id": user.id, "username": user.username}), 200


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    data = request.get_json(silent=True) or {}

    try:
        schema = UpdateUserSchema.from_dict(data)
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 422

    repo, hasher = _deps()
    try:
        user = UpdateUserService(repo, hasher).execute(user_id, schema)
    except LookupError as e:
        return jsonify({"errors": e.args[0]}), 404
    except ValueError as e:
        return jsonify({"errors": e.args[0]}), 409
    except IntegrityError:
        return jsonify({"errors": {"server": "La actualización falló."}}), 409
    except Exception:
        return jsonify(_SERVER_ERROR), 500

    return jsonify({"message": "Usuario actualizado.", "id": user.id, "username": user.username, "email": user.email}), 200
