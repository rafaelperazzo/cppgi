import re
import secrets

REGEX_SENHA_FORTE = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{12,}$')

def senha_forte(senha):
    if not senha or not REGEX_SENHA_FORTE.match(senha):
        return False, ('A senha deve ter no mínimo 12 caracteres e incluir letra maiúscula, '
                        'letra minúscula, número e caractere especial.')
    return True, ''

def gerar_token_seguro(nbytes=32):
    return secrets.token_urlsafe(nbytes)

def obter_ip_cliente(request):
    return request.headers.get('CF-Connecting-IP', request.remote_addr)

def extrair_geolocalizacao_cloudflare(headers):
    pais = headers.get('CF-IPCountry', 'N/A')
    cidade = headers.get('CF-IPCity', 'N/A')
    return pais, cidade

def credencial_vazada(headers):
    return headers.get('Exposed-Credential-Check', '') == '1'

def mascarar_email(email):
    try:
        usuario, dominio = email.split('@', 1)
        oculto = usuario[:2] + '*' * max(len(usuario) - 2, 1)
        return oculto + '@' + dominio
    except ValueError:
        return '***'

def cpf_valido(cpf):
    return bool(cpf) and cpf.isdigit() and len(cpf) == 11

def mascarar_cpf(cpf):
    cpf = str(cpf)
    if len(cpf) != 11 or not cpf.isdigit():
        return '*' * len(cpf) if cpf else '***'
    return cpf[:3] + '******' + cpf[-2:]

REGEX_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def email_valido(email):
    return bool(email) and bool(REGEX_EMAIL.match(email))
