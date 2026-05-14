from marshmallow import Schema, fields, validate

from config.constants import PASSWORD_MIN_LEN, UserRole


class CreateUserSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=PASSWORD_MIN_LEN))
    role = fields.String(load_default=UserRole.USER.value, validate=validate.OneOf(UserRole.values()))


class UpdateUserSchema(Schema):
    name = fields.String(validate=validate.Length(min=2, max=100))
    email = fields.Email()
    password = fields.String(validate=validate.Length(min=PASSWORD_MIN_LEN))
    role = fields.String(validate=validate.OneOf(UserRole.values()))
    active = fields.Boolean()


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))
