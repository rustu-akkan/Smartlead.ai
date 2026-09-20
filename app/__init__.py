from flask import Flask
from flask_cors import CORS
from config import Yapilandirma
from app.database import veri_tabanini_baslat
from chatbot_routes import chatbot_bp

app = Flask(__name__)
app.config.from_object(Yapilandirma)
CORS(app, resources={r"/*": {"origins": Yapilandirma.IZIN_VERILEN_KAYNAKLAR}})
veri_tabanini_baslat(app)

app.register_blueprint(chatbot_bp)

from app import routes