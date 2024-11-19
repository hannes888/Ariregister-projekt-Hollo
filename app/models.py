from . import db


from . import db


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    registration_code = db.Column(db.String(50), nullable=False, unique=True)
    establishment_date = db.Column(db.Date, nullable=False)
    total_capital = db.Column(db.Integer, nullable=False)
    shareholders = db.relationship('Shareholder', backref='company', lazy=True)


class Individual(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    personal_code = db.Column(db.String(20), nullable=False)


class LegalEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    registration_code = db.Column(db.String(20), nullable=False)


class Shareholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'), nullable=True)
    legal_entity_id = db.Column(db.Integer, db.ForeignKey('legal_entity.id'), nullable=True)
    share_amount = db.Column(db.Integer, nullable=False)
    is_founder = db.Column(db.Boolean, default=False)