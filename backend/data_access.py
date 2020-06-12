import sqlalchemy.orm
import typing
import uuid
import datetime
from . import models, schemas


# ENTITY THINGS


def get_entity_by_cpf_cnpj(db: sqlalchemy.orm.Session, cpf_cnpj: str) -> models.Entity:
    return db.query(models.Entity).get(cpf_cnpj)


def create_entity(
    db: sqlalchemy.orm.Session, entity: schemas.Entity, persist: bool = True
) -> models.Entity:

    entity_data = entity.dict()

    db_entity = models.Entity(**entity_data)
    db.add(db_entity)
    if persist:
        db.commit()

    db.flush()
    return db_entity


def filter_entity_by_type(
    db: sqlalchemy.orm.Session, type_entity: str, limit: int = 100
) -> typing.List[models.Entity]:
    query = db.query(models.Entity).filter_by(type_entity=type_entity).limit(limit)
    return query.all()


# CHARGE THINGS


def get_charge_by_id(db: sqlalchemy.orm.Session, charge_id: str) -> models.Charge:
    return db.query(models.Charge).get(charge_id)


def get_charge_by_creditor_cpf_cnpj(
    db: sqlalchemy.orm.Session, creditor_cpf_cnpj: str
) -> models.Charge:
    return db.query(models.Charge).get(creditor_cpf_cnpj)


def filter_charge(
    db: sqlalchemy.orm.Session, charge_filter: schemas.ChargeFilter
) -> typing.List[models.Charge]:
    query = db.query(models.Charge)
    if charge_filter.debtor_cpf_cnpj:
        query = query.filter_by(debtor_cpf_cnpj=charge_filter.debtor_cpf_cnpj)

    if charge_filter.creditor_cpf_cnpj:
        query = query.filter_by(creditor_cpf_cnpj=charge_filter.creditor_cpf_cnpj)

    if charge_filter.is_active is not None:
        query = query.filter_by(is_active=charge_filter.is_active)

    return query.all()


def create_charge(
    db: sqlalchemy.orm.Session, charge: schemas.ChargeCreate
) -> models.Charge:
    debtor_db = get_entity_by_cpf_cnpj(db, charge.debtor.cpf_cnpj)
    creditor_db = get_entity_by_cpf_cnpj(db, charge.creditor_cpf_cnpj)

    if not debtor_db:
        debtor_db = create_entity(db, charge.debtor, persist=False)

    db_charge = models.Charge(
        debtor_cpf_cnpj=debtor_db.cpf_cnpj,
        creditor_cpf_cnpj=creditor_db.cpf_cnpj,
        debito=charge.debito,
        is_active=True,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(db_charge)
    db.commit()
    return db_charge


def payment_charge(
    db: sqlalchemy.orm.Session, payment_info: schemas.ChargePayment
) -> models.Charge:
    db_charge = get_charge_by_id(db, payment_info.id)

    if not db_charge:
        raise ValueError("Charge not found to pay")

    if db_charge.creditor_cpf_cnpj != payment_info.creditor_cpf_cnpj:
        raise ValueError("CPF/CNPJ is not the same on charge")

    db_charge.payed_at = datetime.datetime.utcnow()
    db_charge.is_active = False
    db.add(db_charge)
    db.commit()
    return db_charge