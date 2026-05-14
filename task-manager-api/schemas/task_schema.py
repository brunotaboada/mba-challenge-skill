from marshmallow import Schema, ValidationError, fields, validate

from config.constants import (
    PRIORITY_MAX,
    PRIORITY_MIN,
    TITLE_MAX_LEN,
    TITLE_MIN_LEN,
    TaskStatus,
)


class CreateTaskSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=TITLE_MIN_LEN, max=TITLE_MAX_LEN),
    )
    description = fields.String(load_default='')
    status = fields.String(
        load_default=TaskStatus.PENDING.value,
        validate=validate.OneOf(TaskStatus.values()),
    )
    priority = fields.Integer(
        load_default=3,
        validate=validate.Range(min=PRIORITY_MIN, max=PRIORITY_MAX),
    )
    user_id = fields.Integer(load_default=None, allow_none=True)
    category_id = fields.Integer(load_default=None, allow_none=True)
    due_date = fields.Date(load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)


class UpdateTaskSchema(Schema):
    title = fields.String(validate=validate.Length(min=TITLE_MIN_LEN, max=TITLE_MAX_LEN))
    description = fields.String()
    status = fields.String(validate=validate.OneOf(TaskStatus.values()))
    priority = fields.Integer(validate=validate.Range(min=PRIORITY_MIN, max=PRIORITY_MAX))
    user_id = fields.Integer(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    due_date = fields.Date(allow_none=True)
    tags = fields.Raw(allow_none=True)
