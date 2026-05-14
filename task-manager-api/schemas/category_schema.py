import re

from marshmallow import Schema, ValidationError, fields, validate, validates

HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')


def _validate_color(value: str) -> None:
    if value is None:
        return
    if not HEX_COLOR_RE.match(value):
        raise ValidationError('Cor inválida; use formato hexadecimal #RRGGBB.')


class CreateCategorySchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(load_default='')
    color = fields.String(load_default='#000000')

    @validates('color')
    def _color(self, value, **_kwargs):
        _validate_color(value)


class UpdateCategorySchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=100))
    description = fields.String()
    color = fields.String()

    @validates('color')
    def _color(self, value, **_kwargs):
        _validate_color(value)
