from .database import db
from sqlalchemy import text, func, LargeBinary
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
import json
import base64
from sqlalchemy.dialects.postgresql import JSON, JSONB




class WorkOrder(db.Model):
    """Model represents database table"""
    __tablename__ = "workorder_t"
    __table_args__ = {'extend_existing': True}
    
    ID = db.Column(db.Integer, primary_key=True)
    WORKORDER = db.Column(db.String(255))
    WORKORDER_TYPE = db.Column(db.String(255))
    WORKORDER_AREA = db.Column(db.String(255))
    CREATED_T = db.Column(db.DateTime, default=datetime.utcnow)
    REQUESTED_TIME_CLOSING = db.Column(db.String(255))
    REMARKS = db.Column(db.String(255))
    STATUS = db.Column(db.String(255))
    RATE = db.Column(JSON, nullable=True)
    parent_workorder = db.Column(db.String(255), nullable=True)
    closing_images = db.Column(JSONB, nullable=True, default=[])
    client = db.Column(db.String)
    ticket_assignment_type = db.Column(db.String(50))
    created_by = db.Column(db.String(100))


    
    # ✅ Image stored as binary (PostgreSQL BYTEA)
    image = db.Column(JSONB)
 

    def __repr__(self):
        return f"<WorkOrder {self.WORKORDER}>"

    # ──────────────────────────────────────────────
    # Business Logic Methods
    # ──────────────────────────────────────────────
    

    # ──────────────────────────────────────────────
    # CRUD Methods
    # ──────────────────────────────────────────────
    @classmethod
    def create(cls, data):
        """Insert new workorder using SQL"""
        try:
            sql = text("""
                INSERT INTO workorder_t (
                    "WORKORDER", "WORKORDER_TYPE", "WORKORDER_AREA","client",
                    "REQUESTED_TIME_CLOSING", "REMARKS", "STATUS",
                    "RATE", "image", "closing_images", "CREATED_T",
                    "created_by", "ticket_assignment_type"
                ) VALUES (
                    :WORKORDER, :WORKORDER_TYPE, :WORKORDER_AREA,:CLIENT,
                    :REQUESTED_TIME_CLOSING, :REMARKS, :STATUS,
                    :RATE, :image, :closing_images, :CREATED_T,
                    :created_by, :ticket_assignment_type
                )
                RETURNING *;
            """)

            params = {
                "WORKORDER": data.get("WORKORDER"),
                "WORKORDER_TYPE": data.get("WORKORDER_TYPE"),
                "WORKORDER_AREA": data.get("WORKORDER_AREA"),
                "CLIENT": data.get("CLIENT"),
                "REQUESTED_TIME_CLOSING": data.get("REQUESTED_TIME_CLOSING"),
                "REMARKS": data.get("REMARKS", ""),
                "STATUS": data.get("STATUS", "OPEN"),
                "RATE": json.dumps(data.get("RATE")),
                "image": json.dumps(data.get("image")),
                "closing_images": json.dumps(data.get("closing_images", [])),
                "CREATED_T": datetime.utcnow(),
                "created_by": data.get("created_by"),
                "ticket_assignment_type": data.get("ticket_assignment_type"),

            }

            result = db.session.execute(sql, params)
            db.session.commit()
            row = result.fetchone()
            return dict(row._mapping), None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    
    @classmethod
    def get_all(cls):
        """Get all workorders"""
        try:
            return cls.query.all(), None
        except Exception as e:
            return None, str(e)
    
    @classmethod
    def get_by_id(cls, id):
        """Get single workorder by ID"""
        return cls.query.get(id)
    
    def update(self, data):
        """Update workorder"""
        try:
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def delete(self):
        """Delete workorder"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    

    # ──────────────────────────────────────────────
    # Master data helpers
    # ──────────────────────────────────────────────
    @classmethod
    def get_workorder_types(cls):
        """Fetch all active workorder types"""
        try:
            result = db.session.execute(
                text("SELECT WORKORDER_TYPE FROM WORKORDER_TYPE_T WHERE STATUS='ACTIVE'")
            ).fetchall()
            return [r[0] for r in result], None
        except Exception as e:
            return None, str(e)

    @classmethod
    def get_workorder_areas(cls):
        """Fetch all active workorder areas"""
        try:
            result = db.session.execute(
                text("SELECT WORKORDER_AREA FROM WORKORDER_AREA_T WHERE STATUS='ACTIVE'")
            ).fetchall()
            return [r[0] for r in result], None
        except Exception as e:
            return None, str(e)
        

    @classmethod
    def search_by_workorder_raw(cls, query):
        """Raw SQL search with full debugging (fixed for dict conversion)"""
        try:
            print(f"[DEBUG] search_by_workorder_raw called with query: {query}")
    
            sql = text("""
                SELECT 
                    a.*,
                    b.contractor_id,
                    b.contractor_name,
                    b.contractor_remarks,
                    b.status AS lifecycle_status,
                    b.remarks AS lifecycle_remarks,
                    b.created_t AS lifecycle_created_t
                FROM public."workorder_t" a
                LEFT JOIN public."workorder_life_cycle_t" b
                    ON a."WORKORDER" = b."workorder"
                WHERE a."WORKORDER" = :query
            """)
            
    
            # Use .mappings() to safely convert rows to dictionaries
            results = db.session.execute(sql, {"query": query}).mappings().all()
            print(f"[DEBUG] Number of rows returned: {len(results)}")
    
            combined = []
            for idx, row in enumerate(results):
                row_dict = dict(row)  # now safe
    
                # Convert datetime columns to ISO format
                for key in ['CREATED_T', 'created_t']:
                    if key in row_dict and isinstance(row_dict[key], datetime):
                        row_dict[key] = row_dict[key].isoformat()
    
                # Encode IMAGE as base64 if exists and is bytes
                if 'image' in row_dict and row_dict['image']:
                    if isinstance(row_dict['image'], (bytes, bytearray)):
                        row_dict['image'] = base64.b64encode(row_dict['image']).decode('utf-8')
                    # if it's already dict/list (JSONB), leave it as is
 
                combined.append(row_dict)
    
                if idx == 0:
                    print(f"[DEBUG] First row keys: {row_dict.keys()}")
    
            print(f"[DEBUG] Combined results: {combined}")
            return combined, None
    
        except Exception as e:
            print(f"[ERROR] search_by_workorder_raw exception: {e}")
            return None, str(e)

    # ──────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────
    @classmethod
    def get_next_id(cls):
        """Fetch next ID (if needed for manual sequencing)"""
        max_id = db.session.query(func.max(cls.id)).scalar()
        return (max_id + 1) if max_id is not None else 1

    # ──────────────────────────────────────────────
    # Serialization
    # ──────────────────────────────────────────────
    def to_dict(self):
        rate_json = self.RATE if self.RATE else {}
        total_rate = rate_json.get('total_rate', 0)
        type_rates = rate_json.get('type_rates', {})
    
        image_data = None
        if self.image:
            if isinstance(self.image, (dict, list)):
                image_data = self.image
            else:
                print(f"[WARNING] Unexpected IMAGE type: {type(self.image)}")
    
        return {
            "ID": self.ID,
            "WORKORDER": self.WORKORDER,
            "WORKORDER_TYPE": self.WORKORDER_TYPE,
            "WORKORDER_AREA": self.WORKORDER_AREA,
            "CREATED_T": self.CREATED_T.isoformat() if self.CREATED_T else None,
            "REQUESTED_TIME_CLOSING": self.REQUESTED_TIME_CLOSING,
            "REMARKS": self.REMARKS,
            # "CLIENT": self.CLIENT,
            "STATUS": self.STATUS,
            "RATE": type_rates,
            "total_rate": total_rate,
            "closing_images": self.closing_images if self.closing_images else [],
            "image": self.image,
            # ✅ Add missing fields
            "CLIENT": self.client,
            "ticket_assignment_type": self.ticket_assignment_type,
            "created_by": self.created_by,
            "parent_workorder": self.parent_workorder,
            }
    
    # ──────────────────────────────────────────────
    # Workorder ID generation
    # ──────────────────────────────────────────────
    @classmethod
    def generate_workorder_id(cls, workorder_type):
        """Generates next unique Parent WORKORDER ID"""
        today_str = datetime.now().strftime("%d%m%Y")
        prefix = "P"

        result = db.session.execute(
            text('SELECT "WORKORDER" FROM "workorder_t" ORDER BY "ID" DESC LIMIT 1')
        ).fetchone()

        last_serial = 0
        if result and result[0] and len(result[0]) >= 15:
            try:
                last_serial = int(result[0][-6:])
            except ValueError:
                pass

        serial_str = str(last_serial + 1).zfill(6)
        return f"{today_str}{prefix}{serial_str}"

    @classmethod
    def generates_workorder_id(cls, workorder_type):
        """Generates next unique Child WORKORDER ID"""
        today_str = datetime.now().strftime("%d%m%Y")
        prefix = "W"

        result = db.session.execute(
            text('SELECT "WORKORDER" FROM "workorder_t" ORDER BY "ID" DESC LIMIT 1')
        ).fetchone()

        last_serial = 0
        if result and result[0] and len(result[0]) >= 15:
            try:
                last_serial = int(result[0][-6:])
            except ValueError:
                pass

        serial_str = str(last_serial + 1).zfill(6)
        return f"{today_str}{prefix}{serial_str}"



    @staticmethod
    def get_standard_rates():
        try:
            query = text("""
                SELECT id, state, service, client, price, created_at
                FROM standard_rates_t
                ORDER BY id ASC
            """)
            result = db.session.execute(query)
            rows = result.fetchall()

            data = []
            for row in rows:
                data.append({
                    "id": row.id,
                    "state": row.state,
                    "service": row.service,
                    "client": row.client,
                    "price": float(row.price),
                    "created_at": row.created_at
                })
            return data

        except Exception as e:
            print("[ERROR] get_standard_rates:", e)
            raise

