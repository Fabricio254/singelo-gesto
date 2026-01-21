import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import pandas as pd
from PIL import Image
import xml.etree.ElementTree as ET
import requests
import re

# ==================== CONFIGURAÇÕES ====================
# Configurações do Supabase
# Em produção (Streamlit Cloud), usa secrets
# Em desenvolvimento local, usa as variáveis diretas
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # Fallback para desenvolvimento local
    SUPABASE_URL = "https://fjgugglxqyhlyxwzvdts.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqZ3VnZ2x4cXlobHl4d3p2ZHRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzODI4NzQsImV4cCI6MjA3NTk1ODg3NH0.YGQIfxghu4yK58iVoklI1YkwwH6aoprZ06LUsWzcYPk"

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar: {str(e)}")
        return None

# ==================== ESTILO E CORES ====================
def apply_custom_style():
    st.markdown("""
        <style>
        /* Cores baseadas na logo Singelo Gesto */
        :root {
            --primary-color: #C9A58A;
            --secondary-color: #A67C6B;
            --background-color: #F5E6DC;
            --text-color: #6B4E3D;
        }
        
        .stApp {
            background-color: #F5E6DC;
        }
        
        .main-header {
            text-align: center;
            color: #A67C6B;
            font-family: 'Serif';
            padding: 20px 0;
            border-bottom: 2px solid #C9A58A;
            margin-bottom: 30px;
        }
        
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .box-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #C9A58A;
            margin: 10px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .stButton>button {
            background-color: #A67C6B;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 25px;
            font-weight: bold;
            width: 100%;
        }
        
        .stButton>button:hover {
            background-color: #8B6353;
        }
        
        .success-message {
            background-color: #D4EDDA;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28A745;
            margin: 10px 0;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #C9A58A 0%, #A67C6B 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        }
        
        h1, h2, h3 {
            color: #A67C6B;
        }
        
        .stSelectbox label, .stNumberInput label, .stTextInput label {
            color: #6B4E3D !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

# ==================== BOXES PREDEFINIDAS ====================
BOXES = [
    "Box Café da manhã/tarde",
    "Box Chocolate",
    "Box Maternidade",
    "Box Casamento",
    "Box Aniversário",
    "Box Formatura",
    "Box de Flor com Caneca"
]

# ==================== TAMANHOS E CUSTOS ====================
TAMANHOS = {
    "Box mini": 20.00,
    "Box PP": 30.00,
    "Box P": 40.00,
    "Box M": 50.00,
    "Box master": 60.00
}

# ==================== FUNÇÕES DO BANCO DE DADOS ====================
def criar_tabelas():
    """Cria as tabelas no Supabase se não existirem"""
    # Nota: As tabelas devem ser criadas no Supabase Dashboard
    # Esta função é apenas informativa
    st.info("""
    🔧 **Tabelas necessárias no Supabase:**
    
    ⚠️ **IMPORTANTE:** Tabelas com prefixo "singelo_" para não conflitar com o sistema existente
    
    **Tabela: singelo_compras**
    - id (int8, primary key, auto-increment)
    - data (timestamp with time zone)
    - valor_total (numeric)
    - descricao (text, opcional)
    - created_at (timestamp with time zone, default now())
    
    **Tabela: singelo_vendas**
    - id (int8, primary key, auto-increment)
    - data (timestamp with time zone)
    - produto (text)
    - quantidade (int4)
    - valor_total (numeric)
    - created_at (timestamp with time zone, default now())
    
    📝 Execute o script SQL fornecido no arquivo 'criar_tabelas.sql'
    """)

def buscar_xml_por_chave(chave_acesso):
    """Busca o XML da NF-e pela chave de acesso de 44 dígitos"""
    try:
        # Validar se tem 44 dígitos
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            return {
                "sucesso": False,
                "mensagem": "A chave de acesso deve ter exatamente 44 dígitos numéricos"
            }
        
        # Extrair UF da chave (2 primeiros dígitos)
        uf_codigo = chave_acesso[:2]
        
        # Mapa de códigos de UF
        uf_map = {
            '35': 'SP', '33': 'RJ', '31': 'MG', '41': 'PR', '42': 'SC', '43': 'RS',
            '53': 'DF', '52': 'GO', '51': 'MT', '50': 'MS', '11': 'RO', '12': 'AC',
            '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO', '21': 'MA',
            '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
            '28': 'SE', '29': 'BA', '32': 'ES'
        }
        
        uf = uf_map.get(uf_codigo, 'Desconhecido')
        
        # Montar URL da SEFAZ (exemplo para SP)
        # Nota: Cada estado tem sua própria URL e pode requerer autenticação
        if uf == 'ES':
            url = f"https://app.sefaz.es.gov.br/ConsultaNFCe/qrcode.aspx"
            return {
                "sucesso": True,
                "mensagem": f"✅ Link da SEFAZ-ES gerado! Acesse para baixar o XML",
                "url": url,
                "chave": chave_acesso,
                "uf": uf,
                "instrucoes": f"1. Clique no link abaixo\n2. Digite a chave no campo indicado\n3. Clique em 'Consultar'\n4. Baixe o XML na página que abrir"
            }
        elif uf == 'SP':
            url = f"https://www.nfe.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaPublica.aspx"
            return {
                "sucesso": True,
                "mensagem": f"✅ Link da SEFAZ-SP gerado! Acesse para baixar o XML",
                "url": url,
                "chave": chave_acesso,
                "uf": uf,
                "instrucoes": f"1. Clique no link abaixo\n2. Digite a chave no campo indicado\n3. Clique em 'Consultar'\n4. Baixe o XML na página que abrir"
            }
        else:
            # Para outros estados, retornar link genérico
            return {
                "sucesso": False,
                "mensagem": f"Para {uf}, use o QR Code do cupom ou acesse o site da SEFAZ-{uf}",
                "url": None,
                "chave": chave_acesso,
                "uf": uf
            }
        
        return {
            "sucesso": False,
            "mensagem": f"Para SP, acesse o Portal da Nota Fiscal Paulista ou use o QR Code do cupom",
            "url": url,
            "chave": chave_acesso,
            "uf": uf,
            "instrucoes": "O download automático por chave não está disponível devido às restrições de segurança da SEFAZ. Use o QR Code do cupom fiscal para obter o XML rapidamente."
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao processar chave: {str(e)}"
        }

def extrair_dados_html_nfce(html_content):
    """Extrai dados do HTML do DANFE quando o XML não está disponível"""
    try:
        if isinstance(html_content, bytes):
            try:
                html_content = html_content.decode('utf-8')
            except:
                html_content = html_content.decode('latin-1')
        
        # Extrair valor a pagar
        match_valor = re.search(r'Valor a pagar R\$.*?<span class="totalNumb txtMax">(\d+,\d+)</span>', html_content, re.DOTALL)
        valor_total = 0.0
        if match_valor:
            valor_str = match_valor.group(1).replace(',', '.')
            valor_total = float(valor_str)
        
        # Extrair nome do fornecedor
        match_fornecedor = re.search(r'<div id="u20" class="txtTopo">(.*?)</div>', html_content)
        nome_fornecedor = match_fornecedor.group(1).strip() if match_fornecedor else "Fornecedor"
        
        # Extrair data e número da nota
        match_data = re.search(r'<strong>Emissão: </strong>(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', html_content)
        match_numero = re.search(r'<strong>Número: </strong>(\d+)', html_content)
        
        data_emissao = datetime.now()
        if match_data:
            try:
                data_emissao = datetime.strptime(match_data.group(1), '%d/%m/%Y %H:%M:%S')
            except:
                pass
        
        numero_nf = match_numero.group(1) if match_numero else ""
        
        # Extrair itens - formato específico SEFAZ-ES
        itens = []
        
        # Padrão para o formato usado pela SEFAZ-ES com spans Rqtd e RvlUnit
        pattern = r'<span class="txtTit">([^<]+)</span>.*?<span class="Rqtd">\s*<strong>Qtde\.?:\s*</strong>\s*(\d+(?:,\d+)?)\s*</span>.*?<span class="RvlUnit">\s*<strong>Vl\.\s*Unit\.?:\s*</strong>\s*([\d,]+)\s*</span>.*?Vl\.\s*Total.*?<span class="valor">([\d,]+)</span>'
        matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            nome_prod = match.group(1).strip()
            qtd = float(match.group(2).replace(',', '.'))
            valor_unit = float(match.group(3).replace(',', '.'))
            valor_item = float(match.group(4).replace(',', '.'))
            
            itens.append({
                'produto': nome_prod,
                'quantidade': qtd,
                'valor_unitario': valor_unit,
                'valor_total': valor_item
            })
        
        # Criar descrição
        descricao = f"Compra {nome_fornecedor}"
        if numero_nf:
            descricao += f" - NF {numero_nf}"
        
        # Adicionar lista de itens na descrição
        if itens:
            descricao += "\n\nItens comprados:"
            for i, item in enumerate(itens, 1):
                descricao += f"\n{i}. {item['produto']} - {item['quantidade']:.0f} un - R$ {item['valor_total']:.2f}"
        
        return {
            "valor_total": valor_total,
            "data": data_emissao,
            "descricao": descricao,
            "itens": itens,
            "sucesso": True,
            "mensagem": "Dados extraídos do HTML do cupom com sucesso!"
        }
    except Exception as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao extrair dados do HTML: {str(e)}"
        }

def extrair_dados_xml_nfe(xml_content):
    """Extrai dados relevantes do XML da NF-e"""
    try:
        # Se for bytes, decodificar
        if isinstance(xml_content, bytes):
            try:
                xml_content = xml_content.decode('utf-8')
            except:
                xml_content = xml_content.decode('latin-1')
        
        # Limpar o XML de possíveis problemas
        # Remover BOM (Byte Order Mark)
        xml_content = xml_content.replace('\ufeff', '')
        
        # Remover possíveis tags HTML
        xml_content = xml_content.replace('&nbsp;', ' ')
        xml_content = xml_content.replace('&amp;', '&')
        xml_content = xml_content.replace('&lt;', '<')
        xml_content = xml_content.replace('&gt;', '>')
        
        # Tentar encontrar o início do XML se houver HTML antes
        if '<?xml' in xml_content:
            xml_content = xml_content[xml_content.index('<?xml'):]
        elif '<nfeProc' in xml_content:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>' + xml_content[xml_content.index('<nfeProc'):]
        elif '<NFe' in xml_content:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>' + xml_content[xml_content.index('<NFe'):]
        
        # Remover qualquer coisa depois da tag de fechamento
        if '</nfeProc>' in xml_content:
            xml_content = xml_content[:xml_content.index('</nfeProc>') + len('</nfeProc>')]
        elif '</NFe>' in xml_content:
            xml_content = xml_content[:xml_content.index('</NFe>') + len('</NFe>')]
        
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespace da NF-e
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Extrair valor total
        valor_element = root.find('.//nfe:total/nfe:ICMSTot/nfe:vNF', ns)
        valor_total = float(valor_element.text) if valor_element is not None else 0.0
        
        # Extrair data de emissão
        data_element = root.find('.//nfe:ide/nfe:dhEmi', ns)
        if data_element is not None:
            data_emissao = datetime.fromisoformat(data_element.text.replace('Z', '+00:00'))
        else:
            data_emissao = datetime.now()
        
        # Extrair nome do fornecedor
        nome_element = root.find('.//nfe:emit/nfe:xFant', ns)
        if nome_element is None:
            nome_element = root.find('.//nfe:emit/nfe:xNome', ns)
        nome_fornecedor = nome_element.text if nome_element is not None else "Fornecedor"
        
        # Extrair número da nota
        nf_element = root.find('.//nfe:ide/nfe:nNF', ns)
        numero_nf = nf_element.text if nf_element is not None else ""
        
        # Extrair itens da nota
        itens = []
        det_elements = root.findall('.//nfe:det', ns)
        for det in det_elements:
            prod = det.find('nfe:prod', ns)
            if prod is not None:
                nome_prod = prod.find('nfe:xProd', ns)
                qtd_prod = prod.find('nfe:qCom', ns)
                valor_unit = prod.find('nfe:vUnCom', ns)
                valor_prod = prod.find('nfe:vProd', ns)
                
                item = {
                    'produto': nome_prod.text if nome_prod is not None else "Produto",
                    'quantidade': float(qtd_prod.text) if qtd_prod is not None else 0,
                    'valor_unitario': float(valor_unit.text) if valor_unit is not None else 0,
                    'valor_total': float(valor_prod.text) if valor_prod is not None else 0
                }
                itens.append(item)
        
        # Criar descrição
        descricao = f"Compra {nome_fornecedor}"
        if numero_nf:
            descricao += f" - NF {numero_nf}"
        
        # Adicionar lista de itens na descrição
        if itens:
            descricao += "\n\nItens comprados:"
            for i, item in enumerate(itens, 1):
                descricao += f"\n{i}. {item['produto']} - {item['quantidade']:.0f} un - R$ {item['valor_total']:.2f}"
        
        return {
            "valor_total": valor_total,
            "data": data_emissao,
            "descricao": descricao,
            "itens": itens,
            "sucesso": True,
            "mensagem": "XML lido com sucesso!"
        }
    except ET.ParseError as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao processar XML: Formato inválido. Tente salvar o XML novamente usando 'Exibir código-fonte' na página da SEFAZ."
        }
    except Exception as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao ler XML: {str(e)}"
        }

def inserir_compra(supabase: Client, valor_total: float, descricao: str = "", data_compra=None, num_parcelas: int = 1):
    """Insere uma nova compra no banco e cria as parcelas"""
    data_base = data_compra if data_compra else datetime.now()
    
    data = {
        "data": data_base.isoformat(),
        "valor_total": valor_total,
        "descricao": descricao
    }
    result = supabase.table("singelo_compras").insert(data).execute()
    compra_id = result.data[0]['id']
    
    # Criar parcelas com vencimento sempre no dia 12
    if num_parcelas > 1:
        # Se a compra foi feita após o dia 12, começar no próximo mês
        meses_adicionar = 1 if data_base.day > 12 else 0
        
        valor_parcela = valor_total / num_parcelas
        for i in range(num_parcelas):
            # Adicionar i meses à data base (+ ajuste se comprou após dia 12)
            mes_vencimento = data_base.month + i + meses_adicionar
            ano_vencimento = data_base.year
            
            # Ajustar ano se passar de dezembro
            while mes_vencimento > 12:
                mes_vencimento -= 12
                ano_vencimento += 1
            
            # Sempre usar dia 12 como vencimento (dia do fechamento do cartão)
            try:
                data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
            except ValueError:
                # Se o mês não tem dia 12 (não deve acontecer), usar último dia do mês
                from calendar import monthrange
                ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
                data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
            
            parcela_data = {
                "compra_id": compra_id,
                "numero_parcela": i + 1,
                "total_parcelas": num_parcelas,
                "valor_parcela": valor_parcela,
                "data_vencimento": data_vencimento.isoformat(),
                "status": "pendente",
                "descricao": descricao
            }
            supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    else:
        # Compra à vista - criar uma única parcela com vencimento no dia 12
        # Se a compra foi após o dia 12, vencimento vai para o próximo mês
        mes_vencimento = data_base.month + (1 if data_base.day > 12 else 0)
        ano_vencimento = data_base.year
        
        if mes_vencimento > 12:
            mes_vencimento = 1
            ano_vencimento += 1
        
        try:
            data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
        except ValueError:
            from calendar import monthrange
            ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
            data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
        
        parcela_data = {
            "compra_id": compra_id,
            "numero_parcela": 1,
            "total_parcelas": 1,
            "valor_parcela": valor_total,
            "data_vencimento": data_vencimento.isoformat(),
            "status": "pendente",
            "descricao": descricao
        }
        supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    
    return result

def buscar_parcelas_pendentes(supabase: Client, data_inicio=None, data_fim=None):
    """Busca parcelas com vencimento até o final do período (inclui parcelas futuras do mês)"""
    query = supabase.table("singelo_parcelas_compras").select("*")
    
    if data_inicio:
        query = query.gte("data_vencimento", data_inicio.isoformat())
    if data_fim:
        # Buscar até o final do mês da data_fim para pegar parcelas futuras do mês
        from calendar import monthrange
        ultimo_dia = monthrange(data_fim.year, data_fim.month)[1]
        data_fim_mes = datetime(data_fim.year, data_fim.month, ultimo_dia, 23, 59, 59)
        query = query.lte("data_vencimento", data_fim_mes.isoformat())
    
    result = query.order("data_vencimento", desc=False).execute()
    return result.data

def marcar_parcela_paga(supabase: Client, parcela_id: int):
    """Marca uma parcela como paga"""
    data = {
        "status": "pago",
        "data_pagamento": datetime.now().isoformat()
    }
    result = supabase.table("singelo_parcelas_compras").update(data).eq("id", parcela_id).execute()
    return result

def marcar_parcela_pendente(supabase: Client, parcela_id: int):
    """Marca uma parcela como pendente"""
    data = {
        "status": "pendente",
        "data_pagamento": None
    }
    result = supabase.table("singelo_parcelas_compras").update(data).eq("id", parcela_id).execute()
    return result

def buscar_cep(cep: str):
    """Busca informações de endereço pelo CEP usando ViaCEP"""
    try:
        # Remover formatação do CEP
        cep_limpo = ''.join(filter(str.isdigit, cep))
        
        if len(cep_limpo) != 8:
            return {
                "sucesso": False,
                "mensagem": "CEP deve ter 8 dígitos"
            }
        
        # Buscar na API ViaCEP
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dados = response.json()
            
            if 'erro' in dados:
                return {
                    "sucesso": False,
                    "mensagem": "CEP não encontrado"
                }
            
            return {
                "sucesso": True,
                "cep": cep_limpo,
                "logradouro": dados.get('logradouro', ''),
                "bairro": dados.get('bairro', ''),
                "cidade": dados.get('localidade', ''),
                "uf": dados.get('uf', ''),
                "complemento": dados.get('complemento', '')
            }
        else:
            return {
                "sucesso": False,
                "mensagem": "Erro ao consultar CEP"
            }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro: {str(e)}"
        }

def inserir_venda(supabase: Client, produto: str, quantidade: int, valor_total: float, taxa_entrega: float = 0, 
                  tamanho: str = "", data_entrega=None, cep: str = "", logradouro: str = "", numero: str = "", 
                  complemento: str = "", bairro: str = "", cidade: str = "", uf: str = ""):
    """Insere uma nova venda no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "taxa_entrega": taxa_entrega,
        "tamanho": tamanho,
        "data_entrega": data_entrega.isoformat() if data_entrega else None,
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf
    }
    result = supabase.table("singelo_vendas").insert(data).execute()
    return result

