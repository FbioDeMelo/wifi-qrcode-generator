import os
import uuid
from flask import Flask, render_template, request, flash, redirect, url_for
import qrcode
from PIL import Image

# --- Configuração e Inicialização do App ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura'
app.config['UPLOAD_FOLDER'] = 'static'
# O caminho para o seu logo. Verifique se está correto!
app.config['LOGO_PATH'] = os.path.join(app.config['UPLOAD_FOLDER'], 'logo.png')

# --- Função Auxiliar para Gerar o QR Code ---
def gerar_qr_code_wifi(ssid, password, security, hidden=False):
    """Gera uma imagem de QR Code para conexão Wi-Fi com logo centralizado e sem distorção."""
    wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};"
    if hidden:
        wifi_string += "H:true;"
    wifi_string += ";;"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(wifi_string)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # --- LÓGICA PARA ADICIONAR A LOGO (SEM ESTICAR) ---
    if os.path.exists(app.config['LOGO_PATH']):
        print("Logo encontrada! Tentando adicionar ao QR Code...")
        try:
            logo = Image.open(app.config['LOGO_PATH']).convert("RGBA")

            qr_width, qr_height = qr_img.size
            
            # --- INÍCIO DA CORREÇÃO ---
            # Define o tamanho máximo para a logo (ex: 1/5 do tamanho do QR Code)
            max_logo_size = qr_width // 5
            
            # Redimensiona a logo mantendo sua proporção original (sem esticar)
            logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)
            
            # Pega as novas dimensões da logo (que agora podem não ser quadradas)
            logo_width, logo_height = logo.size
            
            # Calcula a posição para centralizar a logo com base em suas novas dimensões
            pos = ((qr_width - logo_width) // 2, (qr_height - logo_height) // 2)
            # --- FIM DA CORREÇÃO ---
            
            qr_img.paste(logo, pos, mask=logo)
            print("Logo adicionada com sucesso!")
        except Exception as e:
            print(f"Erro ao colar a logo: {e}")
            flash("Não foi possível adicionar a logo ao QR Code.", "warning")
    else:
        print("AVISO: Arquivo da logo não encontrado em:", app.config['LOGO_PATH'])
    # --- FIM DA LÓGICA DA LOGO ---

    filename = f"qrcode_{uuid.uuid4()}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        qr_img.save(filepath)
        # Retorna o caminho completo para a imagem e o nome do arquivo
        return os.path.join('static', filename), filename
    except Exception as e:
        print(f"Erro ao salvar o QR Code: {e}")
        return None, None

# --- Rotas da Aplicação ---
@app.route("/", methods=["GET", "POST"])
def index():
    qr_path = None
    qr_filename = None
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("senha")
        security = request.form.get("tipo", "WPA")
        is_hidden = request.form.get("oculta") == "on"

        if not ssid:
            flash("O nome da rede (SSID) é obrigatório.", "danger")
            return render_template("index.html")

        # A função agora retorna duas variáveis
        qr_path, qr_filename = gerar_qr_code_wifi(ssid, password, security, is_hidden)

        if qr_path:
            flash("QR Code gerado com sucesso!", "success")
        else:
            flash("Ocorreu um erro ao gerar o QR Code. Tente novamente.", "danger")

    # Passa ambas as variáveis para o template
    return render_template("index.html", qr_path=qr_path, qr_filename=qr_filename)

if __name__ == "__main__":
    app.run(debug=True) 