from flask import Flask
from flask_cors import CORS
from config import Yapilandirma
from app.database import veri_tabanini_baslat
app = Flask(__name__)
app.config.from_object(Yapilandirma)
CORS(app, resources={r"/*": {"origins": Yapilandirma.IZIN_VERILEN_KAYNAKLAR}})
veri_tabanini_baslat(app)
from app import routes