def inserir_entrega(supabase: Client, custo_entregador: float, descricao: str = ""):
    """Insere um custo de entregador no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "custo_entregador": custo_entregador,
        "descricao": descricao
    }
    result = supabase.table("singelo_entregas").insert(data).execute()
    return result

def buscar_entregas(supabase: Client, limite: int = 50):
    """Busca os últimos custos de entrega"""
    result = supabase.table("singelo_entregas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def excluir_compra(supabase: Client, compra_id: int):
    """Exclui uma compra do banco"""
    result = supabase.table("singelo_compras").delete().eq("id", compra_id).execute()
    return result

def excluir_venda(supabase: Client, venda_id: int):
    """Exclui uma venda do banco"""
    result = supabase.table("singelo_vendas").delete().eq("id", venda_id).execute()
    return result

def excluir_entrega(supabase: Client, entrega_id: int):
    """Exclui um custo de entrega do banco"""
    result = supabase.table("singelo_entregas").delete().eq("id", entrega_id).execute()
    return result

def atualizar_compra(supabase: Client, compra_id: int, valor_total: float, descricao: str = ""):
    """Atualiza uma compra existente"""
    data = {
        "valor_total": valor_total,
        "descricao": descricao
    }
    result = supabase.table("singelo_compras").update(data).eq("id", compra_id).execute()
    return result

def atualizar_venda(supabase: Client, venda_id: int, produto: str, quantidade: int, valor_total: float, 
                    taxa_entrega: float = 0, tamanho: str = "", data_entrega=None, cep: str = "", 
                    logradouro: str = "", numero: str = "", complemento: str = "", bairro: str = "", 
                    cidade: str = "", uf: str = ""):
    """Atualiza uma venda existente"""
    data = {
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "taxa_entrega": taxa_entrega,
        "tamanho": tamanho,
        "data_entrega": data_entrega.isoformat() if data_entrega else None,
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf
    }
    result = supabase.table("singelo_vendas").update(data).eq("id", venda_id).execute()
    return result

def atualizar_entrega(supabase: Client, entrega_id: int, custo_entregador: float, descricao: str = ""):
    """Atualiza um custo de entrega existente"""
    data = {
        "custo_entregador": custo_entregador,
        "descricao": descricao
    }
    result = supabase.table("singelo_entregas").update(data).eq("id", entrega_id).execute()
    return result

def recalcular_parcelas(supabase: Client, compra_id: int, novo_valor_total: float, novo_num_parcelas: int, data_compra):
    """Recalcula e atualiza todas as parcelas de uma compra"""
    # Excluir parcelas antigas
    supabase.table("singelo_parcelas_compras").delete().eq("compra_id", compra_id).execute()
    
    # Criar novas parcelas com vencimento sempre no dia 12
    # Se a compra foi feita após o dia 12, começar no próximo mês
    meses_adicionar = 1 if data_compra.day > 12 else 0
    
    valor_parcela = novo_valor_total / novo_num_parcelas
    for i in range(novo_num_parcelas):
        # Adicionar i meses à data base (+ ajuste se comprou após dia 12)
        mes_vencimento = data_compra.month + i + meses_adicionar
        ano_vencimento = data_compra.year
        
        # Ajustar ano se passar de dezembro
        while mes_vencimento > 12:
            mes_vencimento -= 12
            ano_vencimento += 1
        
        # Sempre usar dia 12 como vencimento (dia do fechamento do cartão)
        try:
            data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
        except ValueError:
            # Se o mês não tem dia 12 (não deve acontecer), usar último dia do mês
            from calendar import monthrange
            ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
            data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
        
        parcela_data = {
            "compra_id": compra_id,
            "numero_parcela": i + 1,
            "total_parcelas": novo_num_parcelas,
            "valor_parcela": valor_parcela,
            "data_vencimento": data_vencimento.isoformat(),
            "status": "pendente",
            "descricao": ""
        }
        supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    
    return True

def buscar_compras(supabase: Client, limite: int = 50):
    """Busca as últimas compras"""
    result = supabase.table("singelo_compras").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def buscar_vendas(supabase: Client, limite: int = 50):
    """Busca as últimas vendas"""
    result = supabase.table("singelo_vendas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def buscar_entregas(supabase: Client, limite: int = 50):
    """Busca os últimos custos de entrega"""
    result = supabase.table("singelo_entregas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def calcular_resumo(supabase: Client, data_inicio=None, data_fim=None):
    """Calcula o resumo financeiro usando parcelas por vencimento e custos automáticos por data"""
    try:
        # Buscar PARCELAS do período (por data de vencimento)
        query_parcelas = supabase.table("singelo_parcelas_compras").select("valor_parcela, data_vencimento, compra_id")
        
        # Buscar TODAS as compras do período
        query_compras = supabase.table("singelo_compras").select("id, valor_total, data, descricao")
        
        query_vendas = supabase.table("singelo_vendas").select("valor_total, taxa_entrega, data")
        query_entregas = supabase.table("singelo_entregas").select("custo_entregador, data")
        
        if data_inicio:
            query_parcelas = query_parcelas.gte("data_vencimento", data_inicio.isoformat())
            query_compras = query_compras.gte("data", data_inicio.isoformat())
            query_vendas = query_vendas.gte("data", data_inicio.isoformat())
            query_entregas = query_entregas.gte("data", data_inicio.isoformat())
        
        if data_fim:
            # Incluir o dia final completo (até 23:59:59)
            data_fim_final = datetime.combine(data_fim, datetime.max.time())
            query_parcelas = query_parcelas.lte("data_vencimento", data_fim_final.isoformat())
            query_compras = query_compras.lte("data", data_fim_final.isoformat())
            query_vendas = query_vendas.lte("data", data_fim_final.isoformat())
            query_entregas = query_entregas.lte("data", data_fim_final.isoformat())
        
        parcelas = query_parcelas.execute()
        compras = query_compras.execute()
        vendas = query_vendas.execute()
        entregas = query_entregas.execute()
        
        # Separar custos automáticos das compras normais
        custos_auto = [c for c in compras.data if c.get('descricao', '').startswith('Custo automático:')] if compras.data else []
        ids_custos_auto = [c['id'] for c in custos_auto]
        
        # Filtrar parcelas que NÃO são de custos automáticos
        parcelas_normais = [p for p in parcelas.data if p['compra_id'] not in ids_custos_auto] if parcelas.data else []
        
        # Calcular total de parcelas normais (compras de cartão de crédito)
        total_compras_cartao = sum([float(p['valor_parcela']) for p in parcelas_normais])
        
        # Calcular total de custos automáticos (valor total, não parcela)
        total_custos_auto = sum([float(c['valor_total']) for c in custos_auto])
        
        # Total de compras = parcelas normais + custos automáticos
        total_compras = total_compras_cartao + total_custos_auto
        
        total_custo_entregador = sum([float(e['custo_entregador']) for e in entregas.data]) if entregas.data else 0
        
        # Total de vendas = valor da venda + taxa de entrega cobrada do cliente
        total_vendas = sum([float(v['valor_total']) + float(v.get('taxa_entrega', 0)) for v in vendas.data]) if vendas.data else 0
        total_taxa_entrega_cobrada = sum([float(v.get('taxa_entrega', 0)) for v in vendas.data]) if vendas.data else 0
        
        lucro_entregas = total_taxa_entrega_cobrada - total_custo_entregador
        lucro = total_vendas - total_compras
        
        return {
            "total_compras": total_compras,
            "total_compras_cartao": total_compras_cartao,
            "total_custos_auto": total_custos_auto,
            "total_vendas": total_vendas,
            "total_taxa_entrega_cobrada": total_taxa_entrega_cobrada,
            "total_custo_entregador": total_custo_entregador,
            "lucro_entregas": lucro_entregas,
            "lucro": lucro
        }
    except Exception as e:
        return {
            "total_compras": 0,
            "total_compras_cartao": 0,
            "total_custos_auto": 0,
            "total_vendas": 0,
            "total_taxa_entrega_cobrada": 0,
            "total_custo_entregador": 0,
            "lucro_entregas": 0,
            "lucro": 0
        }

# ==================== INTERFACE PRINCIPAL ====================
def main():
    # Configurações da página
    st.set_page_config(
        page_title="Singelo Gesto - Gestão de Vendas",
        page_icon="🎁",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_style()
    
    # Header com logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            logo = Image.open("Z:/codigos/Singelo/logo.png")
            st.image(logo, use_container_width=True)
        except:
            st.markdown("<div class='main-header'><h1>🎁 Singelo Gesto</h1><p>Box de Luxo Personalizadas</p></div>", unsafe_allow_html=True)
    
    # Verificar configuração do Supabase
    if "COLE_SUA" in SUPABASE_KEY or SUPABASE_KEY == "SUA_KEY_AQUI":
        st.error("⚠️ **Configure a ANON KEY do Supabase no arquivo app.py**")
        st.info("📝 Cole a sua Anon Key na variável SUPABASE_KEY no início do arquivo app.py")
        criar_tabelas()
        return
    
    # Inicializar Supabase
    try:
        supabase = init_supabase()
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Supabase: {str(e)}")
        return
    
    # Sidebar - Menu
    with st.sidebar:
        st.markdown("### 📊 Menu Principal")
        opcao = st.radio(
            "Selecione uma opção:",
            ["📈 Dashboard", "🛒 Lançar Compra", "💰 Lançar Venda", "🚚 Custo Entregador", "💳 Contas a Pagar", "📋 Histórico"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ Sobre")
        st.markdown("Sistema de gestão para **Singelo Gesto**")
        st.markdown("Box de Luxo Personalizadas")
    
    # ==================== DASHBOARD ====================
    if opcao == "📈 Dashboard":
        st.markdown("## 📈 Dashboard Financeiro")
        
        # Filtros de período
        st.markdown("### 📅 Filtrar por Período")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        # Data padrão: dia 12 do mês atual até dia 12 do próximo mês
        hoje = datetime.now()
        data_inicio_padrao = datetime(hoje.year, hoje.month, 12)
        
        # Calcular dia 12 do próximo mês
        mes_fim = hoje.month + 1
        ano_fim = hoje.year
        if mes_fim > 12:
            mes_fim = 1
            ano_fim += 1
        data_fim_padrao = datetime(ano_fim, mes_fim, 12)
        
        with col1:
            data_inicio = st.date_input(
                "Data Início",
                value=data_inicio_padrao,
                format="DD/MM/YYYY",
                help="Data de início do período (padrão: dia 12 do mês atual)",
                key="data_inicio_dash"
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Fim",
                value=data_fim_padrao,
                format="DD/MM/YYYY",
                help="Data de fim do período (padrão: dia 12 do próximo mês)",
                key="data_fim_dash"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Limpar Filtros", key="limpar_filtros"):
                st.rerun()
        
        # Converter None para None explicitamente
        data_inicio_filtro = data_inicio if data_inicio else None
        data_fim_filtro = data_fim if data_fim else None
        
        if data_inicio_filtro and data_fim_filtro and data_inicio_filtro > data_fim_filtro:
            st.error("❌ A data de início deve ser anterior à data de fim!")
            return
        
        # Mostrar período selecionado
        if data_inicio_filtro or data_fim_filtro:
            periodo_texto = "Período: "
            if data_inicio_filtro:
                periodo_texto += f"de {data_inicio_filtro.strftime('%d/%m/%Y')}"
            if data_fim_filtro:
                periodo_texto += f" até {data_fim_filtro.strftime('%d/%m/%Y')}"
            st.info(f"📊 {periodo_texto}")
        else:
            st.info("📊 Mostrando todos os dados")
        
        st.markdown("---")
        
        resumo = calcular_resumo(supabase, data_inicio_filtro, data_fim_filtro)
        
        # Linha 1: Compras Cartão, Custos Automáticos, Vendas e Lucro
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card' style='background: #8B4513;'>
                    <h3>💳 Compras Cartão</h3>
                    <h2>R$ {resumo['total_compras_cartao']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card' style='background: #D2691E;'>
                    <h3>📝 Custos Box</h3>
                    <h2>R$ {resumo['total_custos_auto']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>💰 Total Vendas</h3>
                    <h2>R$ {resumo['total_vendas']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            lucro_color = "#28A745" if resumo['lucro'] >= 0 else "#DC3545"
            st.markdown(f"""
                <div class='metric-card' style='background: {lucro_color};'>
                    <h3>📊 Lucro Vendas</h3>
                    <h2>R$ {resumo['lucro']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Linha 2: Entregas
        st.markdown("### 🚚 Controle de Entregas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);'>
                    <h3>💵 Taxa Cobrada</h3>
                    <h2>R$ {resumo['total_taxa_entrega_cobrada']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, #E67E22 0%, #D35400 100%);'>
                    <h3>🚚 Custo Entregador</h3>
                    <h2>R$ {resumo['total_custo_entregador']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            lucro_entrega_color = "#28A745" if resumo['lucro_entregas'] >= 0 else "#DC3545"
            status_entrega = "Lucro" if resumo['lucro_entregas'] >= 0 else "Prejuízo"
            st.markdown(f"""
                <div class='metric-card' style='background: {lucro_entrega_color};'>
                    <h3>📊 {status_entrega} Entregas</h3>
                    <h2>R$ {resumo['lucro_entregas']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Últimas movimentações
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🛒 Últimas Compras")
            compras = buscar_compras(supabase, 5)
            if compras:
                for compra in compras:
                    data_formatada = datetime.fromisoformat(compra['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    st.markdown(f"""
                        <div class='box-card'>
                            <strong>📅 {data_formatada}</strong><br>
                            💵 R$ {float(compra['valor_total']):,.2f}<br>
                            {f"📝 {compra.get('descricao', '')}" if compra.get('descricao') else ""}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma compra registrada ainda")
        
        with col2:
            st.markdown("### 💰 Últimas Vendas")
            vendas = buscar_vendas(supabase, 5)
            if vendas:
                for venda in vendas:
                    data_formatada = datetime.fromisoformat(venda['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    st.markdown(f"""
                        <div class='box-card'>
                            <strong>📅 {data_formatada}</strong><br>
                            🎁 {venda['produto']}<br>
                            📦 Quantidade: {venda['quantidade']}<br>
                            💵 R$ {float(venda['valor_total']):,.2f}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma venda registrada ainda")
    
    # ==================== LANÇAR COMPRA ====================
    elif opcao == "🛒 Lançar Compra":
        st.markdown("## 🛒 Lançar Nova Compra")
        
        # Tabs para escolher entre manual, XML e chave de acesso
        tab1, tab2, tab3 = st.tabs(["✍então a logica é o seguinte, ️ Digitar Manualmente", "📄 Importar XML", "🔑 Buscar por Chave"])
        
        with tab1:
            with st.form("form_compra"):
                st.markdown("### Informações da Compra")
                
                valor = st.number_input(
                    "💵 Valor Total da Compra (R$)",
                    min_value=0.01,
                    value=0.01,
                    step=0.01,
                    format="%.2f"
                )
                
                descricao = st.text_area(
                    "📝 Descrição (opcional)",
                    placeholder="Ex: Compra de materiais, embalagens, ingredientes..."
                )
                
                num_parcelas = st.selectbox(
                    "💳 Número de Parcelas",
                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                    format_func=lambda x: f"{x}x" if x > 1 else "À vista",
                    help="Selecione em quantas parcelas a compra será dividida"
                )
                
                # Mostrar valor das parcelas
                if num_parcelas > 1:
                    valor_parcela = valor / num_parcelas
                    st.info(f"💰 Valor de cada parcela: R$ {valor_parcela:,.2f}")
                
                submitted = st.form_submit_button("✅ Registrar Compra", use_container_width=True)
            
            if submitted:
                if valor > 0:
                    try:
                        inserir_compra(supabase, valor, descricao, num_parcelas=num_parcelas)
                        parcelas_info = f"{num_parcelas}x de R$ {valor/num_parcelas:,.2f}" if num_parcelas > 1 else "à vista"
                        st.markdown(f"""
                            <div class='success-message'>
                                ✅ <strong>Compra registrada com sucesso!</strong><br>
                                Valor: R$ {valor:,.2f} ({parcelas_info})
                            </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar compra: {str(e)}")
                else:
                    st.warning("⚠️ O valor deve ser maior que zero")
        
        with tab2:
            st.markdown("### 📄 Importar XML da Nota Fiscal")
            st.info("💡 **Como obter o XML:** Escaneie o QR Code do cupom fiscal com seu celular e faça o download do arquivo XML")
            
            uploaded_file = st.file_uploader(
                "Selecione o arquivo XML",
                type=['xml'],
                help="Faça upload do arquivo XML da NF-e",
                key="xml_upload"
            )
            
            if uploaded_file is not None:
                try:
                    # Ler conteúdo do arquivo
                    xml_content = uploaded_file.read()
                    
                    # Verificar se é HTML (DANFE) ou XML
                    content_str = xml_content.decode('utf-8', errors='ignore') if isinstance(xml_content, bytes) else xml_content
                    
                    if '<!DOCTYPE html>' in content_str or '<html' in content_str:
                        # É um HTML do DANFE, extrair dados do HTML
                        dados = extrair_dados_html_nfce(xml_content)
                    else:
                        # É XML, processar normalmente
                        dados = extrair_dados_xml_nfe(xml_content)
                    
                    if dados['sucesso']:
                        st.success(dados['mensagem'])
                        
                        # Mostrar dados extraídos
                        st.markdown("### 📊 Dados Extraídos do XML")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("💵 Valor Total", f"R$ {dados['valor_total']:,.2f}")
                        with col2:
                            st.metric("📅 Data", dados['data'].strftime('%d/%m/%Y'))
                        with col3:
                            st.metric("🏪 Fornecedor", dados['descricao'].split(' - ')[0].replace('Compra ', ''))
                        
                        st.info(f"📝 Descrição: {dados['descricao']}")
                        
                        # Mostrar itens da nota fiscal
                        st.markdown("---")
                        st.markdown("### 🛒 Itens da Nota Fiscal")
                        
                        if dados.get('itens') and len(dados['itens']) > 0:
                            st.markdown(f"**Total de itens:** {len(dados['itens'])}")
                            
                            # Criar DataFrame com os itens
                            df_itens = pd.DataFrame(dados['itens'])
                            df_itens['quantidade'] = df_itens['quantidade'].apply(lambda x: f"{x:.2f}")
                            df_itens['valor_unitario'] = df_itens['valor_unitario'].apply(lambda x: f"R$ {x:.2f}")
                            df_itens['valor_total'] = df_itens['valor_total'].apply(lambda x: f"R$ {x:.2f}")
                            
                            # Renomear colunas
                            df_itens.columns = ['Produto', 'Quantidade', 'Valor Unit.', 'Valor Total']
                            
                            # Mostrar tabela
                            st.dataframe(df_itens, use_container_width=True, hide_index=True)
                        else:
                            st.warning("⚠️ Não foi possível extrair os itens do arquivo. Verifique se o formato está correto.")
                            st.info("💡 **Dica:** Alguns cupons fiscais em HTML podem não conter os detalhes dos produtos. Tente fazer o download do XML puro através do QR Code.")
                        
                        st.markdown("---")
                        
                        # Campo para selecionar parcelas
                        num_parcelas_xml = st.selectbox(
                            "💳 Número de Parcelas",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                            format_func=lambda x: f"{x}x" if x > 1 else "À vista",
                            help="Selecione em quantas parcelas a compra será dividida",
                            key="parcelas_xml"
                        )
                        
                        if num_parcelas_xml > 1:
                            valor_parcela = dados['valor_total'] / num_parcelas_xml
                            st.info(f"💰 Valor de cada parcela: R$ {valor_parcela:,.2f}")
                        
                        # Botão para confirmar importação
                        if st.button("✅ Confirmar e Registrar Compra", use_container_width=True, type="primary", key="btn_confirmar_xml"):
                            try:
                                inserir_compra(supabase, dados['valor_total'], dados['descricao'], dados['data'], num_parcelas_xml)
                                parcelas_info = f"{num_parcelas_xml}x de R$ {dados['valor_total']/num_parcelas_xml:,.2f}" if num_parcelas_xml > 1 else "à vista"
                                st.markdown(f"""
                                    <div class='success-message'>
                                        ✅ <strong>Compra importada e registrada com sucesso!</strong><br>
                                        Fornecedor: {dados['descricao']}<br>
                                        Valor: R$ {dados['valor_total']:,.2f} ({parcelas_info})<br>
                                        Data: {dados['data'].strftime('%d/%m/%Y %H:%M')}
                                    </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Erro ao registrar compra: {str(e)}")
                    else:
                        st.error(dados['mensagem'])
                        st.warning("⚠️ Verifique se o arquivo é um XML válido de NF-e")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                    st.warning("⚠️ Certifique-se de que o arquivo é um XML válido de Nota Fiscal Eletrônica")
        
        with tab3:
            st.markdown("### 🔑 Buscar XML pela Chave de Acesso")
            st.info("💡 **Onde encontrar:** A chave de acesso de 44 dígitos está no rodapé do cupom fiscal")
            
            # Campo para digitar a chave
            chave_acesso = st.text_input(
                "Digite a Chave de Acesso (44 dígitos)",
                max_chars=44,
                placeholder="Ex: 35240112345678901234550010000123451234567890",
                help="Digite apenas números, sem espaços ou caracteres especiais",
                key="chave_acesso_input"
            )
            
            # Botão para buscar
            if st.button("🔍 Buscar XML", use_container_width=True, type="primary", key="btn_buscar_chave"):
                if chave_acesso:
                    # Remover espaços e caracteres não numéricos
                    chave_limpa = ''.join(filter(str.isdigit, chave_acesso))
                    
                    with st.spinner("Buscando informações da nota fiscal..."):
                        resultado = buscar_xml_por_chave(chave_limpa)
                    
                    if resultado.get('sucesso'):
                        st.success(resultado['mensagem'])
                        
                        # Mostrar informações
                        st.markdown(f"**🗺️ Estado:** {resultado['uf']}")
                        st.markdown(f"**🔑 Chave:** {resultado['chave']}")
                        
                        # Mostrar instruções
                        if 'instrucoes' in resultado:
                            st.info(f"📋 **Instruções:**\n\n{resultado['instrucoes']}")
                        
                        # Botão para acessar SEFAZ
                        if 'url' in resultado and resultado['url']:
                            st.markdown("---")
                            st.markdown(f"### 🔗 [Clique aqui para acessar a SEFAZ-{resultado['uf']}]({resultado['url']})")
                            st.markdown(f"**Cole esta chave lá:** `{resultado['chave']}`")
                            
                            # Botão de copiar
                            if st.button("📋 Copiar Chave", key="copiar_chave"):
                                st.code(resultado['chave'], language=None)
                                st.success("✅ Chave copiada! Cole na página da SEFAZ")
                    else:
                        st.warning(resultado['mensagem'])
                        
                        if 'uf' in resultado:
                            st.markdown(f"**🗺️ Estado:** {resultado['uf']}")
                        
                        if 'instrucoes' in resultado:
                            st.info(f"ℹ️ {resultado['instrucoes']}")
                        
                        # Mostrar instruções alternativas
                        st.markdown("---")
                        st.markdown("### 📱 Alternativa Recomendada: Use o QR Code")
                        st.markdown("""
                        **Passos para obter o XML pelo QR Code:**
                        1. 📸 Abra a câmera do celular
                        2. 🎯 Aponte para o QR Code do cupom
                        3. 🌐 Abrirá um link da SEFAZ
                        4. 📥 Clique em "Download XML" ou "Baixar XML"
                        5. 💾 Salve o arquivo
                        6. ⬆️ Volte aqui e faça upload na aba "Importar XML"
                        """)
                        
                        # Mostrar link se disponível
                        if 'url' in resultado and resultado['url']:
                            st.markdown(f"**🔗 Ou acesse diretamente:** [Portal da SEFAZ]({resultado['url']})")
                else:
                    st.warning("⚠️ Digite a chave de acesso de 44 dígitos")
    
    # ==================== LANÇAR VENDA ====================
    elif opcao == "💰 Lançar Venda":
        st.markdown("## 💰 Lançar Nova Venda")
        
        # Seletores fora do form para atualização em tempo real
        col1, col2 = st.columns(2)
        
        with col1:
            produto = st.selectbox(
                "🎁 Selecione a Box",
                options=BOXES,
                index=0,
                key="produto_select"
            )
        
        with col2:
            tamanho = st.selectbox(
                "📏 Tamanho da Box",
                options=list(TAMANHOS.keys()),
                index=0,
                help="O custo será registrado automaticamente",
                key="tamanho_select"
            )
        
        # Mostrar o custo que será registrado (atualiza em tempo real)
        custo_box = TAMANHOS[tamanho]
        st.info(f"💰 Custo desta box: R$ {custo_box:,.2f} (será registrado automaticamente nas compras)")
        
        st.markdown("### Informações da Venda")
        
        # Campos fora do form para evitar problema do Enter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quantidade = st.number_input(
                "📦 Quantidade",
                min_value=0,
                value=1,
                step=1,
                key="qtd_venda"
            )
        
        with col2:
            valor = st.number_input(
                "💵 Valor Total da Venda (R$)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f",
                key="valor_venda"
            )
        
        with col3:
            taxa_entrega = st.number_input(
                "🚚 Taxa Entrega (R$)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f",
                help="Valor cobrado do cliente pela entrega",
                key="taxa_entrega"
            )
        
        st.markdown("---")
        st.markdown("### 📍 Endereço de Entrega")
        
        # Inicializar session_state para endereço se não existir
        if 'endereco_logradouro' not in st.session_state:
            st.session_state.endereco_logradouro = ''
        if 'endereco_bairro' not in st.session_state:
            st.session_state.endereco_bairro = ''
        if 'endereco_cidade' not in st.session_state:
            st.session_state.endereco_cidade = ''
        if 'endereco_uf' not in st.session_state:
            st.session_state.endereco_uf = ''
        if 'ultimo_cep' not in st.session_state:
            st.session_state.ultimo_cep = ''
        
        # Campo de data de entrega
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            data_entrega = st.date_input(
                "📅 Data de Entrega",
                value=datetime.now().date(),
                help="Data prevista para entrega",
                format="DD/MM/YYYY",
                key="data_entrega"
            )
        
        with col2:
            cep_input = st.text_input(
                "📮 CEP",
                max_chars=9,
                placeholder="00000-000",
                help="Digite o CEP (8 dígitos)",
                key="cep_input"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_cep_btn = st.button("🔍 Buscar", use_container_width=True, key="btn_buscar_cep")
        
        # Buscar CEP quando clicar no botão
        if buscar_cep_btn:
            cep_limpo = ''.join(filter(str.isdigit, cep_input))
            if cep_limpo and len(cep_limpo) == 8:
                with st.spinner("🔍 Buscando endereço..."):
                    endereco_encontrado = buscar_cep(cep_input)
                    if endereco_encontrado['sucesso']:
                        # Atualizar session_state com os dados encontrados
                        st.session_state.endereco_logradouro = endereco_encontrado.get('logradouro', '')
                        st.session_state.endereco_bairro = endereco_encontrado.get('bairro', '')
                        st.session_state.endereco_cidade = endereco_encontrado.get('cidade', '')
                        st.session_state.endereco_uf = endereco_encontrado.get('uf', '')
                        st.session_state.ultimo_cep = cep_limpo
                        st.success(f"✅ Endereço encontrado: {endereco_encontrado['logradouro']}, {endereco_encontrado['bairro']} - {endereco_encontrado['cidade']}/{endereco_encontrado['uf']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {endereco_encontrado['mensagem']}")
            else:
                st.warning("⚠️ Digite um CEP válido com 8 dígitos")
        
        # Campos de endereço (editáveis, preenchidos automaticamente)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            logradouro = st.text_input(
                "🏠 Rua/Avenida",
                value=st.session_state.endereco_logradouro,
                placeholder="Ex: Rua das Flores"
            )
            # Atualizar session_state se usuário editou
            if logradouro != st.session_state.endereco_logradouro:
                st.session_state.endereco_logradouro = logradouro
        
        with col2:
            numero = st.text_input(
                "🔢 Número",
                placeholder="123",
                key="numero"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            bairro = st.text_input(
                "🏘️ Bairro",
                value=st.session_state.endereco_bairro,
                placeholder="Ex: Centro"
            )
            # Atualizar session_state se usuário editou
            if bairro != st.session_state.endereco_bairro:
                st.session_state.endereco_bairro = bairro
        
        with col2:
            complemento = st.text_input(
                "🏢 Complemento (opcional)",
                placeholder="Ex: Apto 101, Bloco B",
                key="complemento"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            cidade = st.text_input(
                "🌆 Cidade",
                value=st.session_state.endereco_cidade,
                placeholder="Ex: São Paulo"
            )
            # Atualizar session_state se usuário editou
            if cidade != st.session_state.endereco_cidade:
                st.session_state.endereco_cidade = cidade
        
        with col2:
            uf = st.text_input(
                "🗺️ Estado (UF)",
                value=st.session_state.endereco_uf,
                max_chars=2,
                placeholder="SP"
            )
            # Atualizar session_state se usuário editou
            if uf != st.session_state.endereco_uf:
                st.session_state.endereco_uf = uf
        
        st.markdown("---")
        
        # Botão de submit fora do form
        if st.button("✅ Registrar Venda", use_container_width=True, type="primary", key="btn_submit_venda"):
            submitted = True
        else:
            submitted = False
        
        if submitted:
            if valor <= 0:
                st.error("❌ O valor da venda deve ser maior que zero!")
            elif quantidade <= 0:
                st.error("❌ A quantidade deve ser maior que zero!")
            else:
                try:
                    # Registrar a venda com endereço
                    inserir_venda(supabase, produto, quantidade, valor, taxa_entrega, tamanho, 
                                data_entrega, cep_input, logradouro, numero, complemento, bairro, cidade, uf)
                    
                    # Registrar o custo da box automaticamente nas compras
                    custo_total = custo_box * quantidade
                    descricao_compra = f"Custo automático: {quantidade}x {tamanho} - {produto}"
                    inserir_compra(supabase, custo_total, descricao_compra)
                    
                    endereco_completo = f"{logradouro}, {numero}" if numero else logradouro
                    if complemento:
                        endereco_completo += f" - {complemento}"
                    endereco_completo += f" - {bairro}, {cidade}/{uf}" if cidade else ""
                    
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Venda registrada com sucesso!</strong><br>
                            {produto} ({tamanho}) - {quantidade} unidade(s)<br>
                            Valor Venda: R$ {valor:,.2f}<br>
                            Taxa Entrega: R$ {taxa_entrega:,.2f}<br>
                            📅 Entrega: {data_entrega.strftime('%d/%m/%Y')}<br>
                            📍 Endereço: {endereco_completo}<br>
                            💰 Custo registrado: R$ {custo_total:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Limpar session_state do endereço para nova venda
                    st.session_state.endereco_logradouro = ''
                    st.session_state.endereco_bairro = ''
                    st.session_state.endereco_cidade = ''
                    st.session_state.endereco_uf = ''
                    st.session_state.ultimo_cep = ''
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar venda: {str(e)}")
    
    # ==================== CUSTO ENTREGADOR ====================
    elif opcao == "🚚 Custo Entregador":
        st.markdown("## 🚚 Lançar Custo de Entregador")
        
        with st.form("form_entrega"):
            st.markdown("### Informações do Custo")
            
            custo = st.number_input(
                "💵 Valor Pago ao Entregador (R$)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
                help="Quanto você pagou ao entregador"
            )
            
            descricao = st.text_area(
                "📝 Descrição (opcional)",
                placeholder="Ex: Entrega bairro X, 3 pedidos..."
            )
            
            submitted = st.form_submit_button("✅ Registrar Custo", use_container_width=True)
        
        if submitted:
            if custo > 0:
                try:
                    inserir_entrega(supabase, custo, descricao)
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Custo de entrega registrado com sucesso!</strong><br>
                            Valor: R$ {custo:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar custo: {str(e)}")
            else:
                st.warning("⚠️ O valor deve ser maior que zero")
    
    # ==================== CONTAS A PAGAR ====================
    elif opcao == "💳 Contas a Pagar":
        st.markdown("## 💳 Controle de Contas a Pagar")
        
        # Filtros de período
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            data_inicio = st.date_input(
                "📅 Data Início",
                value=datetime.now().replace(day=1),
                format="DD/MM/YYYY",
                help="Selecione a data inicial do período"
            )
        
        with col2:
            # Último dia do mês atual
            from calendar import monthrange
            ultimo_dia = monthrange(datetime.now().year, datetime.now().month)[1]
            data_fim = st.date_input(
                "📅 Data Fim",
                value=datetime.now().replace(day=ultimo_dia),
                format="DD/MM/YYYY",
                help="Selecione a data final do período"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Filtrar", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # Buscar parcelas do período
        parcelas = buscar_parcelas_pendentes(supabase, datetime.combine(data_inicio, datetime.min.time()), datetime.combine(data_fim, datetime.max.time()))
        
        # Marcar automaticamente como paga as parcelas vencidas (compras de cartão)
        parcelas_marcadas = 0
        if parcelas:
            for parcela in parcelas:
                if parcela['status'] == 'pendente':
                    data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                    # Se vencimento já passou, marcar como paga automaticamente
                    if data_venc.date() < datetime.now().date():
                        try:
                            marcar_parcela_paga(supabase, parcela['id'])
                            parcelas_marcadas += 1
                        except:
                            pass
            
            # Se marcou alguma parcela, recarregar dados
            if parcelas_marcadas > 0:
                st.success(f"✅ {parcelas_marcadas} parcela(s) vencida(s) marcada(s) como paga(s) automaticamente")
                parcelas = buscar_parcelas_pendentes(supabase, datetime.combine(data_inicio, datetime.min.time()), datetime.combine(data_fim, datetime.max.time()))
        
        if parcelas:
            # Separar em pagas e pendentes
            parcelas_pendentes = [p for p in parcelas if p['status'] == 'pendente']
            parcelas_pagas = [p for p in parcelas if p['status'] == 'pago']
            
            # Resumo
            total_pendente = sum([float(p['valor_parcela']) for p in parcelas_pendentes])
            total_pago = sum([float(p['valor_parcela']) for p in parcelas_pagas])
            total_geral = total_pendente + total_pago
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);'>
                        <h3>⏰ Pendente</h3>
                        <h2>R$ {total_pendente:,.2f}</h2>
                        <p>{len(parcelas_pendentes)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #28A745 0%, #218838 100%);'>
                        <h3>✅ Pago</h3>
                        <h2>R$ {total_pago:,.2f}</h2>
                        <p>{len(parcelas_pagas)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);'>
                        <h3>📊 Total</h3>
                        <h2>R$ {total_geral:,.2f}</h2>
                        <p>{len(parcelas)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Tabs para separar pendentes e pagas
            tab1, tab2 = st.tabs([f"⏰ Pendentes ({len(parcelas_pendentes)})", f"✅ Pagas ({len(parcelas_pagas)})"])
            
            with tab1:
                st.markdown("### ⏰ Parcelas Pendentes")
                
                if parcelas_pendentes:
                    for parcela in parcelas_pendentes:
                        data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                        dias_para_vencer = (data_venc.date() - datetime.now().date()).days
                        
                        # Determinar cor baseado em dias para vencer (atrasadas já são marcadas como pagas automaticamente)
                        if dias_para_vencer <= 7:
                            cor_status = "🟡 Vence em breve"
                            estilo_extra = "border-left: 4px solid #F39C12;"
                        else:
                            cor_status = "🟢 No prazo"
                            estilo_extra = "border-left: 4px solid #28A745;"
                        
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class='box-card' style='{estilo_extra}'>
                                    <strong>{cor_status}</strong><br>
                                    📅 Vencimento: {data_venc.strftime('%d/%m/%Y')}<br>
                                    💵 Valor: R$ {float(parcela['valor_parcela']):,.2f}<br>
                                    📦 Parcela: {parcela['numero_parcela']}/{parcela['total_parcelas']}<br>
                                    {f"📝 {parcela.get('descricao', '')}" if parcela.get('descricao') else ""}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✅ Marcar como Paga", key=f"pagar_{parcela['id']}", use_container_width=True):
                                try:
                                    marcar_parcela_paga(supabase, parcela['id'])
                                    st.success("Parcela marcada como paga!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                else:
                    st.info("✅ Nenhuma parcela pendente no período selecionado")
            
            with tab2:
                st.markdown("### ✅ Parcelas Pagas")
                
                if parcelas_pagas:
                    for parcela in parcelas_pagas:
                        data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                        data_pag = datetime.fromisoformat(parcela['data_pagamento'].replace('Z', '+00:00')) if parcela.get('data_pagamento') else None
                        
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class='box-card' style='border-left: 4px solid #28A745;'>
                                    <strong>✅ Paga</strong><br>
                                    📅 Vencimento: {data_venc.strftime('%d/%m/%Y')}<br>
                                    💵 Valor: R$ {float(parcela['valor_parcela']):,.2f}<br>
                                    📦 Parcela: {parcela['numero_parcela']}/{parcela['total_parcelas']}<br>
                                    {f"💳 Pago em: {data_pag.strftime('%d/%m/%Y %H:%M')}" if data_pag else ""}<br>
                                    {f"📝 {parcela.get('descricao', '')}" if parcela.get('descricao') else ""}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("↩️ Desfazer", key=f"desfazer_{parcela['id']}", use_container_width=True):
                                try:
                                    marcar_parcela_pendente(supabase, parcela['id'])
                                    st.success("Status alterado para pendente!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                else:
                    st.info("Nenhuma parcela paga no período selecionado")
        else:
            st.info("Nenhuma conta a pagar encontrada no período selecionado")
    
    # ==================== HISTÓRICO ====================
    elif opcao == "📋 Histórico":
        st.markdown("## 📋 Histórico de Movimentações")
        
        tab1, tab2, tab3 = st.tabs(["🛒 Compras", "💰 Vendas", "🚚 Entregas"])
        
        with tab1:
            st.markdown("### 🛒 Histórico de Compras")
            compras = buscar_compras(supabase, 100)
            
            if compras:
                # Total
                total = sum([float(c['valor_total']) for c in compras])
                st.markdown(f"**Total de Compras:** R$ {total:,.2f}")
                st.markdown("---")
                
                # Mostrar cada compra com botão de editar e excluir
                for compra in compras:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 1])
                    
                    data_formatada = datetime.fromisoformat(compra['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    descricao = compra.get('descricao', '-')
                    
                    # Se a descrição tiver múltiplas linhas (itens), mostrar só a primeira linha
                    descricao_curta = descricao.split('\n')[0] if descricao else '-'
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(compra['valor_total']):,.2f}")
                    with col3:
                        # Usar expander para descrições longas
                        if '\n' in descricao:
                            with st.expander(f"📝 {descricao_curta}"):
                                st.text(descricao)
                        else:
                            st.write(f"📝 {descricao_curta}")
                    with col4:
                        if st.button("✏️", key=f"edit_compra_{compra['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_compra = compra
                    with col5:
                        if st.button("🗑️", key=f"del_compra_{compra['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_compra(supabase, compra['id'])
                                st.success("✅ Compra excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de compra
                if 'editando_compra' in st.session_state and st.session_state.editando_compra:
                    compra = st.session_state.editando_compra
                    data_compra_obj = datetime.fromisoformat(compra['data'].replace('Z', '+00:00'))
                    
                    # Buscar parcelas atuais
                    parcelas_atuais = supabase.table("singelo_parcelas_compras").select("*").eq("compra_id", compra['id']).execute()
                    num_parcelas_atual = len(parcelas_atuais.data) if parcelas_atuais.data else 1
                    
                    with st.form(f"form_edit_compra_{compra['id']}"):
                        st.markdown(f"### ✏️ Editar Compra")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_valor = st.number_input(
                                "💵 Valor Total (R$)",
                                min_value=0.01,
                                value=float(compra['valor_total']),
                                step=0.01,
                                format="%.2f"
                            )
                        
                        with col2:
                            novo_num_parcelas = st.selectbox(
                                "💳 Número de Parcelas",
                                options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                index=num_parcelas_atual - 1 if num_parcelas_atual <= 12 else 0,
                                format_func=lambda x: f"{x}x" if x > 1 else "À vista"
                            )
                        
                        nova_descricao = st.text_area(
                            "📝 Descrição",
                            value=compra.get('descricao', ''),
                            height=100
                        )
                        
                        # Aviso se mudar número de parcelas
                        if novo_num_parcelas != num_parcelas_atual:
                            st.warning(f"⚠️ **ATENÇÃO:** Você está alterando o número de parcelas de {num_parcelas_atual}x para {novo_num_parcelas}x. Todas as parcelas já lançadas serão recalculadas!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    # Atualizar compra
                                    atualizar_compra(supabase, compra['id'], novo_valor, nova_descricao)
                                    
                                    # Se mudou o número de parcelas, recalcular
                                    if novo_num_parcelas != num_parcelas_atual:
                                        recalcular_parcelas(supabase, compra['id'], novo_valor, novo_num_parcelas, data_compra_obj)
                                        st.success(f"✅ Compra atualizada e {novo_num_parcelas} parcelas recalculadas!")
                                    else:
                                        st.success("✅ Compra atualizada!")
                                    
                                    del st.session_state.editando_compra
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_compra
                                st.rerun()
            else:
                st.info("📭 Nenhuma compra registrada ainda")
        
        with tab2:
            st.markdown("### 💰 Histórico de Vendas")
            vendas = buscar_vendas(supabase, 100)
            
            if vendas:
                # Resumo
                total = sum([float(v['valor_total']) for v in vendas])
                total_taxa = sum([float(v.get('taxa_entrega', 0)) for v in vendas])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Total de Vendas:** R$ {total:,.2f}")
                with col2:
                    st.markdown(f"**Total Taxa Entrega:** R$ {total_taxa:,.2f}")
                
                st.markdown("---")
                
                # Mostrar cada venda com botão de editar e excluir
                for venda in vendas:
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 1, 1.5, 0.7, 0.7])
                    
                    data_formatada = datetime.fromisoformat(venda['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"🎁 {venda['produto']}")
                    with col3:
                        st.write(f"📏 {venda.get('tamanho', 'N/A')}")
                    with col4:
                        st.write(f"📦 {venda['quantidade']}")
                    with col5:
                        st.write(f"💵 R$ {float(venda['valor_total']):,.2f}")
                    with col6:
                        if st.button("✏️", key=f"edit_venda_{venda['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_venda = venda
                    with col7:
                        if st.button("🗑️", key=f"del_venda_{venda['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_venda(supabase, venda['id'])
                                st.success("✅ Venda excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de venda
                if 'editando_venda' in st.session_state and st.session_state.editando_venda:
                    venda = st.session_state.editando_venda
                    
                    with st.form(f"form_edit_venda_{venda['id']}"):
                        st.markdown(f"### ✏️ Editar Venda")
                        
                        st.markdown("#### 📦 Informações do Produto")
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_produto = st.selectbox("🎁 Box", options=BOXES, index=BOXES.index(venda['produto']) if venda['produto'] in BOXES else 0)
                        with col2:
                            novo_tamanho = st.selectbox("📏 Tamanho", options=list(TAMANHOS.keys()), 
                                                       index=list(TAMANHOS.keys()).index(venda.get('tamanho', 'Box mini')) if venda.get('tamanho') in TAMANHOS.keys() else 0)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nova_quantidade = st.number_input("📦 Quantidade", min_value=1, value=venda['quantidade'], step=1)
                        with col2:
                            novo_valor = st.number_input("💵 Valor (R$)", min_value=0.01, value=float(venda['valor_total']), step=0.01, format="%.2f")
                        with col3:
                            nova_taxa = st.number_input("🚚 Taxa Entrega (R$)", min_value=0.00, value=float(venda.get('taxa_entrega', 0)), step=0.01, format="%.2f")
                        
                        st.markdown("---")
                        st.markdown("#### 📍 Endereço de Entrega")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            # Converter string ISO para date se necessário
                            data_entrega_atual = None
                            if venda.get('data_entrega'):
                                try:
                                    if isinstance(venda['data_entrega'], str):
                                        data_entrega_atual = datetime.fromisoformat(venda['data_entrega'].replace('Z', '+00:00')).date()
                                    else:
                                        data_entrega_atual = venda['data_entrega']
                                except:
                                    data_entrega_atual = datetime.now().date()
                            else:
                                data_entrega_atual = datetime.now().date()
                            
                            nova_data_entrega = st.date_input(
                                "📅 Data de Entrega",
                                value=data_entrega_atual,
                                format="DD/MM/YYYY"
                            )
                        with col2:
                            novo_cep = st.text_input("📮 CEP", value=venda.get('cep', ''), max_chars=9)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            novo_logradouro = st.text_input("🏠 Rua/Avenida", value=venda.get('logradouro', ''))
                        with col2:
                            novo_numero = st.text_input("🔢 Número", value=venda.get('numero', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_bairro = st.text_input("🏘️ Bairro", value=venda.get('bairro', ''))
                        with col2:
                            novo_complemento = st.text_input("🏢 Complemento", value=venda.get('complemento', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            nova_cidade = st.text_input("🌆 Cidade", value=venda.get('cidade', ''))
                        with col2:
                            novo_uf = st.text_input("🗺️ Estado (UF)", value=venda.get('uf', ''), max_chars=2)
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    atualizar_venda(supabase, venda['id'], novo_produto, nova_quantidade, novo_valor, nova_taxa, novo_tamanho,
                                                   data_entrega=nova_data_entrega, cep=novo_cep, 
                                                   logradouro=novo_logradouro, numero=novo_numero,
                                                   complemento=novo_complemento, bairro=novo_bairro,
                                                   cidade=nova_cidade, uf=novo_uf)
                                    st.success("✅ Venda atualizada!")
                                    del st.session_state.editando_venda
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_venda
                                st.rerun()
                
                # Resumo por produto
                st.markdown("#### 📊 Vendas por Produto")
                vendas_por_produto = {}
                for venda in vendas:
                    produto = venda['produto']
                    if produto not in vendas_por_produto:
                        vendas_por_produto[produto] = {'quantidade': 0, 'valor': 0}
                    vendas_por_produto[produto]['quantidade'] += venda['quantidade']
                    vendas_por_produto[produto]['valor'] += float(venda['valor_total'])
                
                for produto, dados in vendas_por_produto.items():
                    st.markdown(f"**{produto}:** {dados['quantidade']} unidades - R$ {dados['valor']:,.2f}")
            else:
                st.info("📭 Nenhuma venda registrada ainda")
        
        with tab3:
            st.markdown("### 🚚 Histórico de Custos de Entrega")
            entregas = buscar_entregas(supabase, 100)
            
            if entregas:
                # Total
                total = sum([float(e['custo_entregador']) for e in entregas])
                st.markdown(f"**Total Pago aos Entregadores:** R$ {total:,.2f}")
                st.markdown("---")
                
                # Mostrar cada entrega com botão de editar e excluir
                for entrega in entregas:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 1])
                    
                    data_formatada = datetime.fromisoformat(entrega['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(entrega['custo_entregador']):,.2f}")
                    with col3:
                        st.write(f"📝 {entrega.get('descricao', '-')}")
                    with col4:
                        if st.button("✏️", key=f"edit_entrega_{entrega['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_entrega = entrega
                    with col5:
                        if st.button("🗑️", key=f"del_entrega_{entrega['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_entrega(supabase, entrega['id'])
                                st.success("✅ Custo excluído!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de entrega
                if 'editando_entrega' in st.session_state and st.session_state.editando_entrega:
                    entrega = st.session_state.editando_entrega
                    
                    with st.form(f"form_edit_entrega_{entrega['id']}"):
                        st.markdown(f"### ✏️ Editar Custo de Entrega")
                        
                        novo_custo = st.number_input(
                            "💵 Custo (R$)",
                            min_value=0.01,
                            value=float(entrega['custo_entregador']),
                            step=0.01,
                            format="%.2f"
                        )
                        
                        nova_descricao = st.text_area(
                            "📝 Descrição",
                            value=entrega.get('descricao', ''),
                            height=100
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    atualizar_entrega(supabase, entrega['id'], novo_custo, nova_descricao)
                                    st.success("✅ Custo atualizado!")
                                    del st.session_state.editando_entrega
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_entrega
                                st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("📭 Nenhum custo de entrega registrado ainda")

if __name__ == "__main__":
    main()
