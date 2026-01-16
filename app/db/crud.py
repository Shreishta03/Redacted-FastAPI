from sqlalchemy.orm import Session
from app.db.models import RedactionLog
import json

from sqlalchemy.orm import Session
from app.db.models import User
from app.auth.password import hash_password

def create_redaction_log(
    db: Session,
    input_type: str,
    source_name: str,
    entity_count: int | None,
    columns_redacted: list[str] | None = None
):
    log = RedactionLog(
        input_type=input_type,
        source_name=source_name,
        entity_count=entity_count,
        columns_redacted=json.dumps(columns_redacted) if columns_redacted else None
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log

from sqlalchemy.orm import Session
from app.db.models import User
from app.auth.password import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str):
    hashed_pwd = hash_password(password)

    user = User(
        email=email,
        hashed_password=hashed_pwd
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user