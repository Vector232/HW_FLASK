from auth import check_owner, check_password, check_token, hash_password
from crud import add_item, create_item, delete_item, get_item_by_id, update_item
from errors import HttpError
from flask import jsonify, request
from flask.views import MethodView
from models import Advertisement, Token, User
from schema import CreateAdvertisement, CreateUser, Login, PatchUser, UpdateAdvertisement
from sqlalchemy import func
from sqlalchemy.orm import Session
from tools import validate


class BaseView(MethodView):
    @property
    def session(self) -> Session:
        return request.session

    @property
    def token(self) -> Token:
        return request.token

    @property
    def user(self) -> User:
        return request.token.user


class UserView(BaseView):
    @check_token
    def get(self):
        return jsonify(self.user.dict)

    def post(self):
        payload = validate(CreateUser, request.json)
        payload["password"] = hash_password(payload["password"])
        user = create_item(User, payload, self.session)
        return jsonify({"id": user.id})

    @check_token
    def patch(self):
        payload = validate(PatchUser, request.json)
        user = update_item(self.token.user, payload, self.session)
        return jsonify({"id": user.id})

    @check_token
    def delete(self):
        delete_item(self.token.user, self.session)
        return jsonify({"status": "ok"})


class LoginView(BaseView):
    def post(self):
        payload = validate(Login, request.json)
        user = self.session.query(User).filter_by(name=payload["name"]).first()
        if user is None:
            raise HttpError(404, "user not found")
        if check_password(user.password, payload["password"]):
            token = create_item(Token, {"user_id": user.id}, self.session)
            add_item(token, self.session)
            return jsonify({"token": token.token})
        raise HttpError(401, "invalid password")


class AdvertisementView(BaseView):
    @check_token
    def get(self, advertisement_id: int = None):
        if advertisement_id is None:
            return jsonify([advertisement.dict for advertisement in self.user.advertisements])
        advertisement = get_item_by_id(Advertisement, advertisement_id, self.session)
        check_owner(advertisement, self.token.user_id)
        return jsonify(advertisement.dict)

    @check_token
    def post(self):
        payload = validate(CreateAdvertisement, request.json)
        advertisement = create_item(
            Advertisement, dict(user_id=self.token.user_id, **payload), self.session
        )
        return jsonify({"id": advertisement.id})

    @check_token
    def patch(self, advertisement_id: int):
        payload = validate(UpdateAdvertisement, request.json)
        if "done" in payload:
            payload["finish_time"] = func.now()
        advertisement = get_item_by_id(Advertisement, advertisement_id, self.session)
        check_owner(advertisement, self.token.user_id)
        advertisement = update_item(advertisement, payload, self.session)
        return jsonify({"id": advertisement.id})

    @check_token
    def delete(self, advertisement_id: int):
        advertisement = get_item_by_id(Advertisement, advertisement_id, self.session)
        check_owner(advertisement, self.token.user_id)
        delete_item(advertisement, self.session)
        return jsonify({"status": "ok"})
