from jsonschema import validate


block = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {
            "type": "string"
        },
        "id": {
            "type": "integer"
        },
        "classes": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "content": {
            "type": "object"
        },
        "created": {
            "type": "string"
        },
        "modified": {
            "type": "string"
        }
    },
    "required": ["id"]
}


column = {
    "type": "array",
    "items": block
}


section = {
    "id": "section",
    "type": "object",
    "properties": {
        "columns": {
            "type": "array",
            "items": column
        }
    },
    "required": ["id", "columns"]
}

article = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "order": {
            "type": "integer"
        },
        "sections": {
            "id": "sections",
            "type": "array",
            "items": section
        }
    },
    "required": ["name", "sections"]
}


palette_item = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "hex": {
            "type": "string"
        }
    },
    "required": ["name", "hex"]
}


font = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer"
        },
        "name": {
            "type": "string"
        },
        "fontFamily": {
            "type": "string"
        },
        "url": {
            "type": "string"
        }
    },
    "required": ["id", "name", "fontFamily"]
}

# TODO: Improve theme validation
theme = {
    "id": "theme",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "palette": {
            "type": "array",
            "items": palette_item
        },
        "fonts": {
            "type": "array",
            "items": font
        },
        "fontSizes": {
            "type": "array"
        },
        "buttonStyles": {
            "type": "object"
        },
        "captionStyles": {
            "type": "object"
        },
        "imageStyles": {
            "type": "object"
        },
        "quoteStyles": {
            "type": "object"
        },
        "textStyles": {
            "type": "object"
        },
        "videoStyles": {
            "type": "object"
        }
    }
}


def validate_article(obj):
    validate(obj, article)


def validate_theme(obj):
    validate(obj, theme)
