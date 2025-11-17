from app import db

class Contractor(db.Model):
    __tablename__ = "providers_t"
    __table_args__ = {'extend_existing': True}

    provider_id = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(255))
    service_locations = db.Column(db.String(255))
    rate = db.Column(db.Float)
    status = db.Column(db.String(50))
    email_id = db.Column(db.String(255))


    def to_dict(self):
        return {
            "provider_id": self.provider_id,
            "full_name": self.full_name,
            "service_locations": self.service_locations,
            "rate": self.rate,
            "status": self.status,
            "email_id": self.email_id,
        }

    @classmethod
    def get_by_service_location(cls, area):
        try:
            contractors = cls.query.filter(
                cls.service_locations.ilike(f"%{area}%"),
                cls.status == "active"
            ).all()
            return contractors, None
        except Exception as e:
            return None, str(e)

    @classmethod
    def get_all(cls):
        try:
            contractors = cls.query.filter_by(status="active").all()
            return contractors, None
        except Exception as e:
            return None, str(e)