def serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }


def serialize_document(doc, status=None):
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "status": status or doc.status
    }


def serialize_history_entry(doc):
    entry = serialize_document(doc)
    entry["created_at"] = doc.created_at.isoformat()
    return entry
