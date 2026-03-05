from bson import ObjectId


def bson_to_json(doc):
    if isinstance(doc, list):
        return [bson_to_json(d) for d in doc]

    if isinstance(doc, dict):
        new_doc = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                new_doc[k] = str(v)
            else:
                new_doc[k] = bson_to_json(v)
        return new_doc

    return doc
